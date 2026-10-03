CROP_OPTIONS = ["Cotton", "Soybean", "Wheat", "Sugarcane", "Orange"]

SYMPTOMS = [
    {"key": "yellow", "name": "Leaves turning yellow"},
    {"key": "spots", "name": "Brown or dark spots"},
    {"key": "curling", "name": "Leaves curling or distorted"},
    {"key": "wilting", "name": "Plant wilting"},
    {"key": "holes", "name": "Holes or chewing damage"},
    {"key": "white", "name": "White powder or coating"},
    {"key": "stunted", "name": "Slow or stunted growth"},
    {"key": "insects", "name": "Visible insects"},
]

def health_check(crop, stage, symptoms, notes):
    s = set(symptoms)
    if "white" in s and "spots" in s:
        title = "Possible fungal-type leaf problem"
        desc = "The combination of coating and leaf spots can occur with several fungal diseases."
        actions = [
            "Inspect both sides of several leaves and record whether the problem is spreading.",
            "Avoid prolonged leaf wetness and unnecessary overhead irrigation.",
            "Remove severely affected plant material where agronomically appropriate.",
            "Confirm the disease with a local agriculture professional before applying a fungicide."
        ]
    elif "curling" in s and ("insects" in s or "holes" in s):
        title = "Inspect for insect damage"
        desc = "Curling together with visible insects or chewing damage should trigger a close pest inspection."
        actions = [
            "Check the underside of young leaves and growing points.",
            "Inspect at least 10 plants from different parts of the field.",
            "Record the insect appearance and approximate number before treatment.",
            "Use an approved control only after the pest has been identified."
        ]
    elif "yellow" in s and "stunted" in s:
        title = "Check nutrition, roots and water"
        desc = "Yellowing and weak growth can have several causes, including nutrient shortage, water stress or root problems."
        actions = [
            "Compare affected plants with healthy plants in the same field.",
            "Check soil moisture around the root zone.",
            "Use a soil test before applying a large fertilizer dose.",
            "Inspect roots if the problem is localized or plants are collapsing."
        ]
    elif "wilting" in s:
        title = "Check water and root condition"
        desc = "Wilting is not enough to identify a disease by itself."
        actions = [
            "Check soil moisture before irrigating.",
            "Look for damaged roots, stem lesions or waterlogging.",
            "Check whether wilting occurs in patches or across the whole field.",
            "Seek local diagnosis if wilting continues despite suitable soil moisture."
        ]
    elif "holes" in s or "insects" in s:
        title = "Inspect for chewing insects"
        desc = "Leaf damage and visible insects suggest a pest inspection is useful."
        actions = [
            "Check leaf undersides, young shoots and nearby weeds.",
            "Look for larvae, eggs, webbing or fresh feeding damage.",
            "Record the affected area before choosing a control method.",
            "Prefer integrated pest management and verified local recommendations."
        ]
    else:
        title = "More observation is needed"
        desc = "The selected symptoms do not point to one reliable cause."
        actions = [
            "Photograph affected and healthy plants for comparison.",
            "Check soil moisture and recent rainfall.",
            "Inspect both sides of leaves and the stem/root area.",
            "Repeat the observation after 24–48 hours if the problem is changing."
        ]
    return {
        "status": "FIRST CHECK",
        "title": title,
        "description": desc,
        "actions": actions,
        "note": "This is a symptom-screening aid, not a confirmed plant-disease diagnosis."
    }

def _num(form, key):
    try:
        value = form.get(key, "").strip()
        return float(value) if value else None
    except (TypeError, ValueError):
        return None

def soil_review(form):
    ph, n, p, k, moisture = [_num(form, x) for x in ("ph","n","p","k","moisture")]
    metrics = []
    if ph is not None:
        status = "Acidic" if ph < 6 else "Near neutral" if ph <= 7.5 else "Alkaline"
        metrics.append({"label":"pH","value":ph,"status":status})
    if n is not None: metrics.append({"label":"Nitrogen","value":n,"status":"Record"})
    if p is not None: metrics.append({"label":"Phosphorus","value":p,"status":"Record"})
    if k is not None: metrics.append({"label":"Potassium","value":k,"status":"Record"})
    if moisture is not None:
        metrics.append({"label":"Moisture","value":f"{moisture}%","status":"Field reading"})
    actions = [
        "Use the same units and test method when comparing readings over time.",
        "For fertilizer decisions, prefer a laboratory soil test or locally calibrated recommendation.",
        "Combine soil information with crop, growth stage, previous crop and irrigation method."
    ]
    title = "Soil readings recorded"
    summary = "The values can now be used as a baseline for field records."
    if ph is not None and ph < 5.5:
        title = "Low pH needs attention"
        summary = "The reading is strongly acidic. Confirm with a soil laboratory before making a corrective application."
    elif ph is not None and ph > 8.0:
        title = "High pH needs attention"
        summary = "The reading is alkaline. Confirm with a soil laboratory and check crop suitability."
    return {"metrics":metrics,"title":title,"summary":summary,"actions":actions}

def fertilizer_plan(form):
    crop = form.get("crop","")
    stage = form.get("stage","")
    test = form.get("test","no")
    concern = form.get("concern","")
    actions = []
    if test == "yes":
        actions.append("Use the soil-test recommendation as the starting point instead of a generic dose.")
    else:
        actions.append("Arrange a soil test before making a large fertilizer application.")
    actions.append(f"Match nutrient timing to {crop}'s {stage.lower()} stage and local agronomic guidance.")
    if "nitrogen" in concern.lower():
        actions.append("Check leaf colour, crop growth and the soil-test nitrogen result before adding nitrogen.")
    elif "phosphorus" in concern.lower():
        actions.append("Confirm phosphorus status with a soil test; avoid repeated application without evidence of need.")
    elif "potassium" in concern.lower():
        actions.append("Check potassium status and crop demand before application.")
    else:
        actions.append("Record the product, dose, date and field area after every application.")
    return {
        "title": f"{crop} nutrient planning",
        "summary": f"Stage: {stage}. Main concern: {concern}.",
        "actions": actions,
        "note": "No fixed fertilizer quantity is generated because a safe dose depends on soil test, crop requirement, yield target and local recommendations."
    }

def pest_review(form):
    symptom = form.get("symptom","")
    mapping = {
        "holes": ("Chewing damage", ["Inspect leaves for larvae, beetles and fresh feeding edges.", "Check weeds and nearby plants for the same insect.", "Estimate the affected area before selecting a control."]),
        "curling": ("Leaf distortion", ["Inspect young leaves and growing points for sucking insects.", "Check both sides of leaves.", "Confirm the cause before treatment."]),
        "sticky": ("Honeydew-type symptom", ["Look for aphids, whiteflies, mealybugs or other sap-feeding insects.", "Check for black sooty growth on leaves.", "Record pest presence before treatment."]),
        "wilting": ("Wilting requires diagnosis", ["Check soil moisture and root condition.", "Look for stem injury and patch patterns.", "Do not assume an insect cause from wilting alone."]),
        "spots": ("Leaf spotting", ["Check whether spots are expanding and whether the underside has growth.", "Compare with healthy leaves.", "Consider disease, nutrient and spray injury as different possibilities."]),
        "insects": ("Visible insect activity", ["Photograph the insect if possible.", "Check location on the plant and feeding type.", "Identify the pest before choosing a pesticide."])
    }
    title, actions = mapping.get(symptom, ("Field inspection", ["Inspect several plants and record the pattern."]))
    return {
        "title": title,
        "summary": "The symptom is a starting point for inspection, not proof of one pest.",
        "actions": actions,
        "note": "Follow the product label and local agricultural recommendations for any pesticide decision."
    }

def farm_tasks():
    return [
        {"day":"Today","task":"Check soil moisture","detail":"Inspect the root zone before starting irrigation."},
        {"day":"Today","task":"Inspect crop leaves","detail":"Look at healthy and affected plants from different parts of the field."},
        {"day":"Tomorrow","task":"Review rainfall","detail":"Adjust irrigation planning if meaningful rain is forecast."},
        {"day":"Within 3 days","task":"Review nutrient needs","detail":"Use a soil test and crop stage before fertilizer application."},
        {"day":"This week","task":"Record field activity","detail":"Save irrigation, fertilizer and crop-health observations."},
        {"day":"Weekly","task":"Walk the field","detail":"Look for new pest, disease, waterlogging or nutrient symptoms."}
    ]
