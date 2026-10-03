from PIL import Image
import numpy as np

ALLOWED = {"jpg", "jpeg"}

def screen_image(file_obj, mode="plant"):
    img = Image.open(file_obj).convert("RGB")
    img.thumbnail((700, 700))
    a = np.asarray(img).astype(np.float32)
    if mode == "plant":
        r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
        green = ((g > r*1.08) & (g > b*1.05) & (g > 45)).mean()
        yellow = ((r > 90) & (g > 80) & (b < 90) & (abs(r-g) < 80)).mean()
        brown = ((r > b*1.25) & (g > b*1.05) & (r < 190)).mean()
        if green > 0.35 and yellow < 0.25:
            finding = "Healthy-looking green vegetation"
        elif yellow > 0.18:
            finding = "Possible yellowing pattern"
        elif brown > 0.20:
            finding = "Possible dry or damaged area"
        else:
            finding = "No clear visual pattern"
        recommendation = "Use this only as a preliminary visual screen. A confirmed disease diagnosis needs a validated crop-specific model or expert/lab confirmation."
    else:
        brightness = a.mean()
        spread = a.std()
        if brightness < 85:
            finding = "Dark soil appearance"
        elif brightness > 165:
            finding = "Light soil appearance"
        else:
            finding = "Mixed soil appearance"
        if spread > 55:
            finding += " with visible variation"
        recommendation = "A soil photo cannot reliably determine pH, N-P-K, moisture or fertilizer dose. Use a laboratory soil test or calibrated sensor for those decisions."
    return {"finding": finding, "recommendation": recommendation}
