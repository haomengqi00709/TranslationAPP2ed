#!/usr/bin/env python3
"""
Test V5 on Slide 2 only (the problematic dense methodology slide).
"""

import json
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# Import V5 functions
sys.path.insert(0, str(Path(__file__).parent))
from translate_ai_v5 import load_glossary, restructure_slide_v5


def main():
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        sys.exit(1)

    print("🧪 Testing V5 on Slide 2 (dense methodology)")
    print("="*70 + "\n")

    # Load source slides
    input_path = Path("output/extracted_slides_v2.json")
    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    # Get Slide 2 (index 1)
    slide_2 = slides_data[1]

    print(f"ORIGINAL SLIDE 2:")
    print(f"Title: {slide_2['title']}")
    print(f"Content length: {len(slide_2['content'])} chars, {len(slide_2['content'].split())} words")
    print(f"\nFirst 200 chars of content:")
    print(slide_2['content'][:200] + "...")
    print("\n" + "="*70)

    # Load glossary
    glossary = load_glossary()

    # Restructure Slide 2
    result = restructure_slide_v5(slide_2, glossary, api_key)

    # Print results
    print("\n" + "="*70)
    print("V5 RESTRUCTURING RESULT:")
    print("="*70)

    print(f"\n📊 Analysis:")
    analysis = result['analysis']
    print(f"   Content type: {analysis['content_type']}")
    print(f"   Density: {analysis['density']}")
    print(f"   Word count: {analysis['word_count']}")

    if analysis.get('key_statistics'):
        print(f"   Key statistics found: {len(analysis['key_statistics'])}")
        for stat in analysis['key_statistics'][:3]:
            print(f"      • {stat['number']} - {stat['label']}")

    if analysis.get('distinct_topics'):
        print(f"   Topics identified: {', '.join(analysis['distinct_topics'])}")

    print(f"\n✂️  Decision: Split into {len(result['output_slides'])} slide(s)")

    print("\n" + "-"*70)
    for i, slide in enumerate(result['output_slides'], 1):
        print(f"\nOUTPUT SLIDE {i}:")
        print(f"   ID: {slide['id']}")
        print(f"   Layout: {slide['layout_type']}")
        print(f"   Title: {slide['french_title']}")
        print(f"   Summary: {slide['summary_one_liner']}")

        if slide['layout_type'] == 'clean_cards' and slide['cards']:
            print(f"   Cards ({len(slide['cards'])}):")
            for card in slide['cards']:
                print(f"      • {card['number']} - {card['label']}")
                if card.get('sublabel'):
                    print(f"        ({card['sublabel']})")

        if slide['layout_type'] == 'text_bullets' and slide['french_points']:
            print(f"   Bullets ({len(slide['french_points'])}):")
            for bullet in slide['french_points']:
                print(f"      • {bullet[:80]}...")

        print("-"*70)

    # Save test output
    output_path = Path("output/test_v5_slide2.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Test result saved to: {output_path}")

    print("\n✅ Test complete! Review the output above.")
    print("   If this looks good, run translate_ai_v5.py for full corpus.")


if __name__ == "__main__":
    main()
