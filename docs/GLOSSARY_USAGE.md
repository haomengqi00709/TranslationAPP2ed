# Terminology Glossary System

## Overview

The glossary system ensures **consistent terminology** across your PowerPoint translations. It works in two stages:

1. **Translation Stage**: Injects glossary terms into LLM prompts to guide translation
2. **Alignment Stage**: Teaches BERT aligner to recognize glossary term mappings for better formatting preservation

## Quick Start

### 1. Create Your Glossary

The system comes with a sample glossary (`glossary.json`) containing Canadian government and disability accommodation terms. You can:

**Option A: Use the sample glossary**
```bash
# Already created! Just use glossary.json
```

**Option B: Create a custom glossary**
```json
{
  "entries": [
    {
      "source": "Senate",
      "target": "Sénat",
      "case_sensitive": true,
      "priority": 10,
      "notes": "Canadian Senate (upper house)"
    },
    {
      "source": "accommodation",
      "target": "mesure d'adaptation",
      "context": "disability",
      "priority": 9,
      "notes": "In disability context, not housing"
    }
  ]
}
```

**Option C: Use CSV format** (easier to edit in Excel/Google Sheets)
```csv
source,target,context,case_sensitive,notes,priority
Senate,Sénat,,true,Canadian Senate,10
accommodation,mesure d'adaptation,disability,false,Not housing,9
invisible disability,handicap invisible,,false,,9
```

### 2. Load Glossary in Your Code

The glossary integrates seamlessly into the existing pipeline. Here's how to use it programmatically:

```python
from glossary import TerminologyGlossary
from translate_paragraphs import ParagraphTranslator
from apply_alignment import AlignmentApplicator
from apply_table_alignment import TableAlignmentApplicator

# Load glossary
glossary = TerminologyGlossary()
glossary.load_from_json("glossary.json")  # or .load_from_csv("glossary.csv")

# Use in translation
translator = ParagraphTranslator(
    translator_type="local",  # or "openai" or "anthropic"
    glossary=glossary  # 👈 Glossary is automatically injected into prompts
)
translator.translate_paragraphs("input.jsonl", "output.jsonl")

# Use in BERT alignment
aligner = AlignmentApplicator(glossary=glossary)  # 👈 Glossary mappings added to BERT
aligner.apply_alignment("translated.jsonl", "aligned.jsonl")

# Use in table alignment
table_aligner = TableAlignmentApplicator(glossary=glossary)
table_aligner.apply_table_alignment("tables.jsonl", "aligned_tables.jsonl")
```

### 3. Verify Translations

Check if translations comply with your glossary:

```python
from glossary import TerminologyGlossary

glossary = TerminologyGlossary()
glossary.load_from_json("glossary.json")

source = "Employees with an invisible disability may request accommodation."
translated = "Les employés ayant un handicap invisible peuvent demander une mesure d'adaptation."

result = glossary.verify_translation(source, translated)

if result['compliant']:
    print(f"✅ All {result['total_terms']} terms translated correctly!")
else:
    print(f"❌ Found {len(result['violations'])} violations:")
    for v in result['violations']:
        print(f"  - Expected '{v['expected_target']}' for '{v['source_term']}'")
```

## Glossary Entry Fields

### Required Fields
- **`source`**: English term to match (e.g., "Senate")
- **`target`**: French translation (e.g., "Sénat")

### Optional Fields
- **`context`**: Disambiguate terms with multiple meanings
  - Example: "accommodation" in "disability" context → "mesure d'adaptation"
  - Example: "accommodation" in "housing" context → "hébergement"

- **`case_sensitive`**: Whether matching requires exact case (default: `false`)
  - `true`: "Senate" matches, "senate" doesn't
  - `false`: Both match

- **`priority`**: Higher priority terms are matched first (default: `0`)
  - Use for overlapping terms (e.g., "Senate" vs "Senator")
  - Range: 0-100 (10 is high, 3 is medium, 0 is low)

- **`notes`**: Human-readable notes for context

## How It Works

### Stage 1: Translation
When translating a paragraph with glossary terms:

1. **Detects** glossary terms in source text
2. **Generates** prompt context with relevant terms:
   ```
   TERMINOLOGY GLOSSARY (use these exact translations):

   - "Senate" → "Sénat"
   - "invisible disability" → "handicap invisible"
   - "accommodation" → "mesure d'adaptation" (context: disability)
   ```
3. **Injects** this into the LLM prompt automatically
4. **LLM translates** using the specified terms

### Stage 2: BERT Alignment
When aligning formatting after translation:

1. **Loads** glossary phrase mappings into BERT:
   ```python
   {
     'senate': ['sénat'],
     'invisible disability': ['handicap invisible'],
     'accommodation': ["mesure d'adaptation"]
   }
   ```
2. **BERT recognizes** these as semantically equivalent
3. **Matches formatting** correctly even if terms differ from natural translation

## Example Workflow

### Complete Translation with Glossary

```python
import logging
from glossary import TerminologyGlossary
from extract_content import ContentExtractor
from translate_paragraphs import ParagraphTranslator
from apply_alignment import AlignmentApplicator
from translate_content import ContentTranslator
from apply_table_alignment import TableAlignmentApplicator
from update_pptx import PowerPointUpdater

logging.basicConfig(level=logging.INFO)

# 1. Load glossary
glossary = TerminologyGlossary()
glossary.load_from_json("glossary.json")
print(f"Loaded {len(glossary)} glossary entries")

# 2. Extract content
extractor = ContentExtractor()
extractor.extract_all("input.pptx", "temp/extracted_text.jsonl",
                      "temp/extracted_tables.jsonl", "temp/extracted_charts.jsonl")

# 3. Translate paragraphs WITH GLOSSARY
translator = ParagraphTranslator(translator_type="local", glossary=glossary)
translator.translate_paragraphs("temp/extracted_text.jsonl",
                                "temp/translated_text.jsonl")

# 4. Apply BERT alignment WITH GLOSSARY
aligner = AlignmentApplicator(glossary=glossary)
aligner.apply_alignment("temp/translated_text.jsonl", "temp/aligned_text.jsonl")

# 5. Translate tables/charts WITH GLOSSARY
content_translator = ContentTranslator(translator_type="local", glossary=glossary)
content_translator.translate_tables("temp/extracted_tables.jsonl",
                                   "temp/slide_context.jsonl",
                                   "temp/translated_tables.jsonl")

# 6. Apply table alignment WITH GLOSSARY
table_aligner = TableAlignmentApplicator(glossary=glossary)
table_aligner.apply_table_alignment("temp/translated_tables.jsonl",
                                   "temp/aligned_tables.jsonl")

# 7. Update PowerPoint
updater = PowerPointUpdater()
updater.update_pptx("input.pptx", "temp/merged_content.jsonl", "output.pptx")

print("✅ Translation complete with glossary consistency!")
```

## Best Practices

### 1. Start Small
Begin with high-priority terms (government names, key concepts, brand names):
```json
{
  "entries": [
    {"source": "Senate", "target": "Sénat", "priority": 10},
    {"source": "Department of Health", "target": "Ministère de la Santé", "priority": 10}
  ]
}
```

### 2. Use Context for Ambiguous Terms
Same word, different meanings:
```json
{
  "entries": [
    {"source": "accommodation", "target": "mesure d'adaptation", "context": "disability"},
    {"source": "accommodation", "target": "hébergement", "context": "housing"}
  ]
}
```

### 3. Set Priorities for Overlapping Terms
Prevent partial matches:
```json
{
  "entries": [
    {"source": "Senate", "target": "Sénat", "priority": 10},
    {"source": "Senator", "target": "Sénateur", "priority": 9}
  ]
}
```
The system matches "Senate" first, preventing "Senator" from matching just "Senat".

### 4. Use Case-Sensitivity for Proper Nouns
```json
{
  "entries": [
    {"source": "Senate", "target": "Sénat", "case_sensitive": true},
    {"source": "Parliament", "target": "Parlement", "case_sensitive": true}
  ]
}
```

### 5. Add Notes for Team Collaboration
```json
{
  "entries": [
    {
      "source": "accommodation",
      "target": "mesure d'adaptation",
      "context": "disability",
      "notes": "As per Treasury Board directive on disability management"
    }
  ]
}
```

## Testing Your Glossary

Run the test script to verify your glossary works:

```bash
python test_glossary_integration.py
```

This will show:
- Which terms are found in sample text
- How prompt context is generated
- How BERT phrase mappings are created
- Translation verification results

## Troubleshooting

### Problem: Terms not being matched
**Solution**: Check word boundaries. The glossary uses `\b` boundaries, so "Senate" won't match inside "Senates".

### Problem: Wrong translation priority
**Solution**: Increase priority for important terms. Higher = matched first.

### Problem: BERT not aligning correctly
**Solution**: Ensure glossary terms are semantically reasonable. "Senate" → "Sénat" works because they're similar. "Senate" → "Upper House" might not align well.

### Problem: Case sensitivity issues
**Solution**:
- Use `case_sensitive: true` for proper nouns (Senate, Parliament)
- Use `case_sensitive: false` for common terms (employee, manager)

## Advanced Features

### Programmatic Glossary Building

```python
glossary = TerminologyGlossary()

# Add entries programmatically
glossary.add_entry("Senate", "Sénat", case_sensitive=True, priority=10)
glossary.add_entry("accommodation", "mesure d'adaptation", context="disability", priority=9)

# Save for reuse
glossary.save_to_json("my_glossary.json")
```

### Loading from Dictionary

```python
terms = {
    "Senate": "Sénat",
    "Parliament": "Parlement",
    "employee": "employé"
}

glossary = TerminologyGlossary()
glossary.load_from_dict(terms)
```

### Get BERT Mappings for Custom Use

```python
glossary = TerminologyGlossary()
glossary.load_from_json("glossary.json")

bert_mappings = glossary.get_bert_phrase_mappings()
# Returns: {'senate': ['sénat'], 'parliament': ['parlement'], ...}
```

## Integration with Pipeline Scripts

The glossary system is designed to integrate with existing scripts WITHOUT breaking compatibility:

- **Without glossary**: Scripts work exactly as before
- **With glossary**: Pass `glossary=glossary` to constructors

This means you can gradually adopt the glossary system without rewriting existing code.

## Performance Notes

- Glossary matching uses regex with word boundaries (fast)
- Compilation step (sorting, indexing) happens once
- Minimal overhead on translation/alignment performance
- Recommended: < 100 entries for optimal performance

## Next Steps

1. **Edit glossary.json** with your project-specific terms
2. **Run test_glossary_integration.py** to verify it works
3. **Integrate into your pipeline** by passing `glossary=glossary`
4. **Verify translations** using `glossary.verify_translation()`
5. **Iterate and improve** as you discover new terminology

---

**Questions?** Check the code examples in:
- `glossary.py` - Core glossary implementation
- `test_glossary_integration.py` - Integration examples
- `CLAUDE.md` - Full project documentation
