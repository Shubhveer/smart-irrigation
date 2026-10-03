(function(){
  const KEY='farm_saathi_language';
  function lang(){ return localStorage.getItem(KEY)||'en'; }
  function translateNode(node, dict){
    if(node.nodeType!==Node.TEXT_NODE || !node.nodeValue.trim()) return;
    const raw=node.nodeValue;
    const leading=raw.match(/^\s*/)[0], trailing=raw.match(/\s*$/)[0];
    const key=raw.trim();
    if(dict[key]) node.nodeValue=leading+dict[key]+trailing;
  }
  function applyLanguage(l){
    const dict=(window.FARM_SAATHI_TRANSLATIONS||{}).en;
    const target=(window.FARM_SAATHI_TRANSLATIONS||{})[l]||dict;
    document.title = target[document.title] || document.title;
    document.querySelectorAll('body *').forEach(el=>{
      if(['SCRIPT','STYLE','OPTION'].includes(el.tagName)) return;
      Array.from(el.childNodes).forEach(n=>translateNode(n,target));
      ['placeholder','title','aria-label'].forEach(a=>{ if(el.hasAttribute(a)){ const v=el.getAttribute(a); if(target[v]) el.setAttribute(a,target[v]); }});
    });
    document.querySelectorAll('option').forEach(o=>{ const v=o.textContent.trim(); if(target[v]) o.textContent=target[v]; });
    document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('active',b.dataset.lang===l));
    document.documentElement.lang=l==='hi'?'hi':l==='mr'?'mr':'en';
    document.body.dataset.language=l;
  }
  window.setFarmLanguage=function(l){ localStorage.setItem(KEY,l); location.reload(); };
  document.addEventListener('DOMContentLoaded',()=>applyLanguage(lang()));
})();
