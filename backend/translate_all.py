#!/usr/bin/env python3
"""Translate ALL 880 scenarios using free Google Translate."""
import json
import time
from deep_translator import GoogleTranslator

def translate_text(text, target_lang):
    """Translate a single text string."""
    if not text or not text.strip():
        return text
    try:
        result = GoogleTranslator(source='en', target=target_lang).translate(text)
        return result or text
    except Exception as e:
        print(f"    Error translating: {e}")
        return text

def translate_scenario(scenario, target_lang):
    """Translate all fields of a scenario."""
    translated = dict(scenario)
    translated["question"] = translate_text(scenario["question"], target_lang)
    translated["short_answer"] = translate_text(scenario["short_answer"], target_lang)
    translated["explanation"] = translate_text(scenario["explanation"], target_lang)
    translated["script"] = translate_text(scenario.get("script", ""), target_lang)
    
    # Translate next_steps list
    next_steps = scenario.get("next_steps", [])
    translated["next_steps"] = [translate_text(step, target_lang) for step in next_steps]
    
    return translated

def translate_all(target_lang, lang_name):
    """Translate entire data.json to target language."""
    with open('data.json') as f:
        data = json.load(f)
    
    # Translate categories and subcategories
    for cat in data["categories"]:
        cat["name"] = translate_text(cat["name"], target_lang)
        cat["description"] = translate_text(cat.get("description", ""), target_lang)
        for sub in cat.get("subcategories", []):
            sub["name"] = translate_text(sub["name"], target_lang)
    
    # Translate all scenarios
    total = 0
    for cat_id, subcats in data["scenarios"].items():
        for sub_id, scenarios in subcats.items():
            print(f"  [{cat_id}/{sub_id}] {len(scenarios)} scenarios...")
            for i, s in enumerate(scenarios):
                scenarios[i] = translate_scenario(s, target_lang)
                total += 1
                # Rate limit to avoid blocking
                if total % 50 == 0:
                    print(f"    ...{total} done")
                    time.sleep(2)
    
    # Save
    output_file = f'data_{target_lang}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ {output_file} saved ({total} scenarios translated to {lang_name})")

if __name__ == "__main__":
    languages = [
        ("es", "Spanish"),
        ("fr", "French"),
        ("zh-CN", "Mandarin Chinese"),
    ]
    
    for lang_code, lang_name in languages:
        # Use short code for filename
        file_code = lang_code.split("-")[0]  # "zh-CN" -> "zh"
        output_file = f'data_{file_code}.json'
        
        import os
        if os.path.exists(output_file):
            print(f"\n{output_file} exists, skipping (delete to re-translate)")
            continue
        
        print(f"\n{'='*50}")
        print(f"Translating to {lang_name}...")
        print(f"{'='*50}")
        translate_all(lang_code, lang_name)
