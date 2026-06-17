"""读 docx -> 规范化「区块流」（保序：段落与表格交错）。

只读取，不改内容。每段保留 text + runs(text/bold/italic) + 原样式名；表格保留单元格文本。
"""
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.ns import qn


def _iter_block_items(doc):
    """按文档真实顺序产出段落与表格。"""
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def ingest(path):
    doc = Document(path)
    blocks = []
    for i, blk in enumerate(_iter_block_items(doc)):
        if isinstance(blk, Paragraph):
            runs = [{"text": r.text, "bold": bool(r.bold), "italic": bool(r.italic)}
                    for r in blk.runs if r.text]
            text = blk.text
            blocks.append({
                "idx": i,
                "kind": "paragraph",
                "text": text,
                "style": (blk.style.name if blk.style else "Normal") or "Normal",
                "runs": runs if runs else ([{"text": text, "bold": False, "italic": False}] if text else []),
                "empty": not text.strip(),
            })
        else:  # Table
            rows = [[cell.text for cell in row.cells] for row in blk.rows]
            blocks.append({
                "idx": i,
                "kind": "table",
                "rows": rows,
                "n_rows": len(blk.rows),
                "n_cols": len(blk.columns),
            })
    return blocks


def all_text(blocks):
    """抽全文文本序列（段落 + 表格单元格），供内容守恒闸用。"""
    seq = []
    for b in blocks:
        if b["kind"] == "paragraph":
            if b["text"].strip():
                seq.append(b["text"])
        else:
            for row in b["rows"]:
                for cell in row:
                    if cell.strip():
                        seq.append(cell)
    return seq
