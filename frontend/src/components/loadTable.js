import {esc} from '../format.js';
import {pill} from './desk.js';

export function loadTable(findings, items) {
  return `<div class="load-table"><table><caption>固定种子 ${findings.seed} · ${findings.count} 份匿名汇总</caption>
    <thead><tr><th>条目</th><th>因子一</th><th>因子二</th><th>共同度</th><th>主载荷</th></tr></thead>
    <tbody>${findings.items.map(row => `<tr><th scope="row"><small>${esc(row.code)}</small> ${esc(items.find(item=>item.id===row.item_id)?.prompt)}
      ${row.reverse ? pill('反向已校正') : ''}</th>
      ${row.loadings.map(value => `<td class="${value < 0 ? 'negative' : 'positive'}"><span>${value.toFixed(3)}</span>
        <meter min="0" max="1" value="${Math.min(1,Math.abs(value))}"></meter></td>`).join('')}
      <td>${row.communality.toFixed(3)}</td><td>${row.strong ? `因子 ${row.primary}` : '偏弱'}</td></tr>`).join('')}</tbody>
    </table></div>`;
}
