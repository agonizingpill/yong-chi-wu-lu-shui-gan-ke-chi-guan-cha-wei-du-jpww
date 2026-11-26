import {pool} from './api.js';
const key = 'luwan-teaching-session';
let auth = JSON.parse(sessionStorage.getItem(key) || 'null');
export const actor = () => auth?.profile;
export const api = () => pool(auth?.access_token);
export function save(session) {
  auth = session;
  if (session) sessionStorage.setItem(key,JSON.stringify(session));
  else sessionStorage.removeItem(key);
}
