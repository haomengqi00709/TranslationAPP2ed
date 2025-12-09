#!/usr/bin/env python3
"""
Stage 2 V5: AI Content Restructuring (NotebookLLM-style)
Analyzes content and creates optimal presentation layouts, may split/merge slides.
Includes multimodal vision analysis for chart slides.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from analyze_charts_vision import analyze_chart_image, build_chart_analysis_prompt
from PIL import Image
import time


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


def build_analysis_prompt(slide_data: Dict, glossary: Dict) -> str:
    """Phase 1: Analyze content and decide structure."""
    glossary_text = build_glossary_text(glossary)

    # Extract full content for analysis
    full_content = f"{slide_data['title']}\n\n{slide_data['content']}"

    prompt = f"""You are a professional presentation designer analyzing government survey content.

{glossary_text}

TASK: Analyze this slide and decide optimal presentation structure.

ORIGINAL CONTENT:
{full_content}

ANALYSIS FRAMEWORK:

1. Content Density:
   - Word count: {len(slide_data['content'].split())} words
   - Is this: concise (<100 words) / moderate (100-200) / dense (>200)?

2. Content Type:
   - Data-heavy (multiple statistics/numbers)?
   - Process/methodology explanation?
   - Findings/insights?
   - Section divider?

3. Extractable Data:
   - List any key numbers/statistics with their context
   - Example: "980 total responses", "93% related to handicap"

4. Distinct Topics:
   - How many separate ideas/topics are covered?
   - Can they be logically separated?

DECISION RULES:

→ OUTPUT 1 SLIDE when:
  - Content is already concise
  - Single clear topic
  - Already well-structured

→ OUTPUT 2-3 SLIDES when:
  - Dense (>200 words) with multiple topics
  - Mix of statistics + narrative context
  - Methodology sections (often have: purpose + process + constraints)

LAYOUT OPTIONS:
- "section_header": Big title + one sentence (for dividers)
- "clean_cards": 2-4 key statistics with visual emphasis (MAX 4 CARDS - displays in single horizontal row)
- "styled_table": Relational data (rows compare to each other) - USE THIS for 5+ data points instead of clean_cards
- "text_bullets": Narrative content, 3-5 concise bullets
- "chart_image": Data visualization/chart detected - will be analyzed separately with multimodal AI
- "quote": **RARE** - Only for THE single most important insight/conclusion (use sparingly, max 1-2 per entire document)

OUTPUT (JSON only):
{{
  "analysis": {{
    "density": "dense|moderate|concise",
    "content_type": "data-heavy|process|findings|section-divider",
    "word_count": {len(slide_data['content'].split())},
    "key_statistics": [
      {{"number": "980", "label": "total responses", "context": "..."}}
    ],
    "distinct_topics": ["topic 1", "topic 2"]
  }},
  "decision": {{
    "output_count": 1,
    "slides": [
      {{
        "sequence": 1,
        "layout_type": "clean_cards|text_bullets|styled_table|section_header",
        "content_focus": "Brief description of what this slide should contain",
        "rationale": "Why this layout?"
      }}
    ]
  }}
}}

Be smart: Don't split unnecessarily. Only split when it genuinely improves clarity."""

    return prompt


def build_generation_prompt(
    slide_data: Dict,
    glossary: Dict,
    layout_decision: Dict,
    slide_sequence: int
) -> str:
    """Phase 2: Generate content for a specific decided slide."""
    glossary_text = build_glossary_text(glossary)

    layout_type = layout_decision['layout_type']
    content_focus = layout_decision['content_focus']

    full_content = f"{slide_data['title']}\n\n{slide_data['content']}"

    # Build layout-specific instructions
    if layout_type == "clean_cards":
        layout_template = """
{{
  "french_title": "Short title (8-10 words max)",
  "summary_one_liner": "One sentence context",
  "layout_type": "clean_cards",
  "cards": [
    {{
      "number": "980",
      "label": "Réponses totales",
      "sublabel": "Sondage de suivi"
    }}
  ]
}}

REQUIREMENTS:
- Extract 2-4 key numbers from content (MAX 4 CARDS - they display in single horizontal row)
- If you have 5+ data points, use "styled_table" layout instead
- Each card: number + clear French label + optional sublabel
- Focus on: {content_focus}
- Use *emphasis* in labels for key terms if needed (e.g., "Réponses *d'employés*")
"""
    elif layout_type == "styled_table":
        layout_template = """
{{
  "french_title": "Short title (8-10 words max)",
  "summary_one_liner": "One sentence context",
  "layout_type": "styled_table",
  "translated_tables": [
    {{
      "headers": ["French header 1", "French header 2"],
      "rows": [["Row 1 data", "36%"]]
    }}
  ]
}}

REQUIREMENTS:
- Structure data as table
- Translate headers and cells to French
- Focus on: {content_focus}
"""
    elif layout_type == "section_header":
        layout_template = """
{{
  "french_title": "Section title (brief)",
  "summary_one_liner": "One sentence (15-20 words) describing this section",
  "layout_type": "section_header"
}}

REQUIREMENTS:
- Bold, clear section title
- One-liner captures essence
- Focus on: {content_focus}
"""
    elif layout_type == "quote":
        layout_template = """
{{
  "french_title": "Brief context title (5-8 words)",
  "quote_text": "THE single most powerful insight from this slide (one sentence, 15-25 words max)",
  "layout_type": "quote"
}}

REQUIREMENTS:
- Extract THE ONE most important/surprising/actionable finding
- Must be genuinely powerful - not just a bullet point
- This will be displayed LARGE and CENTERED with dramatic typography
- If no truly powerful insight exists, DO NOT use this layout
- Focus on: {content_focus}
"""
    elif layout_type == "chart_image":
        layout_template = """
{{
  "french_title": "Brief descriptive title (8-10 words max)",
  "summary_one_liner": "One sentence explaining what the chart shows",
  "layout_type": "chart_image",
  "chart_caption": "Detailed French caption explaining the key insight from the chart (20-30 words)"
}}

REQUIREMENTS:
- Translate title to French
- Summary explains WHAT the chart visualizes
- Caption explains the KEY INSIGHT or FINDING from the data
- Focus on: {content_focus}
- NOTE: The chart image will be displayed, this text provides context
"""
    else:  # text_bullets
        layout_template = """
{{
  "french_title": "Clear title (8-10 words max)",
  "summary_one_liner": "One sentence summary",
  "layout_type": "text_bullets",
  "french_points": [
    "Concise bullet 1 (15-20 words max)",
    "Concise bullet 2",
    "Concise bullet 3"
  ]
}}

REQUIREMENTS:
- 3-5 concise bullets
- Each bullet: one clear idea, 15-20 words max
- Natural French, formal tone (vouvoiement)
- Focus on: {content_focus}

EMPHASIS GUIDELINES (use markdown formatting):
- Use *single asterisks* for key terms, roles, concepts (rendered as italic, blue)
  Example: "L'expérience des *employés* et des *superviseurs*"

- Use **double asterisks** for critical findings, statistics, important numbers (rendered as bold, dark)
  Example: "**93% des demandes** concernent un handicap"

- Use ***triple asterisks*** RARELY for THE most critical insight (rendered as bold+italic+highlighted)
  Example: "Cette recherche révèle un ***écart critique*** dans le processus"

Apply emphasis to 2-4 words per bullet to guide reader's attention to what matters most.
"""

    prompt = f"""You are translating and restructuring government content into French.

{glossary_text}

ORIGINAL CONTENT:
{full_content}

YOUR TASK:
Create slide {slide_sequence} focusing on: {content_focus}

Layout type: {layout_type}

EXTRACT AND TRANSLATE:
- Only include content relevant to the focus area
- Translate naturally to French (formal government style)
- Condense for clarity (this is slide {slide_sequence} of a split)

OUTPUT (JSON only):
{layout_template}

Remember: This slide should contain ONLY the "{content_focus}" part, not everything."""

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


def translate_chart_content(title: str, chart_data: Dict, glossary: Dict, api_key: str) -> Dict:
    """Translate chart title and labels to French."""
    glossary_text = build_glossary_text(glossary)

    prompt = f"""Translate this chart content from English to French.

GLOSSARY (use these exact translations):
{glossary_text}

CHART DATA:
Title: {title}
Labels: {json.dumps(chart_data.get('labels', chart_data.get('title', '')))}

Translate to French. Return JSON only:
{{
  "french_title": "...",
  "french_labels": ["...", "..."]  // Only if labels exist
}}"""

    response = call_gemini_api(prompt, api_key)
    return response


def translate_table_data(table: Dict, glossary: Dict, api_key: str) -> Dict:
    """Translate table headers and rows from English to French."""
    glossary_text = build_glossary_text(glossary)

    prompt = f"""Translate this table data from English to French.

GLOSSARY (use these exact translations):
{glossary_text}

TABLE DATA:
Headers: {json.dumps(table.get('headers', []))}
Rows: {json.dumps(table.get('rows', []))}

TRANSLATION RULES:
- Translate all headers to French
- Translate all text cells to French
- Keep numeric values (percentages, numbers) unchanged
- Maintain table structure exactly

Return JSON only:
{{
  "headers": ["...", "..."],  // Translated headers
  "rows": [["...", "..."], ...]  // Translated rows
}}"""

    response = call_gemini_api(prompt, api_key)
    return response


def restructure_chart_slide_v5(slide_data: Dict, glossary: Dict, api_key: str, image_dir: Path) -> Dict:
    """
    V5 Chart Restructuring: Use vision AI to analyze chart and extract data.
    """
    slide_id = slide_data['id']
    print(f"\n📈 Chart Slide Detected: {slide_data['title'][:50]}...")

    # Get slide image path
    image_path = image_dir / f"slide{slide_id}.png"

    if not image_path.exists():
        print(f"   ⚠️  Image not found: {image_path.name}, falling back to text analysis")
        return restructure_slide_v5(slide_data, glossary, api_key, image_dir)

    # Get chart metadata
    charts = slide_data.get('charts', [])
    if not charts:
        print(f"   ⚠️  No chart metadata found, falling back to text analysis")
        return restructure_slide_v5(slide_data, glossary, api_key, image_dir)

    chart_info = charts[0]  # Use first chart for now

    # Analyze chart with vision AI
    print(f"   🔍 Vision analysis...")
    try:
        analysis = analyze_chart_image(str(image_path), chart_info, api_key)

        layout_decision = analysis.get('layout_decision', 'chart_image')
        print(f"   ✅ Decision: {layout_decision}")

        # Translate chart content to French
        print(f"   🌐 Translating to French...")
        translation = translate_chart_content(
            slide_data['title'],
            analysis.get('chart_data', {}),
            glossary,
            api_key
        )

        # Build output slide based on vision analysis
        output_slide = {
            "id": str(slide_id),
            "source_id": slide_id,
            "original_title": slide_data['title'],
            "type": slide_data.get('type', 'chart'),
            "french_title": translation.get('french_title', slide_data['title']),
            "summary_one_liner": "",
            "layout_type": layout_decision,
            "original_img": slide_data.get('original_img', ''),
            "charts": charts
        }

        # Add layout-specific data from vision analysis
        if layout_decision in ['bar_chart', 'column_chart', 'line_chart', 'pie_chart']:
            chart_data = analysis.get('chart_data', {}).copy()
            # Translate chart labels to French
            if translation.get('french_labels'):
                chart_data['labels'] = translation['french_labels']
            # Translate chart title to French
            if translation.get('french_title'):
                chart_data['title'] = translation['french_title']
            output_slide['chart_data'] = chart_data
            output_slide['french_points'] = []
            output_slide['cards'] = []
            output_slide['translated_tables'] = []
        elif layout_decision == 'clean_cards':
            output_slide['cards'] = analysis.get('cards', [])
            output_slide['french_points'] = []
            output_slide['translated_tables'] = []
        elif layout_decision == 'styled_table':
            # Translate table data to French
            english_table = analysis.get('table', {})
            if english_table and (english_table.get('headers') or english_table.get('rows')):
                translated_table = translate_table_data(english_table, glossary, api_key)
                output_slide['translated_tables'] = [translated_table]
            else:
                output_slide['translated_tables'] = [english_table]
            output_slide['cards'] = []
            output_slide['french_points'] = []
        else:  # chart_image fallback
            output_slide['chart_caption'] = analysis.get('caption', '')
            output_slide['french_points'] = []
            output_slide['cards'] = []
            output_slide['translated_tables'] = []

        # Rate limiting to avoid Gemini API limits (10 requests/minute)
        time.sleep(6)

        return {
            "source_slide_id": slide_id,
            "original_title": slide_data['title'],
            "analysis": {"vision_analyzed": True, "layout_decision": layout_decision},
            "output_slides": [output_slide]
        }

    except Exception as e:
        print(f"   ❌ Vision analysis failed: {e}")
        print(f"   Falling back to text analysis")
        return restructure_slide_v5(slide_data, glossary, api_key, image_dir)


def restructure_slide_v5(slide_data: Dict, glossary: Dict, api_key: str, image_dir: Path = None) -> Dict:
    """
    V5 Restructuring: Analyze content and create optimal slides.
    May produce 1-3 output slides from one source slide.
    """
    print(f"\n🔍 Analyzing: {slide_data['title'][:50]}...")

    # Check if this is a chart slide and we have images
    if slide_data.get('type') == 'chart' and image_dir and slide_data.get('charts'):
        return restructure_chart_slide_v5(slide_data, glossary, api_key, image_dir)

    # Phase 1: Analyze and decide structure
    analysis_prompt = build_analysis_prompt(slide_data, glossary)
    analysis_result = call_gemini_api(analysis_prompt, api_key)

    decision = analysis_result['decision']
    output_count = decision['output_count']

    print(f"   📊 Analysis: {analysis_result['analysis']['content_type']} "
          f"({analysis_result['analysis']['density']})")
    print(f"   ✂️  Decision: Split into {output_count} slide(s)")

    # Phase 2: Generate content for each decided slide
    output_slides = []

    for slide_plan in decision['slides']:
        sequence = slide_plan['sequence']
        layout_type = slide_plan['layout_type']

        print(f"      → Slide {sequence}/{output_count}: {layout_type} "
              f"[{slide_plan['content_focus'][:40]}...]")

        generation_prompt = build_generation_prompt(
            slide_data,
            glossary,
            slide_plan,
            sequence
        )

        generated_content = call_gemini_api(generation_prompt, api_key)

        # Build slide ID (e.g., "2.1", "2.2")
        if output_count == 1:
            slide_id = str(slide_data['id'])
        else:
            slide_id = f"{slide_data['id']}.{sequence}"

        # Build output slide
        output_slide = {
            "id": slide_id,
            "source_id": slide_data['id'],
            "original_title": slide_data['title'],
            "type": slide_data.get('type', 'text'),
            "french_title": generated_content.get('french_title', ''),
            "summary_one_liner": generated_content.get('summary_one_liner', ''),
            "layout_type": generated_content.get('layout_type', layout_type),
            "original_img": slide_data.get('original_img', '')
        }

        # Add layout-specific content
        if layout_type == 'clean_cards':
            output_slide['cards'] = generated_content.get('cards', [])
            output_slide['french_points'] = []
            output_slide['translated_tables'] = []
        elif layout_type == 'styled_table':
            output_slide['translated_tables'] = generated_content.get('translated_tables', [])
            output_slide['cards'] = []
            output_slide['french_points'] = []
        elif layout_type == 'text_bullets':
            output_slide['french_points'] = generated_content.get('french_points', [])
            output_slide['cards'] = []
            output_slide['translated_tables'] = []
        elif layout_type == 'quote':
            output_slide['quote_text'] = generated_content.get('quote_text', '')
            output_slide['french_points'] = []
            output_slide['cards'] = []
            output_slide['translated_tables'] = []
        elif layout_type == 'chart_image':
            output_slide['chart_caption'] = generated_content.get('chart_caption', '')
            output_slide['charts'] = slide_data.get('charts', [])  # Include chart metadata
            output_slide['french_points'] = []
            output_slide['cards'] = []
            output_slide['translated_tables'] = []
        else:  # section_header
            output_slide['french_points'] = []
            output_slide['cards'] = []
            output_slide['translated_tables'] = []

        output_slides.append(output_slide)

        print(f"         ✅ {output_slide['french_title'][:60]}...")

    return {
        "source_slide_id": slide_data['id'],
        "original_title": slide_data['title'],
        "analysis": analysis_result['analysis'],
        "output_slides": output_slides
    }


def restructure_all_slides_v5(slides_data: List[Dict], glossary: Dict, api_key: str, image_dir: Path = None) -> List[Dict]:
    """Process all slides with V5 restructuring (including vision analysis for charts)."""
    all_restructured = []

    # Set image directory if not provided
    if image_dir is None:
        image_dir = Path("output/slides_images")

    for idx, slide in enumerate(slides_data, start=1):
        print(f"\n{'='*70}")
        print(f"📄 SOURCE SLIDE {idx}/{len(slides_data)}")

        try:
            restructured = restructure_slide_v5(slide, glossary, api_key, image_dir)
            all_restructured.append(restructured)

            output_count = len(restructured['output_slides'])
            print(f"   ✅ Generated {output_count} output slide(s)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_restructured.append({
                "source_slide_id": slide['id'],
                "original_title": slide['title'],
                "error": str(e),
                "output_slides": []
            })

    return all_restructured


def flatten_to_slides(restructured_data: List[Dict]) -> List[Dict]:
    """Flatten restructured data into simple slide list for rendering."""
    flattened = []

    for source_slide in restructured_data:
        if 'error' not in source_slide:
            for output_slide in source_slide['output_slides']:
                flattened.append(output_slide)

    return flattened


def main():
    """Main entry point."""
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    print("🚀 V5: AI Content Restructuring (NotebookLLM-style)")
    print("   Analyzes content → Optimal layouts → May split slides\n")

    input_path = Path("output/extracted_slides_v2.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} source slides\n")

    glossary = load_glossary()

    # Restructure all slides
    restructured_data = restructure_all_slides_v5(slides_data, glossary, api_key)

    # Save full restructuring data (with analysis)
    full_output_path = Path("output/restructured_full_v5.json")
    with open(full_output_path, 'w', encoding='utf-8') as f:
        json.dump(restructured_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Full analysis saved to: {full_output_path}")

    # Flatten to simple slide list for rendering
    flattened_slides = flatten_to_slides(restructured_data)

    flattened_output_path = Path("output/translated_slides_v5.json")
    with open(flattened_output_path, 'w', encoding='utf-8') as f:
        json.dump(flattened_slides, f, ensure_ascii=False, indent=2)

    print(f"💾 Flattened slides saved to: {flattened_output_path}")

    # Summary statistics
    source_count = len([s for s in restructured_data if 'error' not in s])
    output_count = len(flattened_slides)

    print(f"\n📊 Summary:")
    print(f"   Source slides: {source_count}")
    print(f"   Output slides: {output_count}")
    print(f"   Expansion ratio: {output_count/source_count:.2f}x")

    # Layout distribution
    layout_counts = {}
    for slide in flattened_slides:
        layout = slide.get('layout_type', 'unknown')
        layout_counts[layout] = layout_counts.get(layout, 0) + 1

    print(f"\n📋 Layout Distribution:")
    for layout, count in sorted(layout_counts.items()):
        icon = {
            "text_bullets": "📝",
            "styled_table": "📋",
            "clean_cards": "🎯",
            "section_header": "📌",
            "bar_chart": "📊",
            "column_chart": "📊",
            "pie_chart": "🥧",
            "line_chart": "📈",
            "chart_image": "🖼️",
            "quote": "💬"
        }.get(layout, "❓")
        print(f"   {icon} {layout}: {count}")


if __name__ == "__main__":
    main()
