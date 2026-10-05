from flask import Blueprint, abort, redirect, request

from services.i18n import COOKIE_NAME, LANGS, safe_next

i18n_bp = Blueprint("i18n", __name__)


@i18n_bp.get("/set-language/<code>")
def set_language(code):
    """Remember the language in a cookie, then go back to the page the visitor was on."""
    if code not in LANGS:
        abort(404)
    resp = redirect(safe_next(request.args.get("next")))
    resp.set_cookie(COOKIE_NAME, code, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return resp
