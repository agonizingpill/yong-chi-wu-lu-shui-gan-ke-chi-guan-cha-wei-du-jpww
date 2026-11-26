import {esc} from '../format.js';
import {roles} from '../types.js';

const sections = [['waves','班组回收'],['survey','匿名观察'],['loadings','负荷核校'],['editions','观察表版次']];
export const pill = text => `<span class="pill">${esc(text)}</span>`;
export const empty = text => `<p class="empty">${esc(text)}</p>`;
export const headline = (title,detail) => `<header class="heading"><h1>${esc(title)}</h1><p>${esc(detail)}</p></header>`;
export const waveOptions = (waves,active) => waves.map(wave => `<option value="${wave.id}" ${wave.id === active ? 'selected' : ''}>${esc(wave.code)} · ${esc(wave.title)}</option>`).join('');

export function frame(page,user,notice) {
  return `<header class="mast"><a href="#waves" class="logotype">芦湾教研 <small>课池观察</small></a>
    <div class="session">${esc(user.display_name)} · ${esc(roles[user.role])} <button id="exit" class="ghost" type="button">退出</button></div>
    <nav aria-label="课池观察工作区">${sections.map(([key,title]) => `<a href="#${key}" ${key === page ? 'aria-current="page"' : ''}>${title}</a>`).join('')}</nav></header>
    <main class="desk">${notice ? `<p class="notice" role="status">${esc(notice)}</p>` : ''}<div id="workspace"></div></main>`;
}
