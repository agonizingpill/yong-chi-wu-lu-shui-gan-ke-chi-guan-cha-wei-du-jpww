import {esc} from '../format.js';
import {pill} from './desk.js';

export function questions(items) {
  return items.map(item => `<fieldset class="question" data-id="${item.id}">
    <legend><small>${esc(item.code)}</small> ${esc(item.prompt)} ${item.reversed ? pill('反向量表') : ''}</legend>
    <div class="options">${[1,2,3,4,5].map(score => `<label><input type="radio" name="q-${item.id}" value="${score}" required aria-label="${esc(item.code)} 评分 ${score}"><span>${score}</span></label>`).join('')}</div>
  </fieldset>`).join('');
}

export function readScale(form) {
  return Object.fromEntries([...new FormData(form)].filter(([key]) => key.startsWith('q-'))
    .map(([key,value]) => [key.slice(2),Number(value)]));
}
