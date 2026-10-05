"""
Server-side translation for English / Hindi / Marathi.

How it works
------------
* Source text in the code is English. It is the lookup key into translations/hi.json and translations/mr.json.
* Services return plain English strings, or M("text with {placeholders}", name=value) for text that contains data.
  Nothing is translated until it is displayed, so a result can be re-rendered in another language.
* Templates:  {{ _("Some text") }}     {{ value|t }}     {{ _("Hello {name}", name=x) }}
* JSON/Excel/flash messages call tr(...) directly.
* Language comes from ?lang=, the "lang" cookie (set by /set-language/<code>), or the browser's Accept-Language.

To add a language: create translations/<code>.json, add it to LANGS, and add the code to the test in tests/test_i18n.py.
"""
import json
import os
from functools import lru_cache
from pathlib import Path

LANGS = {"en": "English", "hi": "हिन्दी", "mr": "मराठी"}
DEFAULT_LANG = "en"
COOKIE_NAME = "lang"
CATALOG_DIR = Path(__file__).resolve().parent.parent / "translations"

TRACK_MISSING = os.getenv("I18N_TRACK_MISSING") == "1"
MISSING = set()          # (lang, key) pairs that had no translation (only filled when TRACK_MISSING)


@lru_cache(maxsize=None)
def catalog(lang):
    f = CATALOG_DIR / f"{lang}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def get_lang():
    """Language for the current request ('en' outside a request)."""
    try:
        from flask import has_request_context, request
    except ImportError:                                    # pragma: no cover
        return DEFAULT_LANG
    if not has_request_context():
        return DEFAULT_LANG
    code = request.args.get("lang")
    if code in LANGS:
        return code
    code = request.cookies.get(COOKIE_NAME)
    if code in LANGS:
        return code
    for value, _quality in request.accept_languages:       # ordered by the browser's preference
        primary = value.split("-")[0].lower()
        if primary in LANGS:
            return primary
    return DEFAULT_LANG


def M(key, **params):
    """A message with data in it. JSON-serialisable, so it can be stored in the session."""
    return {"_k": key, "_p": params} if params else key


def _lookup(key, lang, track=True):
    if lang == DEFAULT_LANG or not key:
        return key
    found = catalog(lang).get(key)
    if found is None:
        if TRACK_MISSING and track:
            MISSING.add((lang, key))
        return key
    return found


def tr(x, lang=None, _track=True):
    """Translate a str, an M(...) message, or a list of them. Anything else is returned unchanged."""
    lang = lang or get_lang()
    if isinstance(x, dict) and "_k" in x:
        text = _lookup(x["_k"], lang, _track)
        # Values inside a message may be user-typed (a place name), so they are not reported as missing.
        params = {k: (tr(v, lang, False) if isinstance(v, (str, dict)) else v) for k, v in x.get("_p", {}).items()}
        try:
            return text.format(**params)
        except (KeyError, IndexError, ValueError):
            return text
    if isinstance(x, str):
        return _lookup(x, lang, _track)
    if isinstance(x, (list, tuple)):
        return [tr(i, lang, _track) for i in x]
    return x


def gettext(key, **params):
    """Template helper: {{ _("text") }} or {{ _("text {n}", n=3) }}."""
    return tr(M(key, **params))


def safe_next(target, fallback="/"):
    """Only allow redirects to a path on this site (prevents open redirects)."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return fallback
    return target


def init_app(app):
    from flask import request

    app.jinja_env.globals["_"] = gettext
    app.jinja_env.filters["t"] = tr

    @app.context_processor
    def _inject():
        return {"lang": get_lang(), "LANGS": LANGS,
                "current_url": (request.full_path[:-1] if request.full_path.endswith("?") else request.full_path)}
