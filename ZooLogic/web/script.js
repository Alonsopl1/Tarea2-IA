'use strict';
const byId = id => document.getElementById(id);
const examples=byId('examples'),messages=byId('messages'),form=byId('chatForm');
const modeInfo={
  prolog:'El intérprete de Python identifica consultas frecuentes; Prolog aplica las 8 reglas originales. No usa LLM.',
  llm:'Llama 3.2 traduce tu pregunta a una consulta permitida; Python la valida y SWI-Prolog obtiene la respuesta. Se necesitan ambos motores.'
};
byId('modo').addEventListener('change',e=>{byId('modeInfo').textContent=modeInfo[e.target.value];});
function addMessage(text,who='bot',info=null,isError=false){
  const wrapper=document.createElement('div');wrapper.className='msg '+who+(isError?' error':'');
  if(who==='bot'){const avatar=document.createElement('div');avatar.className='avatar';avatar.textContent='Z';wrapper.append(avatar);}
  const bubble=document.createElement('div');bubble.className='bubble';
  if(who==='bot'){const sender=document.createElement('div');sender.className='sender';sender.textContent='ZooLogic';bubble.append(sender);}
  const msg=document.createElement('div');msg.textContent=text;bubble.append(msg);
  if(info && info.consulta && info.consulta!=='—'){
    const debug=document.createElement('div');debug.className='debug';
    debug.textContent='Motor: '+(info.motor||'—');
    const c=document.createElement('code');c.textContent='Consulta: '+info.consulta;debug.append(c);bubble.append(debug);
  }
  wrapper.append(bubble);messages.append(wrapper);messages.scrollTop=messages.scrollHeight;
  return wrapper;
}
async function submit(q){
  q=q.trim();if(!q)return;
  const mode=byId('modo').value;addMessage(q,'user');byId('pregunta').value='';
  byId('send').disabled=true;
  const loading=addMessage('Consultando...');
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pregunta:q,modo:mode})});
    const data=await r.json();loading.remove();addMessage(data.respuesta||'No hubo respuesta','bot',data,!data.ok);
  }catch(error){loading.remove();addMessage('No se pudo conectar al servidor: '+error.message,'bot',null,true);}
  finally{byId('send').disabled=false;byId('pregunta').focus();}
}
form.addEventListener('submit',e=>{e.preventDefault();submit(byId('pregunta').value);});
examples.addEventListener('click',e=>{if(e.target.dataset.question)submit(e.target.dataset.question);});
byId('clearChat').addEventListener('click',()=>{messages.innerHTML='';addMessage('Conversación reiniciada. Puedes seguir preguntando.');});
byId('showData').addEventListener('click',()=>byId('dataDialog').showModal());
byId('closeDialog').addEventListener('click',()=>byId('dataDialog').close());
Promise.all([
 fetch('/api/health').then(r=>r.json()),
 fetch('/api/animales').then(r=>r.json())
]).then(([state,data])=>{
  byId('status').textContent=state.prolog_instalado?'Prolog detectado':'Prolog no instalado';
  byId('status').previousElementSibling.classList.toggle('on',state.prolog_instalado);
  byId('factsBody').innerHTML='';
  for(const item of data.animales){const tr=document.createElement('tr');
    const a=document.createElement('td');a.textContent=item.animal.replaceAll('_',' ');
    const peso=document.createElement('td');peso.textContent=item.peso.toLocaleString('es-CL')+' kg';
    tr.append(a,peso);byId('factsBody').append(tr);
  }
}).catch(()=>{byId('status').textContent='Servidor desconectado';});
