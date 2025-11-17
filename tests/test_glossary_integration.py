"""
Test glossary integration with translation and BERT alignment.

This demonstrates how the glossary system ensures terminology consistency
across translation and alignment stages.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from glossary import TerminologyGlossary
from translate_paragraphs import ParagraphTranslator
from apply_alignment import AlignmentApplicator

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_glossary_integration():
    """Test complete glossary integration."""

    print("=" * 80)
    print("Glossary Integration Test")
    print("=" * 80)
    print()

    # Load glossary
    print("📖 Loading glossary from glossary.json...")
    glossary = TerminologyGlossary()
    glossary.load_from_json("glossary.json")
    glossary.compile()
    print(f"✅ Loaded {len(glossary)} glossary entries")
    print()

    # Test text
    test_text = "Employees with an invisible disability may request accommodation from the Senate."
    print(f"Original text:")
    print(f"  {test_text}")
    print()

    # Show glossary matches
    print("📝 Glossary terms found in text:")
    matches = glossary.get_matching_entries(test_text)
    for entry, start, end in matches:
        print(f"  - '{test_text[start:end]}' → '{entry.target}' (priority: {entry.priority})")
    print()

    # Show prompt context
    print("💬 Prompt context for LLM:")
    print("-" * 80)
    prompt_context = glossary.get_prompt_context(test_text)
    print(prompt_context)
    print("-" * 80)
    print()

    # Show BERT phrase mappings
    print("🔗 BERT phrase mappings:")
    bert_mappings = glossary.get_bert_phrase_mappings()
    relevant_mappings = {k: v for k, v in bert_mappings.items()
                        if any(term.lower() in k for term in ["senate", "disability", "accommodation", "employee"])}
    for source, targets in relevant_mappings.items():
        print(f"  '{source}' → {targets}")
    print()

    # Simulate translation
    print("🌐 Translation Integration:")
    print("  1. Glossary context is injected into LLM prompt")
    print("  2. LLM translates using glossary terms")
    print("  3. Expected translation:")
    expected = "Les employés ayant un handicap invisible peuvent demander une mesure d'adaptation au Sénat."
    print(f"     {expected}")
    print()

    # Verify translation
    print("✓ Verification:")
    result = glossary.verify_translation(test_text, expected)
    print(f"  Compliant: {result['compliant']}")
    print(f"  Correct terms: {len(result['correct'])}/{result['total_terms']}")
    print()

    # Show BERT alignment benefit
    print("🎯 BERT Alignment Integration:")
    print("  1. BERT aligner receives glossary phrase mappings")
    print("  2. Knows 'Senate' ↔ 'Sénat' are semantically related")
    print("  3. Can match and transfer formatting correctly")
    print()
    print("  Example:")
    print("    Source:  'the Senate' (bold)")
    print("    Translation: 'le Sénat'")
    print("    BERT recognizes: 'Senate' ↔ 'Sénat' (from glossary)")
    print("    Result: 'Sénat' gets bold formatting ✓")
    print()

    print("=" * 80)
    print("✅ Glossary Integration Test Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Add your own glossary terms to glossary.json")
    print("  2. Run translations with glossary loaded")
    print("  3. Verify consistency across the document")
    print()


if __name__ == "__main__":
    test_glossary_integration()
