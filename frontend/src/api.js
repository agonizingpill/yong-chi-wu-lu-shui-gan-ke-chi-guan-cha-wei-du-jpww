import {request} from './http.js';

export const login = data => request('/auth/login', {method:'POST',data});

export function pool(token) {
  const get = path => request(path,{token});
  const post = (path,data) => request(path,{token,data,method:'POST'});
  return {
    waves:() => get('/waves'), forms:() => get('/forms'), reports:() => get('/factors'),
    submit:data => post('/surveys',data), fit:wave_id => post('/factors',{wave_id}),
    approve:(id,note) => post(`/factors/${id}/approve`,{note}),
    publish:data => post('/forms/publish',data),
  };
}
