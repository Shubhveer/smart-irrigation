const translations = {
  en: {
    brand: "Water My Field", history_link: "Past Checks",
    eyebrow: "SMART IRRIGATION SYSTEM",
    headline: "Should I water my field today?",
    subhead: "Answer 4 quick questions. Takes 30 seconds.",
    q_location: "Where is your field?", q_location_ph: "Type your city or village name",
    q_soil: "What is your soil like?",
    soil_sandy: "Sandy", soil_sandy_sub: "Drains fast",
    soil_loamy: "Loamy", soil_loamy_sub: "Normal soil",
    soil_clay: "Clay", soil_clay_sub: "Holds water",
    q_stage: "How grown is your crop?",
    stage_seedling: "Just Planted", stage_growing: "Growing",
    stage_flowering: "Flowering", stage_mature: "Ready to Harvest",
    q_size: "Field size (acres)", cta: "Check Now",
    result_yes: "Yes — water your field today", result_no: "No need to water today",
    liters: "Liters", listen: "Listen",
    temp: "Temp", humidity: "Humidity", rainfall: "Rain",
    tips_heading: "Tips",
    tip_irrigate_time: "Water early morning or evening, not midday",
    tip_check_soil: "Press soil with your finger — if dry 2 inches down, water is needed",
    tip_avoid_rain: "Rain is expected — you can skip watering",
    forecast_heading: "Next 7 Days", save_report: "Save Report", check_again: "Check Another",
  },
  hi: {
    brand: "खेत में पानी", history_link: "पुरानी जांच",
    eyebrow: "स्मार्ट सिंचाई प्रणाली",
    headline: "क्या आज खेत में पानी देना चाहिए?",
    subhead: "4 आसान सवाल। सिर्फ 30 सेकंड लगेंगे।",
    q_location: "आपका खेत कहाँ है?", q_location_ph: "अपने शहर या गाँव का नाम लिखें",
    q_soil: "आपकी मिट्टी कैसी है?",
    soil_sandy: "रेतीली", soil_sandy_sub: "जल्दी सूखती है",
    soil_loamy: "दोमट", soil_loamy_sub: "सामान्य मिट्टी",
    soil_clay: "चिकनी", soil_clay_sub: "पानी रोकती है",
    q_stage: "फसल कितनी बड़ी हो गई है?",
    stage_seedling: "अभी लगाई", stage_growing: "बढ़ रही है",
    stage_flowering: "फूल आ रहे हैं", stage_mature: "कटाई के लिए तैयार",
    q_size: "खेत का आकार (एकड़)", cta: "अभी जांचें",
    result_yes: "हाँ — आज खेत में पानी दें", result_no: "आज पानी देने की जरूरत नहीं",
    liters: "लीटर", listen: "सुनें",
    temp: "तापमान", humidity: "नमी", rainfall: "बारिश",
    tips_heading: "सुझाव",
    tip_irrigate_time: "सुबह जल्दी या शाम को पानी दें, दोपहर में नहीं",
    tip_check_soil: "मिट्टी को उंगली से दबाएं — अगर 2 इंच नीचे तक सूखी है तो पानी चाहिए",
    tip_avoid_rain: "बारिश होने वाली है — पानी देना छोड़ सकते हैं",
    forecast_heading: "अगले 7 दिन", save_report: "रिपोर्ट सेव करें", check_again: "दूसरे खेत की जांच करें",
  },
};

function applyLanguage(lang) {
  const dict = translations[lang] || translations.en;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.innerHTML = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key]) el.setAttribute("placeholder", dict[key]);
  });
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
  document.documentElement.lang = lang;
  localStorage.setItem("preferredLang", lang);
}

document.addEventListener("DOMContentLoaded", () => {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/service-worker.js").catch(() => {});
  }

  const savedLang = localStorage.getItem("preferredLang") || "en";
  applyLanguage(savedLang);
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
  });

  const sizeInput = document.getElementById("field_size");
  const minusBtn = document.getElementById("sizeMinus");
  const plusBtn = document.getElementById("sizePlus");
  if (sizeInput && minusBtn && plusBtn) {
    minusBtn.addEventListener("click", () => {
      sizeInput.value = Math.max(0.5, (parseFloat(sizeInput.value) || 1) - 0.5);
    });
    plusBtn.addEventListener("click", () => {
      sizeInput.value = (parseFloat(sizeInput.value) || 1) + 0.5;
    });
  }

  const listenBtn = document.getElementById("listenBtn");
  if (listenBtn && "speechSynthesis" in window) {
    listenBtn.addEventListener("click", () => {
      const lang = localStorage.getItem("preferredLang") || "en";
      const message = lang === "hi" ? listenBtn.dataset.messageHi : listenBtn.dataset.messageEn;
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.lang = lang === "hi" ? "hi-IN" : "en-IN";
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    });
  } else if (listenBtn) {
    listenBtn.style.display = "none";
  }
});
