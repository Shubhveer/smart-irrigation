# Languages: English, Hindi (हिन्दी), Marathi (मराठी)

Everything a visitor sees is translated on the server before it reaches the browser: pages, form options, placeholders,
results (irrigation, crop health, soil, fertilizer, pest, image check, disease names and advice), error and flash messages,
the Excel report and the mobile-API text.

## How a visitor changes language
Click **English / हिन्दी / मराठी** in the top bar. The choice is stored in a cookie. On a first visit the browser's language
is used if it is Hindi or Marathi. Result pages keep their result when the language is switched.

## How it works
| Piece | File |
|---|---|
| Translation engine | `services/i18n.py` |
| Hindi / Marathi text | `translations/hi.json`, `translations/mr.json` (English sentence -> translation) |
| Language switch route | `routes/i18n_routes.py` (`/set-language/<hi|mr|en>`) |
| Templates | `{{ _("English text") }}` for fixed text, `{{ value|t }}` for values coming from Python |
| Python code | returns English text, or `M("Hello {name}", name=x)` when the text contains data |

The English sentence in the code is the key. If a key is missing from a catalog the English text is shown, and the test below fails.

## Change a translation
Edit the value in `translations/hi.json` or `translations/mr.json`. Keep placeholders such as `{crop}` exactly as they are.

## Add or change an English sentence
1. Use `_("New sentence")` in the template (or return it from the service).
2. Add `"New sentence": "..."` to **both** JSON files.
3. Run the tests.

## Add another language (e.g. Gujarati)
1. Create `translations/gu.json` with every key from `hi.json`.
2. Add `"gu": "ગુજરાતી"` to `LANGS` in `services/i18n.py`.
3. Add `"gu"` to `TRANSLATED` in `tests/test_i18n.py` and run the tests.

## Test that nothing is left in English
```
python -m unittest tests.test_i18n -v
```
The test opens every page in every language, submits every form variant, runs all 38 disease classes, calls the API and builds
the Excel report. It fails if any text is missing a translation or any English word remains in a Hindi/Marathi page
(units like C, file types like JPG and official acronyms like ICAR are allowed).

## Mobile API
`POST /api/irrigation` and `POST /api/disease-detect` accept `lang` (JSON field for irrigation, `?lang=` for both) or an
`Accept-Language` header. Existing fields are unchanged; new fields hold ready-to-show text:
`irrigation.alert_text`, `weather_alerts_text`, `recommendations_text`, `week_prediction[].day_text` / `irrigation_text`, and
for images `top_predictions[].plant_text` / `disease_text`. The Flutter app's own screens are separate and are not covered here.

## Quality note
The Hindi and Marathi were written for this project and the first 227 phrases came from your existing dictionary. Agriculture
terms (disease names, fertilizer advice) should be reviewed once by a Hindi/Marathi speaker or your local agriculture officer.
