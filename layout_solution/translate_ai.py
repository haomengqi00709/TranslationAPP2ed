#!/usr/bin/env python3
"""
Stage 2: AI-Powered Translation & Restructuring
Translates English slides to French with layout constraints and context consistency.
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
        print(f"⚠️  Warning: Glossary not found at {glossary_path}")
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

    if "instructions" in glossary and "preserve_as_is" in glossary["instructions"]:
        parts.append("\nDO NOT TRANSLATE (keep as-is):")
        for item in glossary["instructions"]["preserve_as_is"]:
            parts.append(f"  • {item}")

    return "\n".join(parts)


def build_prompt(
    slide_data: Dict,
    glossary: Dict,
    previous_french_slide: Optional[Dict] = None
) -> str:
    """
    Build the AI prompt for translating a single slide.

    Args:
        slide_data: Current slide to translate
        glossary: Translation glossary
        previous_french_slide: Previous slide's French output for consistency

    Returns:
        Complete prompt string
    """
    glossary_text = build_glossary_text(glossary)

    # First slide gets detailed instructions
    if previous_french_slide is None:
        prompt = f"""You are a professional translator specializing in government/institutional documents. You will translate English PowerPoint slide content into French while restructuring it for optimal layout.

{glossary_text}

CRITICAL LAYOUT CONSTRAINTS:
- Maximum 4 bullet points per slide
- Maximum 20 words per bullet point
- Use formal business French (vouvoiement)
- Bullet points should be concise, impactful phrases
- Maintain professional tone throughout

TRANSLATION RULES:
1. Use official translations from the glossary above
2. Preserve company names, contract numbers, and technical codes
3. Translate the meaning, not word-for-word
4. Condense verbose content into concise bullet points
5. Maintain document structure and hierarchy

INPUT SLIDE:
Title: {slide_data['title']}
Content: {slide_data['content']}

OUTPUT FORMAT (return ONLY valid JSON, no markdown):
{{
  "french_title": "Translated concise title",
  "summary_one_liner": "One-sentence summary in French (max 25 words)",
  "french_points": [
    "First bullet point in French (max 20 words)",
    "Second bullet point in French (max 20 words)",
    "Third bullet point in French (max 20 words)",
    "Fourth bullet point in French (max 20 words)"
  ]
}}

IMPORTANT:
- If content is very short (like a section header), french_points can be empty []
- If content is long, condense to most important 4 points
- Return ONLY the JSON object, no other text"""

    else:
        # Subsequent slides get previous example for consistency
        prompt = f"""Continue translating the PowerPoint deck. Follow the EXACT same style, terminology, and format as the previous slide.

{glossary_text}

PREVIOUS SLIDE (for consistency reference):
Title: {previous_french_slide.get('original_title', 'N/A')}
French Title: {previous_french_slide['french_title']}
French Points: {json.dumps(previous_french_slide['french_points'], ensure_ascii=False, indent=2)}

CONSTRAINTS (same as before):
- Max 4 bullet points, max 20 words each
- Use formal French, same terminology as previous slide
- Maintain consistent tone and structure

INPUT SLIDE:
Title: {slide_data['title']}
Content: {slide_data['content']}

OUTPUT FORMAT (return ONLY valid JSON, no markdown):
{{
  "french_title": "Translated title",
  "summary_one_liner": "One-sentence summary (max 25 words)",
  "french_points": ["...", "...", "...", "..."]
}}

Return ONLY the JSON object."""

    return prompt


def call_openai_api(prompt: str, api_key: str) -> Dict:
    """Call OpenAI API for translation."""
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ OpenAI library not installed. Run: pip3 install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Fast and cheap for translation
        messages=[
            {"role": "system", "content": "You are a professional French translator specializing in government documents. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower temperature for consistent translations
        response_format={"type": "json_object"}
    )

    result = response.choices[0].message.content
    return json.loads(result)


def call_gemini_api(prompt: str, api_key: str) -> Dict:
    """Call Google Gemini API for translation."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Google Generative AI library not installed. Run: pip3 install google-generativeai")
        sys.exit(1)

    genai.configure(api_key=api_key)

    # Use Gemini Flash (fast and free)
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
        generation_config={
            'temperature': 0.3
        }
    )

    response = model.generate_content(prompt)

    # Extract JSON from response (Gemini may wrap in markdown)
    text = response.text.strip()
    if text.startswith('```json'):
        text = text[7:]  # Remove ```json
    if text.startswith('```'):
        text = text[3:]  # Remove ```
    if text.endswith('```'):
        text = text[:-3]  # Remove trailing ```

    return json.loads(text.strip())


def translate_slides(
    slides_data: List[Dict],
    glossary: Dict,
    api_key: str,
    api_type: str = "openai"
) -> List[Dict]:
    """
    Translate all slides using context window approach.

    Args:
        slides_data: List of extracted slide data
        glossary: Translation glossary
        api_key: API key (OpenAI or Gemini)
        api_type: "openai" or "gemini"

    Returns:
        List of translated slides with French content
    """
    translated_slides = []
    previous_french = None

    for idx, slide in enumerate(slides_data, start=1):
        print(f"🔄 Translating Slide {idx}/{len(slides_data)}: {slide['title'][:50]}...")

        # Build prompt with context
        prompt = build_prompt(slide, glossary, previous_french)

        # Call AI API
        try:
            if api_type == "gemini":
                french_content = call_gemini_api(prompt, api_key)
            else:
                french_content = call_openai_api(prompt, api_key)

            # Combine original + translated data
            translated_slide = {
                "id": slide["id"],
                "original_title": slide["title"],
                "original_content": slide["content"],
                "french_title": french_content["french_title"],
                "summary_one_liner": french_content.get("summary_one_liner", ""),
                "french_points": french_content["french_points"],
                "original_img": slide["original_img"]
            }

            translated_slides.append(translated_slide)

            # Update context for next slide
            previous_french = translated_slide

            print(f"  ✅ Title: {french_content['french_title'][:60]}...")
            print(f"  ✅ Points: {len(french_content['french_points'])}")

        except Exception as e:
            print(f"  ❌ Error translating slide {idx}: {e}")
            # Add placeholder to maintain order
            translated_slides.append({
                "id": slide["id"],
                "error": str(e),
                "original_title": slide["title"]
            })

    return translated_slides


def main():
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv()

    # Check for API keys (try Gemini first, then OpenAI)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    api_key = None
    api_type = None

    if gemini_key:
        api_key = gemini_key
        api_type = "gemini"
        print("🤖 Using Google Gemini API (gemini-flash-latest)")
    elif openai_key:
        api_key = openai_key
        api_type = "openai"
        print("🤖 Using OpenAI API (gpt-4o-mini)")
    else:
        print("❌ Error: No API key found")
        print("\n📋 Setup Instructions:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("\n2. Edit .env and add your API key:")
        print("   GEMINI_API_KEY=your-gemini-key-here")
        print("   OR")
        print("   OPENAI_API_KEY=sk-your-openai-key-here")
        print("\n3. Get keys from:")
        print("   - Gemini (FREE): https://aistudio.google.com/app/apikey")
        print("   - OpenAI (paid): https://platform.openai.com/api-keys")
        sys.exit(1)

    # Load extracted slides
    input_path = Path("output/extracted_slides.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found. Run extract_ppt.py first.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} slides from {input_path}")

    # Load glossary
    glossary = load_glossary()
    print(f"📚 Loaded glossary with {len(glossary.get('organizations', {}))} organizations, "
          f"{len(glossary.get('terms', {}))} terms")

    # Translate slides
    translated_slides = translate_slides(slides_data, glossary, api_key, api_type)

    # Save results
    output_path = Path("output/translated_slides.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(translated_slides, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved to: {output_path}")

    # Print summary
    print("\n📊 Translation Summary:")
    for slide in translated_slides[:3]:
        if "error" not in slide:
            print(f"\nSlide {slide['id']}:")
            print(f"  EN: {slide['original_title'][:60]}...")
            print(f"  FR: {slide['french_title'][:60]}...")
            print(f"  Points: {len(slide['french_points'])}")

    if len(translated_slides) > 3:
        print(f"\n... and {len(translated_slides) - 3} more slides")


if __name__ == "__main__":
    main()
