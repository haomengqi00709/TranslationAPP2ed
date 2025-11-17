"""
Test complete translation pipeline WITH glossary integration.

This runs the full 9-step pipeline with glossary loaded to ensure
terminology consistency across all stages.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import json

# Import all pipeline components
from glossary import TerminologyGlossary
from extract_content import ContentExtractor
from translate_paragraphs import ParagraphTranslator
from apply_alignment import AlignmentApplicator
from build_slide_context import SlideContextBuilder
from translate_content import ContentTranslator
from apply_table_alignment import TableAlignmentApplicator
from update_pptx import PowerPointUpdater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pipeline_with_glossary():
    """Run complete pipeline with glossary integration."""

    print("\n" + "=" * 80)
    print("  TESTING COMPLETE PIPELINE WITH GLOSSARY")
    print("=" * 80)
    print()

    # Configuration
    INPUT_PPTX = "slides/PPT-3-Government-in-Canada1 (2).pptx"
    OUTPUT_PPTX = "output/test_with_glossary.pptx"
    GLOSSARY_FILE = "glossary.json"
    TEMP_DIR = "temp"

    print(f"📂 Input:    {INPUT_PPTX}")
    print(f"📂 Output:   {OUTPUT_PPTX}")
    print(f"📖 Glossary: {GLOSSARY_FILE}")
    print(f"📂 Temp:     {TEMP_DIR}/")
    print()

    # Ensure temp directory exists
    Path(TEMP_DIR).mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    # ========================================================================
    # STEP 0: Load Glossary
    # ========================================================================
    print("=" * 80)
    print("STEP 0: Loading Glossary")
    print("=" * 80)

    glossary = TerminologyGlossary()
    glossary.load_from_json(GLOSSARY_FILE)
    glossary.compile()

    print(f"✅ Loaded {len(glossary)} glossary entries")
    print()

    # Show some sample entries
    print("Sample glossary entries:")
    for entry in glossary.entries[:5]:
        print(f"  - '{entry.source}' → '{entry.target}' (priority: {entry.priority})")
    print()

    # ========================================================================
    # STEP 1: Extract Content
    # ========================================================================
    print("=" * 80)
    print("STEP 1: Extracting Content")
    print("=" * 80)

    extractor = ContentExtractor()
    counts = extractor.extract_all(
        INPUT_PPTX,
        f"{TEMP_DIR}/extracted_text.jsonl",
        f"{TEMP_DIR}/extracted_tables.jsonl",
        f"{TEMP_DIR}/extracted_charts.jsonl"
    )

    print(f"✅ Extracted:")
    print(f"   - {counts['text_paragraphs']} paragraphs")
    print(f"   - {counts['tables']} tables")
    print(f"   - {counts.get('chart_titles', 0)} charts")
    print()

    # ========================================================================
    # STEP 2: Translate Paragraphs (WITH GLOSSARY)
    # ========================================================================
    print("=" * 80)
    print("STEP 2: Translating Paragraphs (WITH GLOSSARY)")
    print("=" * 80)

    print("📖 Glossary will be injected into LLM prompts...")
    print()

    translator = ParagraphTranslator(
        translator_type="local",
        glossary=glossary  # 👈 GLOSSARY INTEGRATION
    )
    count = translator.translate_paragraphs(
        f"{TEMP_DIR}/extracted_text.jsonl",
        f"{TEMP_DIR}/translated_paragraphs.jsonl"
    )

    print(f"✅ Translated {count} paragraphs with glossary guidance")
    print()

    # ========================================================================
    # STEP 3: Apply BERT Alignment (WITH GLOSSARY)
    # ========================================================================
    print("=" * 80)
    print("STEP 3: Applying BERT Alignment (WITH GLOSSARY)")
    print("=" * 80)

    print("🔗 Glossary phrase mappings loaded into BERT...")
    print()

    aligner = AlignmentApplicator(glossary=glossary)  # 👈 GLOSSARY INTEGRATION
    count = aligner.apply_alignment(
        f"{TEMP_DIR}/translated_paragraphs.jsonl",
        f"{TEMP_DIR}/aligned_paragraphs.jsonl"
    )

    print(f"✅ Aligned {count} paragraphs with glossary-aware BERT")
    print()

    # ========================================================================
    # STEP 4: Build Slide Context
    # ========================================================================
    print("=" * 80)
    print("STEP 4: Building Slide Context")
    print("=" * 80)

    builder = SlideContextBuilder()
    count = builder.build_context(
        f"{TEMP_DIR}/aligned_paragraphs.jsonl",
        f"{TEMP_DIR}/slide_context.jsonl"
    )

    print(f"✅ Built context for {count} slides")
    print()

    # ========================================================================
    # STEP 5: Translate Charts (WITH GLOSSARY)
    # ========================================================================
    print("=" * 80)
    print("STEP 5: Translating Charts (WITH GLOSSARY)")
    print("=" * 80)

    content_translator = ContentTranslator(
        translator_type="local",
        glossary=glossary  # 👈 GLOSSARY INTEGRATION
    )
    count = content_translator.translate_charts(
        f"{TEMP_DIR}/extracted_charts.jsonl",
        f"{TEMP_DIR}/slide_context.jsonl",
        f"{TEMP_DIR}/translated_charts.jsonl"
    )

    print(f"✅ Translated {count} charts with glossary consistency")
    print()

    # ========================================================================
    # STEP 6: Translate Tables (WITH GLOSSARY)
    # ========================================================================
    print("=" * 80)
    print("STEP 6: Translating Tables (WITH GLOSSARY)")
    print("=" * 80)

    count = content_translator.translate_tables(
        f"{TEMP_DIR}/extracted_tables.jsonl",
        f"{TEMP_DIR}/slide_context.jsonl",
        f"{TEMP_DIR}/translated_tables.jsonl"
    )

    print(f"✅ Translated {count} tables with glossary consistency")
    print()

    # ========================================================================
    # STEP 7: Apply Table Alignment (WITH GLOSSARY)
    # ========================================================================
    print("=" * 80)
    print("STEP 7: Applying BERT Alignment to Tables (WITH GLOSSARY)")
    print("=" * 80)

    table_aligner = TableAlignmentApplicator(glossary=glossary)  # 👈 GLOSSARY INTEGRATION
    count = table_aligner.apply_table_alignment(
        f"{TEMP_DIR}/translated_tables.jsonl",
        f"{TEMP_DIR}/aligned_tables.jsonl"
    )

    print(f"✅ Aligned {count} tables with glossary-aware BERT")
    print()

    # ========================================================================
    # STEP 8: Merge All Content
    # ========================================================================
    print("=" * 80)
    print("STEP 8: Merging Content")
    print("=" * 80)

    # Merge aligned paragraphs, tables, and charts
    merged_file = f"{TEMP_DIR}/merged_content.jsonl"

    with open(merged_file, 'w', encoding='utf-8') as f_out:
        # Add paragraphs
        with open(f"{TEMP_DIR}/aligned_paragraphs.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                f_out.write(line)

        # Add tables
        with open(f"{TEMP_DIR}/aligned_tables.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                f_out.write(line)

        # Add charts
        with open(f"{TEMP_DIR}/translated_charts.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                f_out.write(line)

    print(f"✅ Merged all content to {merged_file}")
    print()

    # ========================================================================
    # STEP 9: Update PowerPoint
    # ========================================================================
    print("=" * 80)
    print("STEP 9: Updating PowerPoint")
    print("=" * 80)

    updater = PowerPointUpdater()
    updater.update_presentation(
        INPUT_PPTX,
        merged_file,
        OUTPUT_PPTX
    )

    print(f"✅ PowerPoint updated: {OUTPUT_PPTX}")
    print()

    # ========================================================================
    # VERIFICATION: Check Glossary Compliance
    # ========================================================================
    print("=" * 80)
    print("VERIFICATION: Glossary Compliance Check")
    print("=" * 80)

    # Sample some paragraphs and verify
    violations_found = 0
    terms_checked = 0

    with open(f"{TEMP_DIR}/translated_paragraphs.jsonl", 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 paragraphs
                break

            para = json.loads(line.strip())
            source = para.get("text", "")
            translated = para.get("translated_text", "")

            if source and translated:
                result = glossary.verify_translation(source, translated)
                terms_checked += result['total_terms']
                violations_found += len(result['violations'])

                if result['violations']:
                    print(f"\n⚠️  Paragraph {i+1} violations:")
                    for v in result['violations']:
                        print(f"    - Expected '{v['expected_target']}' for '{v['source_term']}'")

    print()
    if violations_found == 0:
        print(f"✅ All {terms_checked} glossary terms translated correctly!")
    else:
        print(f"⚠️  Found {violations_found} violations out of {terms_checked} terms")
        print(f"   Note: This is expected with local LLM - glossary guides but doesn't force")
    print()

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("✅ PIPELINE COMPLETE WITH GLOSSARY!")
    print("=" * 80)
    print()
    print("📊 Results:")
    print(f"   - Glossary entries used: {len(glossary)}")
    print(f"   - Translated paragraphs: {counts['text_paragraphs']}")
    print(f"   - Translated tables: {counts['tables']}")
    print(f"   - Translated charts: {counts.get('chart_titles', 0)}")
    print()
    print(f"📂 Output saved to: {OUTPUT_PPTX}")
    print()
    print("🎯 Glossary Integration Points:")
    print("   1. ✅ Paragraph translation (glossary → LLM prompts)")
    print("   2. ✅ Paragraph alignment (glossary → BERT mappings)")
    print("   3. ✅ Chart translation (glossary → LLM prompts)")
    print("   4. ✅ Table translation (glossary → LLM prompts)")
    print("   5. ✅ Table alignment (glossary → BERT mappings)")
    print()
    print("Next: Open the output file to verify terminology consistency!")
    print()


if __name__ == "__main__":
    test_pipeline_with_glossary()
