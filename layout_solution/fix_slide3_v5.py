#!/usr/bin/env python3
"""
Fix Slide 3 that failed in V5 translation.
"""

import json
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, str(Path(__file__).parent))
from translate_ai_v5 import load_glossary, restructure_slide_v5


def main():
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    print("🔧 Fixing Slide 3...")

    # Load source slides
    input_path = Path("output/extracted_slides_v2.json")
    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    # Get Slide 3 (index 2)
    slide_3 = slides_data[2]

    # Load glossary
    glossary = load_glossary()

    # Retry Slide 3
    try:
        result = restructure_slide_v5(slide_3, glossary, api_key)

        print(f"\n✅ Slide 3 restructured successfully!")
        print(f"   Generated {len(result['output_slides'])} output slides")

        # Load existing V5 results
        full_output_path = Path("output/restructured_full_v5.json")
        with open(full_output_path, 'r', encoding='utf-8') as f:
            all_results = json.load(f)

        # Replace Slide 3 (index 2)
        all_results[2] = result

        # Save updated full results
        with open(full_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"   Updated: {full_output_path}")

        # Regenerate flattened slides
        flattened = []
        for source_slide in all_results:
            if 'error' not in source_slide:
                for output_slide in source_slide['output_slides']:
                    flattened.append(output_slide)

        flattened_output_path = Path("output/translated_slides_v5.json")
        with open(flattened_output_path, 'w', encoding='utf-8') as f:
            json.dump(flattened, f, ensure_ascii=False, indent=2)

        print(f"   Updated: {flattened_output_path}")

        # Print summary
        print(f"\n📊 Updated Summary:")
        print(f"   Total output slides: {len(flattened)}")

        layout_counts = {}
        for slide in flattened:
            layout = slide.get('layout_type', 'unknown')
            layout_counts[layout] = layout_counts.get(layout, 0) + 1

        print(f"\n📋 Layout Distribution:")
        for layout, count in sorted(layout_counts.items()):
            icon = {
                "text_bullets": "📝",
                "styled_table": "📋",
                "clean_cards": "🎯",
                "section_header": "📌"
            }.get(layout, "❓")
            print(f"   {icon} {layout}: {count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
