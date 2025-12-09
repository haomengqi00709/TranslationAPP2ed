#!/usr/bin/env python3
"""
Multimodal AI Chart Analysis using Gemini Vision
Analyzes chart images and decides optimal representation.
"""

import json
import os
from pathlib import Path
from PIL import Image
import google.generativeai as genai


def analyze_chart_image(image_path: str, chart_info: dict, api_key: str) -> dict:
    """
    Analyze a chart image using Gemini Vision and decide optimal layout.

    Args:
        image_path: Path to slide image containing chart
        chart_info: Chart metadata from extraction
        api_key: Gemini API key

    Returns:
        dict with analysis results and layout decision
    """
    genai.configure(api_key=api_key)

    # Use Gemini Flash for image analysis (supports vision)
    model = genai.GenerativeModel('gemini-flash-latest')

    # Load image
    image_path = Path(image_path)
    if not image_path.exists():
        return {
            "error": f"Image not found: {image_path}",
            "layout_decision": "chart_image",
            "fallback": True
        }

    img = Image.open(image_path)

    # Build vision prompt
    prompt = build_chart_analysis_prompt(chart_info)

    try:
        # Send image + prompt to Gemini Vision
        response = model.generate_content([prompt, img])
        text = response.text.strip()

        # Clean JSON extraction
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        analysis = json.loads(text.strip())
        return analysis

    except Exception as e:
        print(f"   ⚠️  Vision analysis failed: {e}")
        return {
            "error": str(e),
            "layout_decision": "chart_image",
            "fallback": True,
            "reason": "Keep as image due to analysis error"
        }


def build_chart_analysis_prompt(chart_info: dict) -> str:
    """Build prompt for chart analysis."""
    chart_title = chart_info.get('chart_title', 'Untitled chart')
    chart_type = chart_info.get('chart_type', 'unknown')

    prompt = f"""You are analyzing a chart/graph from a government survey presentation.

CHART METADATA:
- Title: {chart_title}
- Type: {chart_type}

YOUR TASK: Extract the chart data and decide optimal representation for a French report.

CHART TYPE DECISIONS:

1. **bar_chart** - Vertical bars comparing categories
   - Use for: Comparing values across categories
   - Example: Employee vs Supervisor percentages

2. **column_chart** - Horizontal bars
   - Use for: Long category names, rankings
   - Example: Wait time categories across different groups

3. **pie_chart** - Circular slices showing proportions
   - Use for: Parts of a whole (must add to 100%)
   - Example: Distribution of request types

4. **line_chart** - Connected points showing trends
   - Use for: Changes over time or sequential data
   - Example: Response rates by month

5. **clean_cards** - 2-4 key statistics with visual emphasis
   - Use for: Highlighting 2-4 critical numbers
   - Example: "77% require certificate, 23% do not"

6. **styled_table** - Structured data in rows/columns
   - Use for: Complex comparisons with multiple dimensions
   - Example: 5+ categories × 3 groups

7. **chart_image** - Keep original image (fallback)
   - Use for: Complex multi-series, stacked charts, or unclear data

RESPONSE FORMAT (JSON only):

{{
  "layout_decision": "bar_chart|column_chart|pie_chart|line_chart|clean_cards|styled_table|chart_image",
  "reasoning": "Brief explanation of why this representation is best",

  // IF bar_chart, column_chart, line_chart chosen:
  "chart_data": {{
    "title": "{chart_title}",
    "labels": ["Category 1", "Category 2", "Category 3"],
    "datasets": [
      {{
        "label": "Series name (e.g., Employees)",
        "data": [77, 79, 87],
        "backgroundColor": "#4472C4"  // Optional: if color is important
      }},
      {{
        "label": "Series 2 (if multiple series)",
        "data": [34, 41, 44],
        "backgroundColor": "#ED7D31"
      }}
    ],
    "x_axis_label": "Categories",  // Optional
    "y_axis_label": "Percentage"   // Optional
  }},

  // IF pie_chart chosen:
  "chart_data": {{
    "title": "{chart_title}",
    "labels": ["Slice 1", "Slice 2", "Slice 3"],
    "data": [45, 30, 25],  // Must add to 100 for percentages
    "backgroundColor": ["#4472C4", "#ED7D31", "#A5A5A5"]  // Optional colors
  }},

  // IF clean_cards chosen:
  "cards": [
    {{"number": "77%", "label": "Label", "sublabel": "Optional context"}}
  ],

  // IF styled_table chosen:
  "table": {{
    "headers": ["Column 1", "Column 2"],
    "rows": [["Row 1 data", "30%"]]
  }},

  // IF chart_image chosen:
  "caption": "French caption explaining key insight"
}}

EXTRACTION RULES:
- Extract ALL visible data points accurately (don't estimate or round)
- Preserve English text as-is (will be translated to French later)
- If multiple series (lines/bars), create separate datasets
- Include axis labels if visible
- For pie charts, ensure data adds to 100% (or close to it)
- Choose chart type that best matches the VISUAL STRUCTURE, not just content

IMPORTANT CASES:
- 2 bars side-by-side comparing groups → bar_chart with 1 dataset
- Multiple bars per category (grouped) → bar_chart with multiple datasets
- Percentages in a circle → pie_chart
- Values over time/sequence → line_chart
- 2-4 simple values to emphasize → clean_cards
- Complex table-like data → styled_table
- Unclear or too complex → chart_image (fallback)

Analyze the chart image and respond with JSON only."""

    return prompt


def process_chart_slide(slide_data: dict, image_dir: Path, api_key: str) -> dict:
    """
    Process a slide with charts using vision analysis.

    Args:
        slide_data: Extracted slide data with charts
        image_dir: Directory containing slide images
        api_key: Gemini API key

    Returns:
        dict with vision analysis results
    """
    slide_id = slide_data['id']
    charts = slide_data.get('charts', [])

    if not charts:
        return {"error": "No charts found in slide data"}

    # Get slide image path
    image_path = image_dir / f"slide{slide_id}.png"

    print(f"\n🔍 Vision Analysis: Slide {slide_id}")
    print(f"   Charts: {len(charts)}")
    print(f"   Image: {image_path.name}")

    # For now, analyze using first chart (could extend to handle multiple charts)
    chart_info = charts[0]

    analysis = analyze_chart_image(str(image_path), chart_info, api_key)

    if analysis.get('fallback'):
        print(f"   ⚠️  Fallback to chart_image layout")
    else:
        layout = analysis.get('layout_decision', 'chart_image')
        print(f"   ✅ Decision: {layout}")
        print(f"   Reasoning: {analysis.get('reasoning', 'N/A')[:60]}...")

    return analysis


def main():
    """Test vision analysis on chart slides."""
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    # Load extracted slides
    slides_path = Path("output/extracted_slides_v2.json")
    if not slides_path.exists():
        print(f"❌ Error: {slides_path} not found")
        return

    with open(slides_path, 'r', encoding='utf-8') as f:
        slides = json.load(f)

    # Find chart slides
    chart_slides = [s for s in slides if s.get('charts')]

    print(f"📊 Found {len(chart_slides)} slides with charts\n")

    image_dir = Path("output/slides_images")
    if not image_dir.exists():
        print(f"❌ Error: {image_dir} not found. Run export_slides_as_images.py first")
        return

    # Analyze specific chart slides
    # Test slides 8 and 9 (simpler charts)
    test_slides = [s for s in chart_slides if s['id'] in [8, 9]]

    results = []
    for slide in test_slides[:2]:  # Test 2 slides to avoid rate limits
        analysis = process_chart_slide(slide, image_dir, api_key)
        results.append({
            "slide_id": slide['id'],
            "slide_title": slide['title'],
            "analysis": analysis
        })

        # Delay to avoid rate limits
        import time
        time.sleep(6)

    # Save results
    output_path = Path("output/chart_vision_analysis.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Analysis saved to: {output_path}")

    # Summary
    print(f"\n📊 Vision Analysis Summary:")
    for result in results:
        slide_id = result['slide_id']
        decision = result['analysis'].get('layout_decision', 'unknown')
        print(f"   Slide {slide_id}: {decision}")


if __name__ == "__main__":
    main()
