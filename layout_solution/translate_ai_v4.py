#!/usr/bin/env python3
"""
Stage 2 V4: AI Translation with Professional Layout Selection
Simplified 3-layout system for government presentations.
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv


def load_glossary(glossary_path: str = "glossary.json") -> Dict:
    """Load the translation glossary."""
    glossary_path = Path(glossary_path)
    if not glossary_path.exists():
        return {}

    with open(glossary_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_glossary_text(glossary: Dict) -> str:
    """Convert glossary dict to formatted text for prompt."""
    if not glossary:
        return ""

    parts = ["OFFICIAL TRANSLATION GLOSSARY (use these exact translations):"]

    if "organizations" in glossary:
        parts.append("\nOrganizations:")
        for en, fr in glossary["organizations"].items():
            parts.append(f"  • {en} → {fr}")

    if "programs" in glossary:
        parts.append("\nPrograms:")
        for en, fr in glossary["programs"].items():
            parts.append(f"  • {en} → {fr}")

    if "terms" in glossary:
        parts.append("\nKey Terms:")
        for en, fr in glossary["terms"].items():
            parts.append(f"  • {en} → {fr}")

    return "\n".join(parts)


def build_table_prompt_v4(slide_data: Dict, glossary: Dict) -> str:
    """Build prompt for TABLE slides - choose between cards or table."""
    glossary_text = build_glossary_text(glossary)
    tables_json = json.dumps(slide_data['tables'], indent=2, ensure_ascii=False)

    prompt = f"""You are a professional data presentation expert for government reports.

{glossary_text}

TASK: Analyze this data and choose the BEST professional layout.

LAYOUT OPTIONS (choose ONE):

A) "clean_cards" - Use when:
   • 4-8 key statistics that are the main insight
   • Numbers deserve visual emphasis
   • Data is simple (not deeply relational)

B) "styled_table" - Use when:
   • More than 8 data points
   • Data is relational (rows compare to each other)
   • Detail and precision matter

INPUT TABLES:
{tables_json}

SLIDE TITLE: {slide_data['title']}
CONTEXT: {slide_data['content'][:250]}

OUTPUT JSON:

If you choose "clean_cards":
{{
  "french_title": "Short title (8-10 words max)",
  "summary_one_liner": "One sentence summary",
  "layout_type": "clean_cards",
  "cards": [
    {{
      "number": "38%",
      "label": "Victimes de harcèlement",
      "sublabel": "dans les 12 derniers mois"
    }}
  ]
}}

If you choose "styled_table":
{{
  "french_title": "Short title (8-10 words max)",
  "summary_one_liner": "One sentence summary",
  "layout_type": "styled_table",
  "translated_tables": [
    {{
      "headers": ["French header 1", "French header 2"],
      "rows": [["French label", "36%"]]
    }}
  ]
}}

Remember: Choose the layout that best serves GOVERNMENT PROFESSIONALS reading policy data."""

    return prompt


def build_text_prompt_v4(slide_data: Dict, glossary: Dict, previous_french: Optional[Dict] = None) -> str:
    """Build prompt for TEXT slides."""
    glossary_text = build_glossary_text(glossary)

    if previous_french is None:
        prompt = f"""You are a professional translator for government documents.

{glossary_text}

TASK: Translate this slide naturally into French.

INSTRUCTIONS:
- Preserve number of bullet points (1:1 mapping)
- Translate clearly and concisely
- Use formal French (vouvoiement)
- Keep original structure and meaning

INPUT:
Title: {slide_data['title']}
Content: {slide_data['content']}

OUTPUT (JSON only):
{{
  "french_title": "...",
  "summary_one_liner": "...",
  "french_points": ["point 1", "point 2", ...],
  "layout_type": "text_bullets"
}}

Note: Extract numbered findings as separate bullets."""
    else:
        prompt = f"""Continue translating. Use same terminology as previous slide.

{glossary_text}

PREVIOUS: {previous_french.get('french_title', 'N/A')}

INPUT:
Title: {slide_data['title']}
Content: {slide_data['content']}

OUTPUT (JSON only):
{{
  "french_title": "...",
  "summary_one_liner": "...",
  "french_points": ["...", "..."],
  "layout_type": "text_bullets"
}}"""

    return prompt


def build_section_header_prompt(slide_data: Dict, glossary: Dict) -> str:
    """Build prompt for SECTION HEADER slides."""
    glossary_text = build_glossary_text(glossary)

    prompt = f"""Translate this section header to French.

{glossary_text}

INPUT: {slide_data['title']}
CONTEXT: {slide_data['content'][:200]}

OUTPUT (JSON only):
{{
  "french_title": "Brief title",
  "summary_one_liner": "One sentence (15-20 words) describing this section",
  "layout_type": "section_header"
}}"""

    return prompt


def call_gemini_api(prompt: str, api_key: str) -> Dict:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Google Generative AI library not installed.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
        generation_config={'temperature': 0.3}
    )

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean JSON extraction
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]

    return json.loads(text.strip())


def translate_slide_v4(slide_data: Dict, glossary: Dict, api_key: str, previous_french: Optional[Dict] = None) -> Dict:
    """Translate a slide with V4 layout decision."""
    slide_type = slide_data.get('type', 'text')

    # Build prompt based on type
    if slide_type == 'table':
        prompt = build_table_prompt_v4(slide_data, glossary)
    elif slide_type == 'section_header':
        prompt = build_section_header_prompt(slide_data, glossary)
    else:
        prompt = build_text_prompt_v4(slide_data, glossary, previous_french)

    # Call API
    french_content = call_gemini_api(prompt, api_key)

    # Build result
    translated_slide = {
        "id": slide_data["id"],
        "type": slide_type,
        "original_title": slide_data["title"],
        "original_content": slide_data["content"],
        "french_title": french_content["french_title"],
        "summary_one_liner": french_content.get("summary_one_liner", ""),
        "layout_type": french_content.get("layout_type", slide_type),
        "original_img": slide_data["original_img"]
    }

    # Add layout-specific content
    layout = french_content.get("layout_type", "text_bullets")

    if layout == "clean_cards":
        translated_slide["cards"] = french_content.get("cards", [])
        translated_slide["translated_tables"] = []
        translated_slide["french_points"] = []
    elif layout == "styled_table":
        translated_slide["translated_tables"] = french_content.get("translated_tables", [])
        translated_slide["cards"] = []
        translated_slide["french_points"] = []
    elif layout == "text_bullets":
        translated_slide["french_points"] = french_content.get("french_points", [])
        translated_slide["cards"] = []
        translated_slide["translated_tables"] = []
    else:  # section_header
        translated_slide["french_points"] = []
        translated_slide["cards"] = []
        translated_slide["translated_tables"] = []

    return translated_slide


def translate_slides_v4(slides_data: List[Dict], glossary: Dict, api_key: str) -> List[Dict]:
    """Translate all slides with V4 system."""
    translated_slides = []
    previous_french = None

    for idx, slide in enumerate(slides_data, start=1):
        slide_type = slide.get('type', 'text')
        type_icon = {"table": "📊", "text": "📝", "section_header": "📌"}.get(slide_type, "❓")

        print(f"🔄 Slide {idx}/10 {type_icon} [{slide_type}]: {slide['title'][:40]}...")

        try:
            translated_slide = translate_slide_v4(slide, glossary, api_key, previous_french)
            translated_slides.append(translated_slide)

            if slide_type == 'text':
                previous_french = translated_slide

            layout = translated_slide.get('layout_type', slide_type)
            print(f"  ✅ {translated_slide['french_title'][:50]}... [Layout: {layout}]")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            translated_slides.append({
                "id": slide["id"],
                "type": slide_type,
                "error": str(e),
                "original_title": slide["title"]
            })

    return translated_slides


def main():
    """Main entry point."""
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    print("🤖 V4: Professional Layout System (3 Layouts)")
    print("   📋 Styled Table | 🎯 Clean Cards | 📝 Text Bullets\n")

    input_path = Path("output/extracted_slides_v2.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} slides\n")

    glossary = load_glossary()
    translated_slides = translate_slides_v4(slides_data, glossary, api_key)

    output_path = Path("output/translated_slides_v4.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(translated_slides, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved to: {output_path}")

    # Summary
    layout_counts = {}
    for slide in translated_slides:
        if "error" not in slide:
            layout = slide.get('layout_type', 'unknown')
            layout_counts[layout] = layout_counts.get(layout, 0) + 1

    print(f"\n📊 Layout Decisions:")
    for layout, count in sorted(layout_counts.items()):
        icon = {"text_bullets": "📝", "styled_table": "📋", "clean_cards": "🎯", "section_header": "📌"}.get(layout, "❓")
        print(f"  {icon} {layout}: {count}")


if __name__ == "__main__":
    main()
