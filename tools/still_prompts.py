#!/usr/bin/env python3
"""Build reproducible nano_banana_pro prompts for Stage 4 stills from cards.json + passports.
Usage: python3 tools/still_prompts.py c01 c02 ...  (prints JSON list of {id, prompt, refs})"""
import json, sys, re
STYLE = ("Photorealistic cinematic still, vertical 9:16, natural light, shallow depth of field, "
         "35mm look, muted warm palette, no text, no logos, no watermark, no captions.")
HERO = ("Heroine Oksana, 51, Ukrainian woman, dark-blond honey hair in a low ponytail, cream silk blouse, "
        "grey-beige silk scarf, oatmeal cardigan; same face as reference image.")
EXTRAS = {
    "колег": "Colleague Alina, 32, dark hair, office blouse; same face as second reference.",
    "Марта": "Marta, 55, short grey hair, glasses, green sweater; same face as second reference.",
    "Соня": "Daughter Sonia, 25; same face as second reference.",
}
REFS = {"hero": "c852d36e-7c52-41fc-a8ab-16b2a60c8fc9", "product": "b41b8270-3124-41e6-b2a3-c450d41a0879",
        "colleague": "04a929c6-db32-442a-8c76-887beae312a8", "marta": "e5b1215e-4ebe-4e5b-bd35-f14966b54ffd",
        "daughter": "42d8e467-b8e6-4c6b-b76a-7af141f87e9a"}
ACT_LOOK = {1: "Act I look: slightly desaturated, cool-neutral grade.",
            2: "Act II look: neutral daylight grade.",
            3: "Act III look: warm, saturated, golden light."}
def act(c):
    b = int(c["beat"][1:]); return 1 if b <= 5 else (2 if b <= 8 else 3)
def build(c):
    parts = [STYLE, ACT_LOOK[act(c)]]
    refs = []
    if c["world"] == "hero":
        parts.append(HERO); refs.append(("hero", REFS["hero"]))
        for k, v in EXTRAS.items():
            if k in c["shot_desc"]:
                parts.append(v); refs.append(({"колег": "colleague", "Марта": "marta", "Соня": "daughter"}[k], REFS[{"колег": "colleague", "Марта": "marta", "Соня": "daughter"}[k]]))
        if c.get("product_visible"):
            parts.append("Product: matte lavender frosted-glass jar with brushed silver lid exactly as in the product reference image."); refs.append(("product", REFS["product"]))
    else:
        parts.append("Cutaway insert, no people's faces, no product, no brand.")
    if c.get("enemy_in_frame") and "банк" in c["shot_desc"]:
        parts.append("Any competitor jar is plain white, unlabeled, blurred label.")
    parts.append("Scene (Ukrainian brief): " + c["shot_desc"])
    return {"id": c["id"], "prompt": " ".join(parts), "refs": refs,
            "model": "nano_banana_pro", "aspect_ratio": "9:16", "resolution": "1k"}
if __name__ == "__main__":
    cards = {c["id"]: c for c in json.load(open("work/stage3/cards.json"))}
    ids = sys.argv[1:] or list(cards)
    print(json.dumps([build(cards[i]) for i in ids], ensure_ascii=False, indent=1))
