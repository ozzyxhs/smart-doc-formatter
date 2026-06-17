"""运行期 JSON API：上传→排版任务（后台线程跑 pipeline）→ 轮询→ 报告→ 下载。

任务元数据在内存（P1 够用，重启即清）；上传/成品落 app/_jobs/<id>/。
"""
import uuid
import shutil
import threading
import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import yaml
from engine import config, pipeline

router = APIRouter()
_jobs = {}
_lock = threading.Lock()


def _job_dir(jid):
    d = config.JOBS_DIR / jid
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.get("/templates")
def list_templates():
    out = []
    for p in sorted(config.TEMPLATES_DIR.glob("*.yaml")):
        try:
            with open(p, encoding="utf-8") as f:
                m = yaml.safe_load(f)["meta"]
            out.append({"id": m["id"], "name": m["name"],
                        "institution": m.get("institution"), "doc_type": m.get("doc_type"),
                        "spec_version": m.get("spec_version")})
        except Exception:
            pass
    return out


def _run(jid, input_path, template_id, out_path):
    def prog(stage, pct):
        with _lock:
            _jobs[jid].update(stage=stage, pct=pct, status="running")
    try:
        res = pipeline.run(input_path, template_id, out_path, progress=prog)
        with _lock:
            _jobs[jid].update(status=("blocked" if res["blocked"] else "done"),
                              pct=100, report=res["report"], title=res["title"],
                              out_path=str(out_path))
    except Exception as e:
        traceback.print_exc()
        with _lock:
            _jobs[jid].update(status="error", error=str(e), pct=100)


@router.post("/jobs")
async def create_job(file: UploadFile = File(...), template_id: str = Form(...)):
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(400, "目前只支持 .docx 文件（P1）")
    jid = uuid.uuid4().hex[:12]
    d = _job_dir(jid)
    inp = d / file.filename
    with open(inp, "wb") as f:
        shutil.copyfileobj(file.file, f)
    out = d / "output.docx"
    with _lock:
        _jobs[jid] = {"id": jid, "status": "queued", "stage": "queued", "pct": 0,
                      "filename": file.filename, "template_id": template_id,
                      "out_path": None, "report": None, "title": None}
    threading.Thread(target=_run, args=(jid, str(inp), template_id, str(out)), daemon=True).start()
    return {"job_id": jid}


@router.post("/jobs/demo")
def create_demo_job():
    """用本地内置样例（论文三稿→农大）起一个任务。fixtures 不入库，仅本机可用。"""
    sample = config.FIXTURES_DIR / "论文（三稿）.docx"
    if not sample.exists():
        raise HTTPException(404, "本地没有样例文件（fixtures/论文（三稿）.docx）")
    jid = uuid.uuid4().hex[:12]
    d = _job_dir(jid)
    inp = d / sample.name
    shutil.copyfile(sample, inp)
    out = d / "output.docx"
    with _lock:
        _jobs[jid] = {"id": jid, "status": "queued", "stage": "queued", "pct": 0,
                      "filename": sample.name, "template_id": "neau-bachelor-thesis-2025",
                      "out_path": None, "report": None, "title": None}
    threading.Thread(target=_run, args=(jid, str(inp), "neau-bachelor-thesis-2025", str(out)),
                     daemon=True).start()
    return {"job_id": jid}


@router.get("/jobs/{jid}")
def job_status(jid):
    with _lock:
        j = _jobs.get(jid)
        if not j:
            raise HTTPException(404, "无此任务")
        out = {k: j.get(k) for k in ("id", "status", "stage", "pct", "filename", "title", "error")}
        if j.get("report") and j["status"] in ("done", "blocked"):
            out["report"] = j["report"]
        return out


@router.get("/jobs/{jid}/report")
def job_report(jid):
    with _lock:
        j = _jobs.get(jid)
    if not j or not j.get("report"):
        raise HTTPException(404, "报告未就绪")
    return j["report"]


@router.get("/jobs/{jid}/preview")
def job_preview(jid):
    """成品文本预览（供"实时排版"屏）：按字号/加粗粗判类别，文本原样。"""
    with _lock:
        j = _jobs.get(jid)
    if not j or not j.get("out_path"):
        raise HTTPException(404, "成品未就绪")
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    from docx.oxml.ns import qn
    doc = Document(j["out_path"])
    items = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            p = Paragraph(child, doc)
            t = p.text.strip()
            if not t or not p.runs:
                continue
            r = p.runs[0]
            sz = r.font.size.pt if r.font.size else 10.5
            bold = bool(r.bold)
            if sz >= 20:
                kind = "title"
            elif sz >= 17:
                kind = "h1"
            elif sz >= 15 and bold:
                kind = "h2"
            elif bold and sz >= 13:
                kind = "h3"
            else:
                kind = "body"
            items.append({"kind": kind, "text": t})
        elif child.tag == qn("w:tbl"):
            tb = Table(child, doc)
            rows = [[c.text for c in row.cells] for row in tb.rows[:6]]
            items.append({"kind": "table", "rows": rows})
        if len(items) >= 220:
            break
    return {"title": j.get("title"), "items": items}


@router.get("/jobs/{jid}/pages")
def job_pages(jid):
    """真·页面渲染（Word→PDF→PNG）。首次调用会渲染（数秒），之后走缓存。"""
    with _lock:
        j = _jobs.get(jid)
    if not j or not j.get("out_path"):
        raise HTTPException(404, "成品未就绪")
    if j["status"] == "blocked":
        return {"count": 0, "blocked": True, "pages": []}
    from pathlib import Path
    from engine import render
    pages_dir = Path(j["out_path"]).parent / "_pages"
    try:
        n = render.render_pages(j["out_path"], pages_dir)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"渲染失败：{e}")
    return {"count": n, "pages": [f"/api/jobs/{jid}/page/{i + 1}" for i in range(n)]}


@router.get("/jobs/{jid}/page/{n}")
def job_page(jid, n: int):
    from pathlib import Path
    with _lock:
        j = _jobs.get(jid)
    if not j or not j.get("out_path"):
        raise HTTPException(404, "成品未就绪")
    png = Path(j["out_path"]).parent / "_pages" / f"page{n}.png"
    if not png.exists():
        raise HTTPException(404, "该页未渲染")
    return FileResponse(str(png), media_type="image/png")


@router.get("/jobs/{jid}/download")
def job_download(jid):
    with _lock:
        j = _jobs.get(jid)
    if not j or not j.get("out_path"):
        raise HTTPException(404, "成品未就绪")
    if j["status"] == "blocked":
        raise HTTPException(409, "内容守恒未通过，已拒交残稿")
    return FileResponse(
        j["out_path"], filename=f"已排版_{j.get('filename', 'output.docx')}",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
