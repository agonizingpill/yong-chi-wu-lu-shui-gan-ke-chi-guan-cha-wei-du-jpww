export const esc = (text = '') => String(text ?? '').replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');

export const pct = score => new Intl.NumberFormat('zh-CN', {style:'percent', maximumFractionDigits:1}).format(score);
export const shortDay = date => String(date).replace(/^2026-/, '');
