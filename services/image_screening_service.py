import logging

from PIL import Image, ImageFilter, UnidentifiedImageError
import numpy as np

from services import disease_service

logger = logging.getLogger(__name__)

ALLOWED = {"jpg", "jpeg"}
SPOT_THRESHOLD = 0.004  # calibrated on PlantVillage: flags ~1% of healthy and ~45% of diseased leaves


def _leaf_spot_fraction(a):
    """Share of the leaf area covered by brown/red lesion-coloured pixels (None if no leaf found)."""
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    green = (g > r * 1.05) & (g > b * 1.05) & (g > 40)
    density = np.asarray(Image.fromarray((green * 255).astype("uint8")).filter(ImageFilter.BoxBlur(6)),
                         dtype=np.float32) / 255
    leaf = density > 0.35
    if leaf.sum() < 0.03 * leaf.size:
        return None
    lesion = (r > g * 1.08) & (r > b * 1.15) & (r < 210) & (r > 50)
    return float((lesion & leaf).sum() / leaf.sum())


def screen_image(file_obj, mode="plant"):
    # Plant photos: use the trained disease model when it is installed
    if mode == "plant" and disease_service.is_available():
        try:
            return disease_service.predict(file_obj)
        except UnidentifiedImageError:
            raise  # not an image: let the route report it
        except Exception:
            logger.exception("Disease model failed; using colour heuristic")
            file_obj.seek(0)
    img = Image.open(file_obj).convert("RGB")
    img.thumbnail((700, 700))
    a = np.asarray(img).astype(np.float32)
    if mode == "plant":
        r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
        green = ((g > r*1.08) & (g > b*1.05) & (g > 45)).mean()
        yellow = ((r > 90) & (g > 80) & (b < 90) & (abs(r-g) < 80)).mean()
        brown = ((r > b*1.25) & (g > b*1.05) & (r < 190)).mean()
        spots = _leaf_spot_fraction(a)
        if spots is not None and spots > SPOT_THRESHOLD:
            finding = "Visible spots or lesions on the leaf (cause cannot be identified without the disease model)"
        elif green > 0.35 and yellow < 0.25:
            finding = "Mostly green leaf, no obvious spots found by the colour check"
        elif yellow > 0.18:
            finding = "Possible yellowing pattern"
        elif brown > 0.20:
            finding = "Possible dry or damaged area"
        else:
            finding = "No clear visual pattern"
        recommendation = ["Colour check only: it cannot name a disease and misses about half of diseased leaves, so "
                          "\"no spots found\" does NOT mean healthy. Install the trained disease model for a diagnosis, "
                          "and confirm with an expert before any treatment."]
    else:
        brightness = a.mean()
        varied = a.std() > 55
        if brightness < 85:
            finding = "Dark soil appearance with visible variation" if varied else "Dark soil appearance"
        elif brightness > 165:
            finding = "Light soil appearance with visible variation" if varied else "Light soil appearance"
        else:
            finding = "Mixed soil appearance with visible variation" if varied else "Mixed soil appearance"
        recommendation = ["A soil photo cannot reliably determine pH, N-P-K, moisture or fertilizer dose. "
                          "Use a laboratory soil test or calibrated sensor for those decisions."]
    return {"finding": finding, "recommendation": recommendation}
