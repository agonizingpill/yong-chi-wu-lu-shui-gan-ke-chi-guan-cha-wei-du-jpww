import {empty,headline,waveOptions} from '../components/desk.js';
import {questions,readScale} from '../components/scale.js';
import {esc} from '../format.js';
import {formData,handle,inlineError} from '../form.js';
import {actor,api} from '../store.js';

export async function surveyPage(root,ctx) {
  const [waves,forms] = await Promise.all([api().waves(),api().forms()]);
  const open = waves.filter(wave=>wave.state==='collecting');
  const active = open.find(wave=>wave.id===Number(ctx.query.get('id'))) || open[0];
  const form = forms.find(row=>row.id===active?.form_id);
  root.innerHTML = `${headline('匿名观察','提交班次中看到的课堂参与情况。使用无身份信息的一次性观察券。')}
   ${actor().role !== 'technician' ? empty('匿名观察由记录岗提交。原始逐人答案没有查询页面。') :
      !active || !form ? empty('没有开放的观察轮次。请到班组回收检查状态。') : `
    <div class="survey-wrap">
    <aside class="survey-guide">
      <label>观察轮次<select id="select-wave">${waveOptions(open,active?.id)}</select></label>
      <h2>${esc(form.edition)}</h2><p>1 代表很少出现，5 代表经常出现。按观察原样作答，后台会根据版本处理反向条目。</p>
      <small>观察券只用于同轮去重，请勿录入姓名和联系方式。</small>
    </aside>
    <form id="survey-form" class="pad">
      <div class="two"><label>教练组<select name="cohort_id">${active.cohorts.map(row=>`<option value="${row.id}">${esc(row.label)}</option>`).join('')}</select></label>
      <label>观察券<input name="ticket" minlength="16" maxlength="32" required placeholder="16–32 位十六进制"></label></div>
      ${questions(form.items)}
      <label class="check"><input type="checkbox" name="consent" required> 同意只以合并形式使用本份观察</label>
      <button type="submit">送入匿名回收簿</button>${inlineError}</form>
    </div>`}`;
  const selector = root.querySelector('#select-wave');
  if (selector) selector.onchange = event => { location.hash = `survey?id=${event.target.value}`; };
  handle(root.querySelector('#survey-form'),async formElement=>{
    const {cohort_id,ticket} = formData(formElement,['cohort_id']);
    await api().submit({wave_id:active.id,cohort_id,ticket,consent:formElement.elements.consent.checked,answers:readScale(formElement)});
    ctx.refresh('匿名观察已接收。可继续提交下一份。');
  });
}
