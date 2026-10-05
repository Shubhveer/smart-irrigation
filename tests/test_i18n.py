"""
Translation tests. Run from the project root:   python -m unittest tests.test_i18n -v

They check that EVERYTHING a visitor can see is translated:
  1. every page, in every language, with every form variant submitted;
  2. every disease/crop name the model can output (all 38 classes);
  3. the JSON API and the Excel report;
  4. that catalogs are complete and keep their {placeholders}.
"""
import io
import json
import os
import re
import sys
import tempfile
import types
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db"))
os.environ["I18N_TRACK_MISSING"] = "1"

import numpy as np                      # noqa: E402
from PIL import Image                   # noqa: E402

from services import i18n               # noqa: E402
i18n.TRACK_MISSING = True

from app import app                     # noqa: E402
from services import disease_service, irrigation_service, weather_service  # noqa: E402

TRANSLATED = ["hi", "mr"]
# Latin-script text that is allowed to stay in the translated pages (units, symbols, file types, official acronyms, names typed by the user)
ALLOWED_LATIN = {"English", "pH", "N", "P", "K", "C", "JPG", "JPEG", "PIB", "ICAR", "Excel",
                 "Nagpur", "Pune", "Mumbai", "Atlantis"}   # last row: place names typed by the test

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# --------------------------------------------------------------------------------------------- helpers
class _Text(HTMLParser):
    """Collects everything a person can read: text nodes plus placeholder/title/aria-label/alt attributes."""
    SKIP = {"script", "style"}
    ATTRS = {"placeholder", "title", "aria-label", "alt"}

    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        for k, v in attrs:
            if k in self.ATTRS and v:
                self.parts.append(v)

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def visible_text(html):
    p = _Text()
    p.feed(html)
    return p.parts


def english_leftovers(html, extra_allowed=()):
    """Latin-script words still present in a page that should be fully Hindi/Marathi."""
    allowed = ALLOWED_LATIN | set(extra_allowed)
    out = []
    for chunk in visible_text(html):
        words = [w for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*", chunk) if w not in allowed]
        if words:
            out.append(chunk)
    return out


def has_english(text):
    """True if a text still contains English words (technical terms like JSON are fine)."""
    ok = ALLOWED_LATIN | {"JSON", "MB"}
    return any(w not in ok for w in re.findall(r"[A-Za-z]+", str(text)))


def fake_weather(hot_dry=True):
    if hot_dry:
        return ({"temperature": 39, "humidity": 25, "rainfall": 8},
                [{"day": d, "temp": 38, "humidity": 28, "rainfall": 0} for d in DAYS[:5]])
    return ({"temperature": 22, "humidity": 80, "rainfall": 0},
            [{"day": d, "temp": 21, "humidity": 85, "rainfall": 6} for d in DAYS[:5]])


def colourful_jpeg():
    """A synthetic 'photo' that passes the not-a-photo guard."""
    rng = np.random.default_rng(1)
    base = np.zeros((256, 256, 3), dtype=np.uint8)
    base[..., 1] = np.linspace(60, 200, 256)[None, :]
    base[..., 0] = np.linspace(20, 140, 256)[:, None]
    base = np.clip(base.astype(int) + rng.integers(0, 40, base.shape), 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(base).save(buf, "JPEG")
    buf.seek(0)
    return buf


class FakeSession:
    """Stands in for the ONNX session: always predicts class `idx` with high confidence."""
    def __init__(self, idx, n):
        self.idx, self.n = idx, n

    def get_inputs(self):
        return [types.SimpleNamespace(name="input")]

    def run(self, _out, _feed):
        logits = np.zeros((1, self.n), dtype=np.float32)
        if self.idx is not None:
            logits[0, self.idx] = 12.0
        return [logits]


def set_lang(client, code):
    client.set_cookie("lang", code)


def crawl(client, lang):
    """Visit everything. Returns {name: html}."""
    set_lang(client, lang)
    pages = {}
    get = lambda name, url, **kw: pages.__setitem__(name, client.get(url, **kw).get_data(as_text=True))

    for name, url in [("index", "/"), ("crop_health", "/crop-health"), ("soil", "/soil"), ("fertilizer", "/fertilizer"),
                      ("pest", "/pest"), ("farm_plan", "/farm-plan"), ("history_empty", "/history"),
                      ("news", "/government-news"), ("image_check", "/image-check"), ("not_found", "/no-such-page")]:
        get(name, url)

    # --- irrigation: needed (hot/dry, all alerts) and not needed (mild, wet), plus history and result pages
    for hot in (True, False):
        w, f = fake_weather(hot)
        with mock.patch.object(weather_service, "get_weather", return_value=w), \
                mock.patch.object(weather_service, "get_forecast", return_value=f), \
                mock.patch.object(irrigation_service, "predict_irrigation", return_value=1 if hot else 0):
            r = client.post("/predict", data={"location": "Nagpur", "soil_type": "1", "crop_stage": "1",
                                              "field_size": "2"}, follow_redirects=True)
            pages[f"result_hot={hot}"] = r.get_data(as_text=True)
    get("history", "/history")
    # form validation / error messages
    pages["flash_missing"] = client.post("/predict", data={"location": ""}, follow_redirects=True).get_data(as_text=True)
    pages["flash_numbers"] = client.post("/predict", data={"location": "X", "soil_type": "a", "crop_stage": "b"},
                                         follow_redirects=True).get_data(as_text=True)
    with mock.patch.object(weather_service, "get_weather", side_effect=weather_service.WeatherServiceError("x")):
        pages["flash_weather"] = client.post("/predict", data={"location": "Atlantis", "soil_type": "1",
                                                               "crop_stage": "1"}, follow_redirects=True).get_data(as_text=True)
    get("report_missing", "/download/99999", follow_redirects=True)

    # --- crop health: every branch of the advisory logic
    for i, syms in enumerate([["white", "spots"], ["curling", "insects"], ["yellow", "stunted"], ["wilting"],
                              ["holes"], ["insects"], []]):
        r = client.post("/crop-health", data={"crop": "Cotton", "stage": "Flowering", "symptoms": syms},
                        follow_redirects=True)
        pages[f"crop_health_{i}"] = r.get_data(as_text=True)

    # --- soil
    for i, form in enumerate([{"ph": "4.9", "n": "20", "p": "10", "k": "30", "moisture": "22"}, {"ph": "6.8"},
                              {"ph": "8.6"}, {"ph": "7.9", "moisture": "10"}, {}]):
        pages[f"soil_{i}"] = client.post("/soil", data=dict(crop="Wheat", **form), follow_redirects=True).get_data(as_text=True)

    # --- fertilizer
    concerns = ["General nutrient planning", "Low nitrogen suspected", "Low phosphorus suspected",
                "Low potassium suspected", "Crop growth is weak"]
    stages = ["Before sowing", "Early growth", "Vegetative growth", "Flowering", "Fruit / pod development", "Near harvest"]
    for i, c in enumerate(concerns):
        for test in ("yes", "no"):
            pages[f"fert_{i}_{test}"] = client.post("/fertilizer", data={
                "crop": ["Cotton", "Soybean", "Wheat", "Sugarcane", "Orange"][i], "stage": stages[i], "test": test,
                "concern": c}, follow_redirects=True).get_data(as_text=True)
    for j, st in enumerate(stages):
        pages[f"fert_stage_{j}"] = client.post("/fertilizer", data={"crop": "Cotton", "stage": st, "test": "yes",
                                                                    "concern": concerns[0]}, follow_redirects=True).get_data(as_text=True)

    # --- pest
    for s in ["holes", "curling", "sticky", "wilting", "spots", "insects"]:
        pages[f"pest_{s}"] = client.post("/pest", data={"crop": "Soybean", "symptom": s, "part": "Stem"},
                                         follow_redirects=True).get_data(as_text=True)

    # --- image check: soil (6 outcomes), plant heuristic, not-an-image errors
    def img_post(mode, make=None, name="a.jpg", data=None):
        payload = data if data is not None else (make() if make else colourful_jpeg())
        return client.post("/image-check", data={"mode": mode, "image": (payload, name)},
                           content_type="multipart/form-data", follow_redirects=True).get_data(as_text=True)

    def flat(v, noise=0):
        def make():
            a = np.full((200, 200, 3), v, dtype=np.uint8)
            if noise:
                a = np.clip(a.astype(int) + np.random.default_rng(0).integers(-noise, noise, a.shape), 0, 255).astype(np.uint8)
            b = io.BytesIO(); Image.fromarray(a).save(b, "JPEG"); b.seek(0); return b
        return make

    for i, mk in enumerate([flat(40), flat(40, 120), flat(120), flat(120, 100), flat(200), flat(200, 90)]):
        pages[f"soil_img_{i}"] = img_post("soil", mk)
    with mock.patch.object(disease_service, "is_available", return_value=False):   # colour-heuristic fallback
        def tinted(rgb, blobs=False):
            def make():
                a = np.zeros((200, 200, 3), dtype=np.uint8); a[:] = rgb
                if blobs:
                    a[60:90, 60:90] = (150, 80, 50); a[110:140, 100:130] = (140, 70, 45)
                b = io.BytesIO(); Image.fromarray(a).save(b, "JPEG"); b.seek(0); return b
            return make
        for i, mk in enumerate([tinted((40, 160, 50)), tinted((40, 160, 50), True), tinted((200, 190, 40)),
                                tinted((150, 110, 60)), tinted((90, 90, 90))]):
            pages[f"plant_heur_{i}"] = img_post("plant", mk)
    pages["img_not_jpg"] = img_post("plant", name="a.png")
    pages["img_bad"] = img_post("plant", data=io.BytesIO(b"not an image"))
    pages["img_none"] = client.post("/image-check", data={"mode": "plant"}, follow_redirects=True).get_data(as_text=True)
    pages["img_too_big"] = client.post("/image-check", data={"mode": "plant", "image": (io.BytesIO(b"0" * 6_000_000), "a.jpg")},
                                       content_type="multipart/form-data", follow_redirects=True).get_data(as_text=True)

    # --- trained model: every one of the 38 classes, confident, plus a low-confidence and a blank image
    labels = json.loads((ROOT / "models/disease_labels.json").read_text()) if (ROOT / "models/disease_labels.json").exists() else []
    if labels:
        for i, label in enumerate(labels):
            with mock.patch.object(disease_service, "is_available", return_value=True), \
                    mock.patch.object(disease_service, "_load", return_value=(FakeSession(i, len(labels)), labels)):
                pages[f"disease_{i}"] = img_post("plant")
        with mock.patch.object(disease_service, "is_available", return_value=True), \
                mock.patch.object(disease_service, "_load", return_value=(FakeSession(None, len(labels)), labels)):
            pages["disease_low_conf"] = img_post("plant")
        pages["disease_blank"] = img_post("plant", flat(128))
    return pages


# ------------------------------------------------------------------------------------------------ tests
class CatalogTests(unittest.TestCase):
    def test_catalogs_exist_and_keep_placeholders(self):
        for lang in TRANSLATED:
            cat = i18n.catalog(lang)
            self.assertGreater(len(cat), 100, lang)
            for key, val in cat.items():
                self.assertTrue(val.strip(), f"{lang}: empty translation for {key!r}")
                self.assertEqual(sorted(re.findall(r"\{\w+\}", key)), sorted(re.findall(r"\{\w+\}", val)),
                                 f"{lang}: placeholders differ for {key!r}")

    def test_open_redirect_is_blocked(self):
        self.assertEqual(i18n.safe_next("https://evil.example"), "/")
        self.assertEqual(i18n.safe_next("//evil.example"), "/")
        self.assertEqual(i18n.safe_next("/soil?r=1"), "/soil?r=1")


class MessageTableTests(unittest.TestCase):
    """Every fixed message the code can produce must exist in both catalogs, whether or not a page happened to show it."""

    def test_all_fixed_messages_have_translations(self):
        from routes.farm_routes import PEST_SYMPTOMS
        from services import farm_advisory_service as fa
        from services.government_news import OFFICIAL_SOURCES
        texts = set(irrigation_service.ALERT_TEXT.values()) | set(irrigation_service.RECOMMENDATION_TEXT.values())
        texts |= set(disease_service.ADVICE.values()) | {disease_service.CONFIRM_NOTE}
        texts |= {s["name"] for s in fa.SYMPTOMS} | {s["name"] for s in PEST_SYMPTOMS} | set(fa.CROP_OPTIONS)
        for t in fa.farm_tasks():
            texts |= set(t.values())
        for n in OFFICIAL_SOURCES:
            texts |= {n["title"], n["source"]}
        for lang in TRANSLATED:
            cat = i18n.catalog(lang)
            absent = sorted(t for t in texts if t not in cat)
            self.assertEqual(absent, [], f"{lang}: {absent}")


class TemplateStringTests(unittest.TestCase):
    """Static scan of the templates: every string written in them exists in both catalogs (all if/else branches)."""

    def test_every_template_string_has_translations(self):
        strings = set()
        for f in (ROOT / "templates").glob("*.html"):
            src = f.read_text(encoding="utf-8")
            strings |= {m.group(2) for m in re.finditer(r"""_\(\s*(["'])(.*?)\1\s*[,)]""", src)}   # _("text")
            for lst in re.findall(r"\{%\s*for\s+\w+\s+in\s+\[(.*?)\]\s*%\}", src):               # option lists
                strings |= set(re.findall(r'"([^"]+)"', lst))
        self.assertGreater(len(strings), 100)
        for lang in TRANSLATED:
            cat = i18n.catalog(lang)
            absent = sorted(s for s in strings if s not in cat)
            self.assertEqual(absent, [], f"{lang}: {absent}")


class WebsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.pages = {}
        i18n.MISSING.clear()
        for lang in ["en"] + TRANSLATED:
            client = app.test_client()
            cls.pages[lang] = crawl(client, lang)

    def test_no_missing_translation_keys(self):
        missing = sorted(i18n.MISSING)
        self.assertEqual(missing, [], f"{len(missing)} untranslated strings, e.g. {missing[:5]}")

    def test_translated_pages_have_no_english_left(self):
        problems = {}
        for lang in TRANSLATED:
            for name, html in self.pages[lang].items():
                left = english_leftovers(html)
                if left:
                    problems[f"{lang}:{name}"] = left[:4]
        self.assertEqual(problems, {}, json.dumps(problems, ensure_ascii=False, indent=1)[:3000])

    def test_language_attribute_and_switcher(self):
        for lang in ["en"] + TRANSLATED:
            html = self.pages[lang]["index"]
            self.assertIn(f'<html lang="{lang}">', html)
            self.assertEqual(html.count("set-language/"), 3)

    def test_english_pages_unchanged_in_meaning(self):
        # the English site still shows the original English text
        self.assertIn("Good day. What do you need to check?", self.pages["en"]["index"])
        self.assertIn("Irrigation history", self.pages["en"]["history"])

    def test_results_survive_language_switch(self):
        client = app.test_client()
        set_lang(client, "en")
        client.post("/soil", data={"crop": "Wheat", "ph": "4.9"})
        en = client.get("/soil?r=1").get_data(as_text=True)
        self.assertIn("Low pH needs attention", en)
        r = client.get("/set-language/hi?next=/soil?r=1")
        self.assertEqual(r.status_code, 302)
        client.set_cookie("lang", "hi")
        hi = client.get("/soil?r=1").get_data(as_text=True)
        self.assertNotIn("Low pH needs attention", hi)
        self.assertIn(i18n.catalog("hi")["Low pH needs attention"], hi)

    def test_set_language_validation(self):
        c = app.test_client()
        self.assertEqual(c.get("/set-language/xx").status_code, 404)
        r = c.get("/set-language/mr?next=https://evil.example")
        self.assertEqual(r.headers["Location"], "/")
        self.assertIn("lang=mr", r.headers.get("Set-Cookie", ""))

    def test_browser_language_is_respected_until_user_chooses(self):
        c = app.test_client()
        html = c.get("/", headers={"Accept-Language": "hi-IN,hi;q=0.9,en;q=0.5"}).get_data(as_text=True)
        self.assertIn('<html lang="hi">', html)
        html = c.get("/", headers={"Accept-Language": "fr-FR,fr;q=0.9"}).get_data(as_text=True)
        self.assertIn('<html lang="en">', html)

    def test_every_disease_class_translated(self):
        labels = json.loads((ROOT / "models/disease_labels.json").read_text())
        for lang in TRANSLATED:
            cat = i18n.catalog(lang)
            for label in labels:
                plant, _, disease = label.partition("___")
                for part in (plant.replace("_", " ").strip(), disease.replace("_", " ").strip()):
                    self.assertIn(part, cat, f"{lang}: {part!r}")


class ApiAndReportTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_irrigation_api_is_translated(self):
        w, f = fake_weather(True)
        for lang in TRANSLATED:
            with mock.patch.object(weather_service, "get_weather", return_value=w), \
                    mock.patch.object(weather_service, "get_forecast", return_value=f), \
                    mock.patch.object(irrigation_service, "predict_irrigation", return_value=1):
                r = self.client.post("/api/irrigation", json={"location": "Nagpur", "soil_type": 1, "crop_stage": 1,
                                                              "field_size": 1, "lang": lang})
            j = r.get_json()
            self.assertTrue(j["success"])
            self.assertEqual(j["lang"], lang)
            self.assertEqual(j["weather_alerts"], ["LOW_HUMIDITY", "HIGH_TEMP", "RAIN_EXPECTED"])   # codes unchanged
            texts = j["weather_alerts_text"] + j["recommendations_text"] + [j["irrigation"]["alert_text"]]
            texts += [d["day_text"] for d in j["week_prediction"]] + [d["irrigation_text"] for d in j["week_prediction"]]
            for t in texts:
                self.assertFalse(has_english(t), f"{lang}: {t!r}")

    def test_api_errors_are_translated(self):
        for lang in TRANSLATED:
            j = self.client.post("/api/irrigation", json={"lang": lang, "location": ""}).get_json()
            self.assertFalse(has_english(j["error"]), j["error"])
            j = self.client.post("/api/irrigation", data="x", headers={"Accept-Language": lang}).get_json()
            self.assertFalse(has_english(j["error"]), j["error"])
            r = self.client.post(f"/api/disease-detect?lang={lang}")
            self.assertEqual(r.status_code, 400)
            self.assertFalse(has_english(r.get_json()["error"]))

    def test_excel_report_is_translated(self):
        import pandas as pd
        from database.db import SessionLocal
        from database.models import Prediction
        from services import report_service
        db = SessionLocal()
        rec = Prediction(location="Nagpur", soil_type=1, crop_stage=1, field_size=1, temperature=30, humidity=40,
                         rainfall=0, alert="Irrigation Required", water_today=500,
                         week_prediction=[{"day": "Monday", "irrigation": "No Irrigation", "water": 0}])
        db.add(rec); db.commit(); db.refresh(rec)
        try:
            for lang in TRANSLATED:
                df = pd.read_excel(report_service.build_excel_report(rec, lang))
                for text in list(df.columns) + [v for v in df["{}".format(df.columns[5])]]:
                    self.assertFalse(has_english(str(text)), f"{lang}: {text!r}")
            en = pd.read_excel(report_service.build_excel_report(rec, "en"))
            self.assertIn("Irrigation", list(en.columns))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
