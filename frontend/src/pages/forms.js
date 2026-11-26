import {empty,headline,pill} from '../components/desk.js';
import {formData,handle,inlineError} from '../form.js';
import {esc} from '../format.js';
import {actor,api} from '../store.js';
import {formStates} from '../types.js';

function publishForm(report,form) {
  return `<form id="publish-form" class="pad">
    <h2>拟定下轮观察表</h2><p>依据 ${esc(report.code)}。每个因子至少保留一条主要载荷达到阈值的条目。</p>
    <div class="two"><label>版本编号<input name="edition" required value="LW-02"></label>
    <label>新版名称<input name="title" required value="课池观察表 · 新一轮"></label>
    <label>下一轮编号<input name="next_code" required value="POND-1201"></label>
    <label>下一轮名称<input name="next_title" required value="12 月课池体验复采"></label></div>
    <fieldset><legend>选入新版的量表题</legend>${form.items.map(item=>{
      const factor=report.findings.items.find(row=>row.item_id===item.id);
      return `<label class="check"><input type="checkbox" name="item_id" value="${item.id}" checked ${item.pinned?'disabled':''}> ${esc(item.code)} · ${esc(item.prompt)}
       ${item.pinned?pill('固定保留'):''} ${factor?.strong?pill(`因子 ${factor.primary}`):''}</label>`;
    }).join('')}</fieldset>
    <button type="submit">发布并开放下一轮</button>${inlineError}</form>`;
}

export async function formsPage(root,ctx) {
  const [forms,waves,reports] = await Promise.all([api().forms(),api().waves(),api().reports()]);
  const selected = forms.find(f=>f.id===Number(ctx.query.get('id'))) || forms[0];
  const source = reports.find(r=>r.state==='approved' && waves.some(w=>w.id===r.wave_id && w.state==='review' && w.form_id===selected?.id));
  const canWrite = source && selected?.state==='active' && actor().role==='supervisor';
  root.innerHTML = `${headline('观察表版次','现行表连接下一轮匿名回收，历史答卷继续按原版解释。')}
  <div class="form-layout"><section>
  <nav class="edition-nav" aria-label="版次">${forms.map(f=>`<a href="#editions?id=${f.id}" ${selected===f?'aria-current="true"':''}>${esc(f.edition)} ${pill(formStates[f.state])}</a>`).join('')}</nav>
  ${selected ? `<article class="edition-sheet" data-edition="${esc(selected.edition)}"><header><h2>${esc(selected.title)}</h2>
   <small>${esc(selected.signed_by)} 签发</small></header><ol>${selected.items.map(item=>`<li><small>${esc(item.code)}</small> ${esc(item.prompt)}
     ${item.factor ? pill(`因子 ${item.factor}`) : ''} ${item.reversed ? pill('反向量表') : ''}</li>`).join('')}</ol></article>` : empty('目前没有观察表。')}
  </section>${canWrite?publishForm(source,selected):''}</div>`;
  handle(root.querySelector('#publish-form'),async formElement=>{
    const data=formData(formElement);
    const mutable=new FormData(formElement).getAll('item_id').map(Number);
    delete data.item_id;
    const ids=selected.items.filter(item=>item.pinned || mutable.includes(item.id)).map(item=>item.id);
    const output=await api().publish({...data,report_id:source.id,item_ids:ids});
    ctx.flash(`${output.form.edition} 已发布，下一轮已可以收集。`);
    location.hash=`editions?id=${output.form.id}`;
  });
}
