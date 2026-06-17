/* 共用 API 助手 + 小工具。无框架，原生 fetch。 */
const API = {
  async templates() { return (await fetch('/api/templates')).json(); },
  async createJob(file, templateId) {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('template_id', templateId);
    const r = await fetch('/api/jobs', { method: 'POST', body: fd });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '上传失败');
    return r.json();
  },
  async demoJob() {
    const r = await fetch('/api/jobs/demo', { method: 'POST' });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || '样例不可用');
    return r.json();
  },
  async job(id) { return (await fetch('/api/jobs/' + id)).json(); },
  async report(id) { return (await fetch('/api/jobs/' + id + '/report')).json(); },
  async preview(id) { return (await fetch('/api/jobs/' + id + '/preview')).json(); },
  async pages(id) { return (await fetch('/api/jobs/' + id + '/pages')).json(); },
  downloadUrl(id) { return '/api/jobs/' + id + '/download'; },
};

function qs(name) { return new URLSearchParams(location.search).get(name); }
function esc(s) { return (s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

const STAGE_TEXT = {
  queued:   { h: '排队中', d: '马上开始…' },
  ingest:   { h: '读取文档', d: '正在拆解你的稿子…' },
  classify: { h: '分析结构', d: '认每一段是标题/正文/图表/参考文献…' },
  format:   { h: '套用格式', d: '正在按目标规范重排版面…' },
  gate:     { h: '核对内容', d: '逐字比对，确保一个字没丢…' },
  review:   { h: '格式复审', d: 'DeepSeek 拿规范逐条核对排版（深度推理，稍慢）…' },
  done:     { h: '完成', d: '正在打开结果…' },
};