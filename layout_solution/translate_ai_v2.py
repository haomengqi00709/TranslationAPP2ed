#!/usr/bin/env python3
"""
Stage 2 V2: AI-Powered Translation with Content-Aware Routing
Handles text slides, table slides, and section headers differently.
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


def build_text_prompt(slide_data: Dict, glossary: Dict, previous_french: Optional[Dict] = None) -> str:
    """Build prompt for TEXT slides - natural translation with point-for-point mapping."""
    glossary_text = build_glossary_text(glossary)

    if previous_french is None:
        prompt = f"""You are a professional translator for government documents. Translate this slide into French naturally.

{glossary_text}

INSTRUCTIONS:
- Preserve the number of bullet points from the original (each point → each point)
- Translate each point clearly and concisely in natural French
- Use formal French (vouvoiement)
- Keep the meaning and structure of each original point
- Don't add or remove points - maintain 1:1 correspondence

INPUT:
Title: {slide_data['title']}
Content: {slide_data['content']}

OUTPUT (JSON only):
{{
  "french_title": "...",
  "summary_one_liner": "...",
  "french_points": ["point 1 in French", "point 2 in French", ...]
}}

Note: If the content describes numbered findings or key points (e.g., "1. First point, 2. Second point"), extract each one as a separate bullet."""
    else:
        prompt = f"""Continue translating. Use same style and terminology as previous slide.

{glossary_text}

PREVIOUS SLIDE REFERENCE:
{previous_french.get('french_title', 'N/A')}

INSTRUCTIONS:
- Preserve the number of bullet points from the original
- Translate naturally and clearly
- Maintain 1:1 correspondence with original points

INPUT:
Title: {slide_data['title']}
Content: {slide_data['content']}

OUTPUT (JSON only):
{{
  "french_title": "...",
  "summary_one_liner": "...",
  "french_points": ["...", "...", "..."]
}}"""

    return prompt


def build_table_prompt(slide_data: Dict, glossary: Dict) -> str:
    """Build prompt for TABLE slides - translate labels but preserve data."""
    glossary_text = build_glossary_text(glossary)

    tables_json = json.dumps(slide_data['tables'], indent=2, ensure_ascii=False)

    prompt = f"""You are a professional translator for government data tables. Translate table headers and labels to French, but PRESERVE all numerical data exactly.

{glossary_text}

CRITICAL RULES:
- Translate column headers
- Translate row labels (first column text)
- DO NOT change any numbers, percentages, or data values
- Maintain exact table structure
- Use formal French
- TITLE MUST BE SHORT: Maximum 8-10 words, like a PPT slide title (not a sentence!)

INPUT TABLES:
{tables_json}

SLIDE TITLE: {slide_data['title']}
SLIDE DESCRIPTION: {slide_data['content'][:200]}

OUTPUT (JSON only):
{{
  "french_title": "Short, punchy title (8-10 words MAX)",
  "summary_one_liner": "One sentence describing the data shown",
  "translated_tables": [
    {{
      "headers": ["French header 1", "French header 2"],
      "rows": [
        ["French label", "36%"],
        ["French label", "19%"]
      ]
    }}
  ]
}}

Example:
BAD title: "Les demandes de mesures d'adaptation liées à un handicap sont principalement faites pour éliminer les obstacles..."
GOOD title: "Types de handicaps : demandes de mesures d'adaptation"

Remember: Translate text, preserve numbers, KEEP TITLES SHORT!"""

    return prompt


def build_section_header_prompt(slide_data: Dict, glossary: Dict) -> str:
    """Build prompt for SECTION HEADER slides - translate and add context."""
    glossary_text = build_glossary_text(glossary)

    prompt = f"""Translate this section header to French and add a brief description.

{glossary_text}

INPUT TITLE: {slide_data['title']}
CONTEXT: {slide_data['content'][:200]}

OUTPUT (JSON only):
{{
  "french_title": "Brief French title",
  "summary_one_liner": "One sentence (15-20 words) describing what this section covers"
}}

Example:
If title is "Pre-request phase", summary could be: "Cette section explore les pensées et préoccupations des employés avant de faire une demande de mesures d'adaptation."
"""

    return prompt


def call_gemini_api(prompt: str, api_key: str) -> Dict:
    """Call Google Gemini API for translation."""
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

    # Extract JSON from response
    text = response.text.strip()
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]

    return json.loads(text.strip())


def translate_slide(slide_data: Dict, glossary: Dict, api_key: str, previous_french: Optional[Dict] = None) -> Dict:
    """
    Translate a single slide based on its type.

    Returns translated slide data.
    """
    slide_type = slide_data.get('type', 'text')

    # Build appropriate prompt based on type
    if slide_type == 'table':
        prompt = build_table_prompt(slide_data, glossary)
    elif slide_type == 'section_header':
        prompt = build_section_header_prompt(slide_data, glossary)
    else:  # text
        prompt = build_text_prompt(slide_data, glossary, previous_french)

    # Call API
    french_content = call_gemini_api(prompt, api_key)

    # Build translated slide
    translated_slide = {
        "id": slide_data["id"],
        "type": slide_type,
        "original_title": slide_data["title"],
        "original_content": slide_data["content"],
        "french_title": french_content["french_title"],
        "summary_one_liner": french_content.get("summary_one_liner", ""),
        "original_img": slide_data["original_img"]
    }

    # Add type-specific content
    if slide_type == 'table':
        translated_slide["translated_tables"] = french_content.get("translated_tables", [])
        translated_slide["french_points"] = []  # Tables don't have bullets
    elif slide_type == 'section_header':
        translated_slide["french_points"] = []  # Section headers don't have bullets
        translated_slide["translated_tables"] = []
    else:  # text
        translated_slide["french_points"] = french_content.get("french_points", [])
        translated_slide["translated_tables"] = []

    return translated_slide


def translate_slides(slides_data: List[Dict], glossary: Dict, api_key: str) -> List[Dict]:
    """Translate all slides using content-aware routing."""
    translated_slides = []
    previous_french = None

    for idx, slide in enumerate(slides_data, start=1):
        slide_type = slide.get('type', 'text')
        type_icon = {"table": "📊", "text": "📝", "section_header": "📌"}.get(slide_type, "❓")

        print(f"🔄 Slide {idx}/10 {type_icon} [{slide_type}]: {slide['title'][:40]}...")

        try:
            translated_slide = translate_slide(slide, glossary, api_key, previous_french)
            translated_slides.append(translated_slide)

            # Update context (only for text slides)
            if slide_type == 'text':
                previous_french = translated_slide

            print(f"  ✅ {translated_slide['french_title'][:50]}...")

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

    print("🤖 Using Google Gemini API (gemini-flash-latest)")

    # Load extracted slides (V2 format with tables)
    input_path = Path("output/extracted_slides_v2.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found. Run extract_ppt_v2.py first.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} slides")

    # Load glossary
    glossary = load_glossary()
    print(f"📚 Loaded glossary\n")

    # Translate slides
    translated_slides = translate_slides(slides_data, glossary, api_key)

    # Save results
    output_path = Path("output/translated_slides_v2.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(translated_slides, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved to: {output_path}")

    # Summary
    print(f"\n📊 Summary:")
    type_counts = {}
    for slide in translated_slides:
        if "error" not in slide:
            slide_type = slide['type']
            type_counts[slide_type] = type_counts.get(slide_type, 0) + 1

    print(f"  ✅ Text slides: {type_counts.get('text', 0)}")
    print(f"  ✅ Table slides: {type_counts.get('table', 0)}")
    print(f"  ✅ Section headers: {type_counts.get('section_header', 0)}")


if __name__ == "__main__":
    main()
