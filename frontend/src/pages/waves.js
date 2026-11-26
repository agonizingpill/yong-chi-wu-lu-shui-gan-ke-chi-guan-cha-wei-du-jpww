import {empty,headline,pill,waveOptions} from '../components/desk.js';
import {esc} from '../format.js';
import {handle,inlineError} from '../form.js';
import {api,actor} from '../store.js';
import {waveStates} from '../types.js';

export async function wavesPage(root,ctx) {
  const [waves,forms] = await Promise.all([api().waves(),api().forms()]);
  const active = waves.find(row => row.id === Number(ctx.query.get('id'))) || waves[0];
  const form = forms.find(row=>row.id === active?.form_id);
  root.innerHTML = `${headline('班组回收','教练组达到匿名汇总门槛后，才可冻结本轮并拟合。')}
    <div class="lanes-layout"><section>
      <label class="filter">观察轮次<select id="wave-select">${waveOptions(waves,active?.id)}</select></label>
      ${active ? `<div class="lanes" aria-label="匿名观察回收进度">${active.cohorts.map(row=>`<article class="lane">
        <div><small>${esc(row.code)}</small><h2>${esc(row.label)}</h2></div>
        <div class="lane-count"><strong>${row.collected ?? '—'}</strong><small>${row.collected === null?'匿名小组':`计划 ${row.planned}`}</small></div>
        ${pill(row.eligible?'达到门槛':'待补采')}
        ${row.collected === null ? '' : `<meter min="0" max="${Math.max(row.planned,row.collected)}" value="${row.collected}"></meter>`}</article>`).join('')}</div>` : empty('没有观察轮次。')}
    </section><aside class="pad"><h2>本轮教案</h2>
      ${form ? `<a href="#editions?id=${form.id}">${esc(form.edition)} · ${esc(form.title)}</a>` : ''}
      ${active ? `<p>${pill(waveStates[active.state])}</p>` : ''}
      ${active?.next_wave_id ? `<p><a href="#waves?id=${active.next_wave_id}">查下一轮</a></p>` : ''}
      <p>每组至少 8 份，合计至少 24 份。查阅岗看不到小组的具体回收数量。</p>
      ${active?.state === 'collecting' && actor().role === 'technician' ? `<form id="fit-form"><button type="submit">冻结并拟合</button>${inlineError}</form>` : ''}
    </aside></div>`;
  root.querySelector('#wave-select').onchange = event => { location.hash = `waves?id=${event.target.value}`; };
  handle(root.querySelector('#fit-form'),async()=>{
    const result = await api().fit(active.id);
    ctx.flash(`${result.code} 已冻结输入并进入因子队列。`);
    location.hash = `loadings?id=${result.id}`;
  });
}
