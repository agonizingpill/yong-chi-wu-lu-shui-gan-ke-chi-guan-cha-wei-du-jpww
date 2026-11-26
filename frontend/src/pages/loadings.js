import {alignmentForm,alignmentPanel} from '../components/alignment.js';
import {empty,headline,pill} from '../components/desk.js';
import {loadTable} from '../components/loadTable.js';
import {formData,handle,inlineError} from '../form.js';
import {esc} from '../format.js';
import {actor,api} from '../store.js';
import {reportStates} from '../types.js';

export async function loadingsPage(root,ctx) {
  const [reports,waves,forms] = await Promise.all([api().reports(),api().waves(),api().forms()]);
  const selected = reports.find(row=>row.id === Number(ctx.query.get('id'))) || reports[0];
  const wave = waves.find(w=>w.id === selected?.wave_id);
  const form = forms.find(f=>f.id === wave?.form_id);
  const pendingAlignment = selected?.alignment?.status === 'pending';
  root.innerHTML = `${headline('负荷核校','查阅两因子正交旋转的载荷、反向条目和共同度。新报告先按现行观察表的来源报告对齐固定编号。')}
    <div class="analysis"><aside class="index"><button id="reload" type="button" class="ghost">刷新</button>
      ${reports.map(row=>`<a href="#loadings?id=${row.id}" ${row===selected?'aria-current="true"':''}>${esc(row.code)} ${pill(reportStates[row.state])}
        ${row.alignment?.status==='pending'?pill('待认定编号'):''}</a>`).join('')}</aside>
    <section>${selected ? `<article class="pad" data-report="${selected.id}">
      <div class="report-title"><h2>${esc(selected.code)}</h2>${pill(reportStates[selected.state])}</div>
      <p>${esc(wave?.title)} · ${esc(form?.edition)}</p>
      ${alignmentPanel(selected)}
      ${selected.findings ? loadTable(selected.findings,form?.items || []) : empty('当前报告还没有载荷表。')}
      ${selected.review_note ? `<blockquote>${esc(selected.review_note)}</blockquote>` : ''}
      ${pendingAlignment && actor().role === 'supervisor' ? alignmentForm(selected) :
        selected.state === 'ready' && actor().role === 'supervisor' ? `<form id="review-form">
          <label>核校意见<input name="note" minlength="6" required></label><button type="submit">确认负荷与反向条目</button>${inlineError}
        </form>` : ''}
      ${pendingAlignment && actor().role !== 'supervisor' ? empty('共有题证据不足，等待教研认定编号与方向，认定后才能核校签发。') : ''}
      ${selected.state === 'approved' ? '<a href="#editions">到观察表版次查阅或拟定新版</a>' : ''}
    </article>` : empty('暂无可见的因子报告。观察岗可在收集达标后提交拟合。')}</section></div>`;
  root.querySelector('#reload').onclick=()=>ctx.refresh();
  handle(root.querySelector('#align-form'),async formElement=>{
    const data=formData(formElement,['order_0','signs_0','order_1','signs_1']);
    await api().align(selected.id,{order:[data.order_0,data.order_1],signs:[data.signs_0,data.signs_1],note:data.note});
    ctx.refresh('编号与方向已认定。');
  });
  handle(root.querySelector('#review-form'),async formElement=>{
    await api().approve(selected.id,formElement.elements.note.value);
    ctx.refresh('报告核校通过。');
  });
}
