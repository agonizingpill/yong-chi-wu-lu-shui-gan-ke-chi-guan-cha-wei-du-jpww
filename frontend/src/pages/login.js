import {login} from '../api.js';
import {formData,handle,inlineError} from '../form.js';
import {save} from '../store.js';

export function entrance(root,render) {
  root.innerHTML = `<main class="entrance">
    <section class="waterlines"><h1>课池<br>观察</h1><p>芦湾游泳中心 · 水感课教研组</p></section>
    <section class="credentials"><h2>打开教研台</h2><p>采集的观察表只用于班组汇总。</p>
    <form id="login-form"><label>账号<input name="username" autocomplete="username" required></label>
      <label>密码<input name="password" type="password" autocomplete="current-password" required></label>
      <button type="submit">进入教研台</button>${inlineError}</form>
    <p class="micro">本地演示班组 shu、fang、cheng</p></section></main>`;
  handle(root.querySelector('form'),async form=>{
    save(await login(formData(form)));
    if (location.hash === '#waves') render();
    else location.hash = 'waves';
  });
}
