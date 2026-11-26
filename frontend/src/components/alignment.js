import {esc} from '../format.js';
import {inlineError} from '../form.js';
import {pill} from './desk.js';
import {alignSources} from '../types.js';

const signLabel = value => value < 0 ? '反向' : '正向';

function mapping(alignment) {
  return alignment.order.map((canonical, fitted) =>
    `固定因子 ${canonical} ← 拟合因子 ${fitted + 1}（${signLabel(alignment.signs[fitted])}）`).join('　');
}

function evidenceRows(alignment) {
  const evidence = alignment.evidence || {};
  const candidates = evidence.candidates || [];
  if (!candidates.length) return '';
  const best = candidates[0];
  return `<details class="align-evidence" ${alignment.status === 'pending' ? 'open' : ''}>
    <summary>共有题载荷比对（${evidence.shared_items ?? 0} 条）</summary>
    <table><thead><tr><th>拟合编号对应</th><th>方向</th><th>最弱相关</th><th>锚点题数</th></tr></thead>
    <tbody>${candidates.map(row => `<tr ${row === best ? 'class="best"' : ''}>
      <td>${row.order.map((canonical, fitted) => `${fitted + 1}→${canonical}`).join('、')}</td>
      <td>${row.signs.map(signLabel).join('、')}</td>
      <td>${row.score.toFixed(2)}</td>
      <td>${row.anchors.join(' / ')}</td></tr>`).join('')}</tbody></table>
    <p><small>锚点题数指两版都在该因子上主要载荷达到阈值的共有题；只有每个因子都有锚点、相关足够高且与次优方案分得开时才自动认定。</small></p>
  </details>`;
}

export function alignmentPanel(report) {
  const alignment = report.alignment;
  if (!alignment) return '';
  const decided = alignment.status === 'decided';
  const evidence = alignment.evidence || {};
  const shared = evidence.shared_items;
  const source = alignment.source === 'baseline' ? alignSources.baseline
    : alignment.source === 'manual' ? alignSources.manual : alignSources.auto;
  const by = alignment.decided_by === 'system' ? '系统' : alignment.decided_by;
  return `<section class="alignment" data-alignment="${esc(alignment.status)}">
    <h3>因子编号与方向</h3>
    ${decided ? `<p>${pill('编号已认定')} ${esc(mapping(alignment))}</p>
      <p><small>${esc(source)}${by ? ` · ${esc(by)} 确认` : ''}
      ${shared != null ? ` · 共有题 ${shared} 条` : ''}</small></p>` :
      `<p class="align-gap">${esc(alignment.reason || '证据不足，请教研认定编号与方向。')}</p>
      <p><small>${pill('待认定编号')} 证据不足，教研认定前不能核校签发。</small></p>`}
    ${alignment.evidence?.note ? `<p><small>${esc(alignment.evidence.note)}</small></p>` : ''}
    ${evidenceRows(alignment)}
  </section>`;
}

export function alignmentForm(report) {
  if (!report.alignment || report.alignment.status !== 'pending') return '';
  const order = report.alignment.order || [1, 2];
  const signs = report.alignment.signs || [1, 1];
  const factorOptions = selected => [1, 2].map(value =>
    `<option value="${value}" ${value === selected ? 'selected' : ''}>固定因子 ${value}</option>`).join('');
  const signOptions = selected => [[1, '正向'], [-1, '反向']].map(([value, label]) =>
    `<option value="${value}" ${value === selected ? 'selected' : ''}>${label}</option>`).join('');
  return `<form id="align-form" class="pad">
    <h3>认定编号与正反方向</h3>
    <p>按现行观察表的固定编号，说明本次拟合的两个因子各对应哪一个、是否整体反号。两位教研同时提交时，以先确认的为准。</p>
    <div class="two">
      <label>本次拟合因子一 → 固定编号<select name="order_0">${factorOptions(order[0])}</select></label>
      <label>因子一方向<select name="signs_0">${signOptions(signs[0])}</select></label>
      <label>本次拟合因子二 → 固定编号<select name="order_1">${factorOptions(order[1])}</select></label>
      <label>因子二方向<select name="signs_1">${signOptions(signs[1])}</select></label>
    </div>
    <label>认定依据<input name="note" minlength="6" maxlength="180" required placeholder="例如：CW-01 仍属固定因子一，整体反号"></label>
    <button type="submit">认定并锁定编号</button>${inlineError}
  </form>`;
}
