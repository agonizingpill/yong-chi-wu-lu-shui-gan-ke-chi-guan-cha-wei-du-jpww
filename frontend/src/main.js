import {frame,empty} from './components/desk.js';
import {actor,save} from './store.js';
import {entrance} from './pages/login.js';
import {wavesPage} from './pages/waves.js';
import {surveyPage} from './pages/survey.js';
import {loadingsPage} from './pages/loadings.js';
import {formsPage} from './pages/forms.js';

const root=document.querySelector('#app');
const pages={waves:wavesPage,survey:surveyPage,loadings:loadingsPage,editions:formsPage};
let notice='';

async function render() {
  const [key,query]=location.hash.slice(1).split('?');
  if (!actor() || key==='login') return entrance(root,render);
  const active=Object.hasOwn(pages,key)?key:'waves';
  root.innerHTML=frame(active,actor(),notice);
  notice='';
  root.querySelector('#exit').onclick=()=>{ save(null);location.hash='login'; };
  const content=root.querySelector('#workspace');
  try {
    await pages[active](content,{query:new URLSearchParams(query),
      flash:text=>{ notice=text; }, refresh:(text='')=>{ notice=text;render(); }});
  } catch (error) {
    if (!content.isConnected) return;
    if (error.status===401 || error.status===403) {
      save(null);
      location.hash='login';
      return;
    }
    content.innerHTML=`${empty(error.message)}<button type="button" id="retry">重试</button>`;
    content.querySelector('#retry').onclick=render;
  }
}

window.addEventListener('hashchange',render);
render();
