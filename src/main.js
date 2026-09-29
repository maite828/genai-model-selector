import {createIcons, Workflow, SlidersHorizontal, Database, History, GitBranch, FlaskConical, LockKeyhole, Cloud, ArrowRight, GitPullRequestArrow, Play, Download, RefreshCw, Trash2, ShieldCheck} from 'lucide';
import './style.css';

const icons = {Workflow, SlidersHorizontal, Database, History, GitBranch, FlaskConical, LockKeyhole, Cloud, ArrowRight, GitPullRequestArrow, Play, Download, RefreshCw, Trash2, ShieldCheck};
const $ = (id) => document.getElementById(id);
const escape = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (value, digits=3) => Number(value).toLocaleString('es-ES', {minimumFractionDigits:digits, maximumFractionDigits:digits});
const profileNames = {balanced:'Equilibrio', quality:'Calidad', cost:'Coste', emissions:'Emisiones'};
const executionNames = {completed:'Ejecución local', failed:'Ejecución fallida', blocked:'Ejecución bloqueada'};
let config, profile='balanced', current=null, busy=false;
const emptyDecision = $('decision').innerHTML;

async function api(path, body, method='POST') {
  const res = await fetch('/api/'+path, {method:body === undefined && method==='POST' ? 'GET' : method,
    headers:{'Content-Type':'application/json', 'X-Session-Token':config?.token || ''},
    ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  const data = await res.json();
  if(!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Revisa los valores de la solicitud.');
  return data;
}
function showError(err) { $('error').textContent=err.message; $('error').hidden=false; }
function requestBody() {
  return {prompt:$('prompt').value, task:$('task').value, privacy:$('privacy').value,
    allow_remote:$('allow-remote').checked, profile, max_cost:Number($('budget').value),
    min_quality:Number($('min-quality').value)/100, output_tokens:Number($('tokens').value)};
}
function weights() {
  if(!config)return;
  const w=config.weights[profile];
  ['quality','cost','emissions'].forEach((k,i)=>$('w-'+k).textContent=Math.round(w[i]*100)+'%');
  const canvas=$('weights-chart'), ratio=window.devicePixelRatio || 1;
  const width=canvas.clientWidth;
  canvas.width=width*ratio; canvas.height=13*ratio;
  const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
  let x=0;
  w.forEach((v,i)=>{ctx.fillStyle=['#21715d','#ce8069','#c5a24e'][i];ctx.fillRect(x,2,Math.max(0,v*width-3),8);x+=v*width;});
  canvas.setAttribute('aria-label',`Pesos: calidad ${Math.round(w[0]*100)}%, coste ${Math.round(w[1]*100)}%, emisiones ${Math.round(w[2]*100)}%`);
}
function updateForm() {
  $('allow-remote').disabled=$('privacy').value!=='public';
  if($('allow-remote').disabled)$('allow-remote').checked=false;
  $('char-count').textContent=$('prompt').value.length.toLocaleString('es-ES')+' / 20.000';
  $('quality-value').textContent=$('min-quality').value+'%';
}
function invalidate() {
  current=null;$('decision').innerHTML=emptyDecision;$('decision-status').textContent='Pendiente';
  $('decision-status').className='badge neutral';$('export').disabled=true;
  $('execution').hidden=true;$('response').hidden=true;$('response').textContent='';$('error').hidden=true;
  updateForm();renderTable();
}
function renderTable() {
  const candidates=current?.candidates || config?.catalog || [];
  $('comparison-body').innerHTML=candidates.map(c=>`<tr class="${current?.selected?.id===c.id?'selected':''}">
    <td>${escape(c.name)}${c.reasons?.length?`<small>${escape(c.reasons.join(' · '))}</small>`:''}</td>
    <td><span class="badge ${c.location==='local'?'success':'neutral'}">${c.location==='local'?'Local':'Remoto'}</span></td>
    <td>${current?fmt(c.quality*100,0)+'%':'—'}</td><td>${current?fmt(c.cost,5)+' €':'—'}</td>
    <td>${current?fmt(c.emissions,3)+' gCO₂e':'—'}</td>
    <td>${current?(c.eligible?`<div class="score-cell"><span class="score-bar"><b style="width:${c.score*100}%"></b></span>${fmt(c.score,3)}</div>`:'Excluido'):'Sin evaluar'}</td></tr>`).join('');
}
function renderDecision() {
  const r=current, c=r.selected;
  $('decision-status').textContent=c?'Seleccionado':'Abstención';
  $('decision-status').className='badge '+(c?'success':'warning');
  const allowed=r.candidates.filter(x=>x.eligible).length;
  $('decision').innerHTML=`<div class="winner"><p class="eyebrow">${c?'RESULTADO DE LA SELECCIÓN':'SIN CANDIDATOS ADMISIBLES'}</p>
    <h3>${c?escape(c.name):'Abstención'}</h3><p>${c?`Mayor puntuación WSM con el perfil ${profileNames[r.constraints.profile].toLowerCase()}. ${allowed} de 3 candidatos admisibles.`:'Ningún candidato cumple todas las restricciones. No se ha enviado la solicitud a ningún modelo.'}</p></div>
    ${c?`<div class="decision-metrics"><div><span>Puntuación WSM</span><strong>${fmt(c.score)}</strong><small>Utilidad normalizada</small></div><div><span>Coste estimado</span><strong>${fmt(c.cost,4)} €</strong><small>Dato sintético</small></div><div><span>Emisiones estimadas</span><strong>${fmt(c.emissions,3)}</strong><small>gCO₂e · Dato sintético</small></div></div>`:''}
    <ol class="trace"><li><span class="step">1</span><div><strong>Análisis local completado</strong><small>${r.analysis.input_tokens_estimated} tokens de entrada estimados · Tarea declarada</small></div></li>
    <li><span class="step">2</span><div><strong>${r.analysis.local_only?'Privacidad: solo modelos locales':'Candidatos locales y remotos permitidos'}</strong><small>${r.analysis.sensitive_signal?'Señal sensible detectada por heurística local.':'Política aplicada antes de la comparación.'}</small></div></li>
    <li><span class="step">3</span><div><strong>${allowed} candidatos admisibles</strong><small>Filtro de privacidad, coste y calidad mínima</small></div></li>
    <li><span class="step">4</span><div><strong>${c?'Decisión registrada':'Abstención registrada'}</strong><small>${escape(r.catalog_version)} · Sin guardar el contenido</small></div></li></ol>`;
  $('export').disabled=false;
  $('execution').hidden=!c;
  if(c){
    const binding=config.bindings[c.id];
    $('execute-btn').disabled=!binding;
    $('execution-note').textContent=binding?`Destino local: ${binding}. Métricas del catálogo aún sin calibrar.`:
      c.location==='remote'?'Ejecución remota no habilitada.':'Modelo Ollama sin vincular. Solo selección, sin generación.';
  }
  renderTable();
}
function setBusy(value){
  busy=value;
  $('route-btn').disabled=value;
  $('request-form').setAttribute('aria-busy',String(value));
  $('route-btn').lastChild.textContent=value?'Procesando…':'Evaluar selección';
  document.querySelectorAll('#request-form input, #request-form textarea, #request-form select, #request-form .segmented button').forEach(el=>el.disabled=value);
  if(!value)updateForm();
}
$('request-form').addEventListener('submit',async e=>{
  e.preventDefault();if(busy || !config)return;
  const body=requestBody();invalidate();setBusy(true);
  try{current=await api('route',body);renderDecision();}catch(err){showError(err);}finally{setBusy(false);}
});
document.querySelectorAll('[data-profile]').forEach(btn=>btn.addEventListener('click',()=>{
  profile=btn.dataset.profile;document.querySelectorAll('[data-profile]').forEach(b=>{b.classList.toggle('chosen',b===btn);b.setAttribute('aria-pressed',String(b===btn));});weights();invalidate();
}));
$('request-form').addEventListener('input',e=>{if(e.target.id!=='example')invalidate();});
$('example').addEventListener('change',()=>{
  const kind=$('example').value;if(!kind)return;
  const samples={summary:'Resume en cinco puntos las ventajas y limitaciones del trabajo en equipo en un proyecto de investigación.',private:'Redacta un resumen de esta historia clínica ficticia de un paciente para una revisión interna. No hay datos reales.',code:'Escribe una función en Python que elimine duplicados de una lista conservando el orden.',abstain:'Explica en una frase qué es una red neuronal.'};
  $('prompt').value=samples[kind];$('task').value=kind==='code'?'code':kind==='abstain'?'knowledge':'summary';
  $('privacy').value=kind==='private'?'sensitive':'public';$('allow-remote').checked=kind!=='private';
  $('budget').value=kind==='abstain'?'0':'0.02';$('min-quality').value='0';invalidate();
});
$('export').addEventListener('click',()=>download(current));
function download(data){
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`decision-${data.id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('execute-btn').addEventListener('click',async()=>{
  if(busy || !current?.selected)return;
  if(!confirm('¿Ejecutar esta solicitud en el modelo local de Ollama? Puede tardar y consumir recursos del equipo.'))return;
  $('execute-btn').disabled=true;setBusy(true);$('error').hidden=true;
  $('response').hidden=true;$('response').textContent='';
  try{const result=await api('execute',requestBody());current=result.decision;renderDecision();$('response').textContent=result.response;$('response').hidden=false;$('execution-note').textContent=`Respuesta local · ${fmt(current.execution.latency_ms/1000,2)} s · ${current.execution.output_tokens??'N/D'} tokens de salida · Energía no medida`;}catch(err){showError(err);}finally{setBusy(false);$('execute-btn').disabled=!config.bindings[current?.selected?.id];}
});
async function showHistory(){
  const rows=await api('history');
  $('history-list').innerHTML=rows.length?rows.map(r=>`<div class="history-row"><div><strong>${escape(r.selected?.name||'Abstención')} <span class="badge neutral">${executionNames[r.execution?.status]||(r.status==='abstained'?'Abstención':'Selección')}</span></strong><small>${escape(new Date(r.created_at).toLocaleString('es-ES'))} · ${profileNames[r.constraints.profile]} · ${escape(r.id.slice(0,8))}</small></div><button class="icon-button history-download" data-id="${r.id}" title="Descargar decisión" aria-label="Descargar decisión ${r.id.slice(0,8)}"><i data-lucide="download"></i></button></div>`).join(''):'<div class="empty-decision"><h3>Sin decisiones registradas</h3></div>';
  document.querySelectorAll('.history-download').forEach(btn=>btn.addEventListener('click',()=>download(rows.find(r=>r.id===btn.dataset.id))));createIcons({icons});
}
async function checkHealth(){
  $('health').textContent='Comprobando conexión…';
  try{const h=await api('health');$('health').textContent=h.ollama?`Ollama disponible · ${h.models.length} modelos instalados${h.models.length?' · '+h.models.join(', '):''}`:'Ollama no está activo. La selección con el catálogo de demostración sigue disponible.';}catch(err){$('health').textContent=err.message;}
}
document.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',async()=>{
  const id=btn.dataset.view;
  document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==id);
  document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el===btn));
  $('view-title').textContent={workspace:'Selección de modelos',catalog:'Catálogo de modelos',history:'Decisiones registradas',method:'Metodología'}[id];
  if(id==='workspace')weights();
  try{if(id==='history')await showHistory();if(id==='catalog')await checkHealth();}catch(err){const el=id==='history'?$('history-list'):$('health');el.textContent=err.message;}
}));
$('clear-history').addEventListener('click',async()=>{if(confirm('¿Borrar todas las decisiones guardadas en este equipo?')){try{await api('history',undefined,'DELETE');await showHistory();}catch(err){$('history-list').textContent=err.message;}}});
$('refresh-health').addEventListener('click',checkHealth);
new ResizeObserver(weights).observe($('weights-chart'));
createIcons({icons});updateForm();
async function initialize(){try{
  config=await api('config');weights();renderTable();
  $('catalog-version').textContent=config.version;
  $('catalog-list').innerHTML=config.catalog.map(c=>`<div class="catalog-row"><div><h3>${escape(c.name)}</h3><span class="badge ${c.location==='local'?'success':'neutral'}">${c.location==='local'?'Local':'Remoto'}</span></div><div><small>Calidad sintética por tarea</small><strong>${fmt(Math.min(...Object.values(c.quality))*100,0)}–${fmt(Math.max(...Object.values(c.quality))*100,0)}%</strong></div><div><small>€/1.000 tokens · Sintético</small><strong>${fmt(c.eur_per_1k,3)}</strong></div><div><small>gCO₂e/1.000 tokens · Sintético</small><strong>${fmt(c.g_per_1k,2)}</strong></div></div>`).join('');
}catch(err){showError(err);$('route-btn').disabled=true;}}
initialize();
