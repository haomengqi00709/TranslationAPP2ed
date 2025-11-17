#!/bin/bash
# Complete translation pipeline - runs all steps in sequence
# Usage: ./run_pipeline.sh

set -e  # Exit on any error

echo "=========================================="
echo "PowerPoint Translation Pipeline"
echo "=========================================="
echo ""

# Activate virtual environment
source myenv/bin/activate

INPUT_PPTX="slides/PPT-3-Government-in-Canada1 (2).pptx"
OUTPUT_PPTX="output/test_complete_translation.pptx"

echo "📂 Input:  $INPUT_PPTX"
echo "📂 Output: $OUTPUT_PPTX"
echo ""

# Step 1: Extract all content
echo "=========================================="
echo "STEP 1: Extracting content..."
echo "=========================================="
python extract_content.py "$INPUT_PPTX"
echo "✅ Extraction complete"
echo ""

# Step 2: Translate paragraphs
echo "=========================================="
echo "STEP 2: Translating paragraphs..."
echo "=========================================="
python translate_paragraphs.py temp/extracted_text.jsonl temp/translated_paragraphs.jsonl local
echo "✅ Translation complete"
echo ""

# Step 3: Apply BERT alignment
echo "=========================================="
echo "STEP 3: Applying BERT alignment..."
echo "=========================================="
python apply_alignment.py temp/translated_paragraphs.jsonl temp/aligned_paragraphs.jsonl
echo "✅ Alignment complete"
echo ""

# Step 4: Build slide context
echo "=========================================="
echo "STEP 4: Building slide context..."
echo "=========================================="
python build_slide_context.py temp/aligned_paragraphs.jsonl temp/slide_context.jsonl
echo "✅ Context built"
echo ""

# Step 5: Translate charts
echo "=========================================="
echo "STEP 5: Translating charts..."
echo "=========================================="
python translate_content.py charts temp/extracted_charts.jsonl temp/slide_context.jsonl temp/translated_charts.jsonl
echo "✅ Charts translated"
echo ""

# Step 6: Translate tables
echo "=========================================="
echo "STEP 6: Translating tables..."
echo "=========================================="
python translate_content.py tables temp/extracted_tables.jsonl temp/slide_context.jsonl temp/translated_tables.jsonl
echo "✅ Tables translated"
echo ""

# Step 7: Apply BERT alignment to tables
echo "=========================================="
echo "STEP 7: Applying BERT alignment to tables..."
echo "=========================================="
python apply_table_alignment.py temp/translated_tables.jsonl temp/aligned_tables.jsonl
echo "✅ Tables aligned"
echo ""

# Step 8: Merge all content
echo "=========================================="
echo "STEP 8: Merging content..."
echo "=========================================="
cat temp/aligned_paragraphs.jsonl temp/aligned_tables.jsonl temp/translated_charts.jsonl > temp/merged_content.jsonl
echo "✅ Content merged"
echo ""

# Step 9: Update PowerPoint
echo "=========================================="
echo "STEP 9: Updating PowerPoint..."
echo "=========================================="
python update_pptx.py "$INPUT_PPTX" temp/merged_content.jsonl "$OUTPUT_PPTX"
echo "✅ PowerPoint updated"
echo ""

# Summary
echo "=========================================="
echo "✅ PIPELINE COMPLETE!"
echo "=========================================="
echo ""
echo "📊 Results:"
echo "   - Translated: $(wc -l < temp/extracted_text.jsonl) paragraphs"
echo "   - Translated: $(wc -l < temp/extracted_tables.jsonl) tables"
echo "   - Translated: $(wc -l < temp/extracted_charts.jsonl) charts"
echo ""
echo "📂 Output saved to: $OUTPUT_PPTX"
echo ""
echo "Opening translated file..."
open "$OUTPUT_PPTX"
