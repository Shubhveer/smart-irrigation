"""Post/Redirect/Get helpers.

A result is stored (in its language-neutral form) in the visitor's session and the browser is redirected to a GET page.
That lets the visitor switch language on a result page without re-submitting the form.
"""
from flask import request, session


def stash(name, result):
    session[f"result_{name}"] = result


def recall(name):
    """The stored result, only when the URL carries ?r=1 (so revisiting the page from the menu shows a blank form)."""
    return session.get(f"result_{name}") if request.args.get("r") else None
