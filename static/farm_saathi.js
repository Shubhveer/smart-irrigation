const langData={
en:{},
hi:{
"Dashboard":"डैशबोर्ड","Crop Health":"फसल स्वास्थ्य","Soil":"मिट्टी","Fertilizer":"उर्वरक","Pest Guide":"कीट मार्गदर्शक","Farm Plan":"खेत योजना","Records":"रिकॉर्ड"
},
mr:{
"Dashboard":"डॅशबोर्ड","Crop Health":"पिकाचे आरोग्य","Soil":"माती","Fertilizer":"खत","Pest Guide":"कीड मार्गदर्शक","Farm Plan":"शेत योजना","Records":"नोंदी"
}};
function setLang(lang){
 document.querySelectorAll(".nav a").forEach(a=>{
   const key=a.textContent.trim(); if(langData[lang]&&langData[lang][key]) a.textContent=langData[lang][key];
 });
 document.querySelectorAll(".lang-btn").forEach(b=>b.classList.toggle("active",b.dataset.lang===lang));
 localStorage.setItem("farm-saathi-lang",lang);
}
document.addEventListener("DOMContentLoaded",()=>{
 const l=localStorage.getItem("farm-saathi-lang")||"en"; setLang(l);
 document.querySelectorAll(".lang-btn").forEach(b=>b.addEventListener("click",()=>setLang(b.dataset.lang)));
});
