"""
Terminology glossary system for consistent translation.

This module provides a flexible glossary system that supports:
1. Simple term-to-term mappings
2. Context-aware translations (same term, different context)
3. Phrase-level mappings
4. Case-sensitive/insensitive matching
5. Multiple file formats (JSON, CSV, JSONL)

The glossary can be injected into translators to ensure consistent
terminology across the entire document.
"""

import json
import csv
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class GlossaryEntry:
    """A single glossary entry with source and target terms."""

    source: str
    target: str
    context: Optional[str] = None  # Optional context for disambiguation
    case_sensitive: bool = False
    notes: Optional[str] = None
    priority: int = 0  # Higher priority = applied first (for overlapping terms)

    def matches(self, text: str, context_text: Optional[str] = None) -> bool:
        """
        Check if this entry matches the given text and context.

        Args:
            text: Text to match against
            context_text: Optional context for disambiguation

        Returns:
            True if matches, False otherwise
        """
        # Check term match
        if self.case_sensitive:
            term_match = self.source in text
        else:
            term_match = self.source.lower() in text.lower()

        if not term_match:
            return False

        # If entry has context requirement, check context
        if self.context and context_text:
            context_match = self.context.lower() in context_text.lower()
            return context_match

        return True


class TerminologyGlossary:
    """
    Manages terminology glossaries for consistent translation.

    Supports multiple glossary sources and provides methods to:
    - Load glossaries from files (JSON, CSV, JSONL)
    - Apply glossary terms to text before translation (pre-translation marking)
    - Verify glossary compliance after translation
    - Extract glossary context for LLM prompts
    """

    def __init__(self):
        """Initialize empty glossary."""
        self.entries: List[GlossaryEntry] = []
        self._source_to_entries: Dict[str, List[GlossaryEntry]] = defaultdict(list)
        self._compiled = False

    def add_entry(
        self,
        source: str,
        target: str,
        context: Optional[str] = None,
        case_sensitive: bool = False,
        notes: Optional[str] = None,
        priority: int = 0
    ):
        """
        Add a glossary entry.

        Args:
            source: Source term (English)
            target: Target term (French)
            context: Optional context for disambiguation
            case_sensitive: Whether matching should be case-sensitive
            notes: Optional notes about this entry
            priority: Priority level (higher = applied first)
        """
        entry = GlossaryEntry(
            source=source,
            target=target,
            context=context,
            case_sensitive=case_sensitive,
            notes=notes,
            priority=priority
        )
        self.entries.append(entry)
        self._compiled = False

    def load_from_json(self, json_path: str):
        """
        Load glossary from JSON file.

        Expected format:
        {
            "entries": [
                {
                    "source": "Senate",
                    "target": "Sénat",
                    "case_sensitive": true,
                    "priority": 10
                },
                ...
            ]
        }

        Args:
            json_path: Path to JSON file
        """
        logger.info(f"Loading glossary from {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry_dict in data.get("entries", []):
            self.add_entry(
                source=entry_dict["source"],
                target=entry_dict["target"],
                context=entry_dict.get("context"),
                case_sensitive=entry_dict.get("case_sensitive", False),
                notes=entry_dict.get("notes"),
                priority=entry_dict.get("priority", 0)
            )

        logger.info(f"Loaded {len(data.get('entries', []))} entries from {json_path}")

    def load_from_csv(self, csv_path: str, has_header: bool = True):
        """
        Load glossary from CSV file.

        Expected CSV columns:
        source,target,context,case_sensitive,notes,priority

        Minimum required: source,target

        Args:
            csv_path: Path to CSV file
            has_header: Whether CSV has header row
        """
        logger.info(f"Loading glossary from {csv_path}")

        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f) if has_header else csv.reader(f)

            for row in reader:
                if has_header:
                    # DictReader - access by column name
                    source = row.get("source", "").strip()
                    target = row.get("target", "").strip()
                    context = row.get("context", "").strip() or None
                    case_sensitive = row.get("case_sensitive", "").lower() == "true"
                    notes = row.get("notes", "").strip() or None
                    priority = int(row.get("priority", "0") or "0")
                else:
                    # Plain reader - access by index
                    if len(row) < 2:
                        continue
                    source = row[0].strip()
                    target = row[1].strip()
                    context = row[2].strip() if len(row) > 2 and row[2].strip() else None
                    case_sensitive = row[3].lower() == "true" if len(row) > 3 else False
                    notes = row[4].strip() if len(row) > 4 and row[4].strip() else None
                    priority = int(row[5]) if len(row) > 5 else 0

                if source and target:
                    self.add_entry(
                        source=source,
                        target=target,
                        context=context,
                        case_sensitive=case_sensitive,
                        notes=notes,
                        priority=priority
                    )
                    count += 1

        logger.info(f"Loaded {count} entries from {csv_path}")

    def load_from_dict(self, glossary_dict: Dict[str, str]):
        """
        Load glossary from simple dictionary.

        Args:
            glossary_dict: Dict mapping source terms to target terms
        """
        for source, target in glossary_dict.items():
            self.add_entry(source=source, target=target)

        logger.info(f"Loaded {len(glossary_dict)} entries from dictionary")

    def compile(self):
        """
        Compile glossary for efficient lookup.

        This sorts entries by priority and builds lookup indices.
        """
        # Sort by priority (descending) then by length (longer first)
        self.entries.sort(
            key=lambda e: (e.priority, len(e.source)),
            reverse=True
        )

        # Build source lookup index
        self._source_to_entries.clear()
        for entry in self.entries:
            key = entry.source if entry.case_sensitive else entry.source.lower()
            self._source_to_entries[key].append(entry)

        self._compiled = True
        logger.info(f"Compiled glossary with {len(self.entries)} entries")

    def get_matching_entries(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[Tuple[GlossaryEntry, int, int]]:
        """
        Find all glossary entries that appear in the text.

        Args:
            text: Text to search
            context: Optional context for disambiguation

        Returns:
            List of (entry, start_pos, end_pos) tuples, sorted by position
        """
        if not self._compiled:
            self.compile()

        matches = []

        for entry in self.entries:
            # Find all occurrences of this term
            if entry.case_sensitive:
                pattern = re.escape(entry.source)
                flags = 0
            else:
                pattern = re.escape(entry.source)
                flags = re.IGNORECASE

            # Use word boundaries to avoid partial matches
            # e.g., "Senate" shouldn't match "Senator"
            pattern = r'\b' + pattern + r'\b'

            for match in re.finditer(pattern, text, flags=flags):
                # Check context if provided
                if entry.context and context:
                    if entry.context.lower() not in context.lower():
                        continue

                matches.append((entry, match.start(), match.end()))

        # Sort by position
        matches.sort(key=lambda x: x[1])

        # Remove overlapping matches (keep higher priority)
        non_overlapping = []
        used_positions = set()

        for entry, start, end in matches:
            # Check if any position is already used
            if any(pos in used_positions for pos in range(start, end)):
                continue

            # Add this match
            non_overlapping.append((entry, start, end))
            used_positions.update(range(start, end))

        return non_overlapping

    def get_prompt_context(
        self,
        text: Optional[str] = None,
        max_entries: int = 50
    ) -> str:
        """
        Generate context string for LLM prompt with glossary terms.

        Args:
            text: Optional text to find relevant terms for
            max_entries: Maximum number of entries to include

        Returns:
            Formatted string with glossary terms for prompt injection
        """
        if not self._compiled:
            self.compile()

        if text:
            # Get relevant entries that appear in text
            matches = self.get_matching_entries(text)
            relevant_entries = [entry for entry, _, _ in matches]

            # Add high-priority entries even if not in text
            high_priority = [e for e in self.entries if e.priority >= 10]
            for entry in high_priority:
                if entry not in relevant_entries:
                    relevant_entries.append(entry)
        else:
            # No text provided, use all entries (sorted by priority)
            relevant_entries = self.entries

        # Limit to max_entries
        relevant_entries = relevant_entries[:max_entries]

        if not relevant_entries:
            return ""

        # Build formatted string
        lines = ["TERMINOLOGY GLOSSARY (use these exact translations):"]
        lines.append("")

        for entry in relevant_entries:
            line = f"- \"{entry.source}\" → \"{entry.target}\""
            if entry.context:
                line += f" (context: {entry.context})"
            if entry.notes:
                line += f" // {entry.notes}"
            lines.append(line)

        return "\n".join(lines)

    def get_bert_phrase_mappings(self) -> Dict[str, List[str]]:
        """
        Generate phrase mappings dictionary for BERT aligner.

        This converts glossary entries into the format expected by
        PowerPointBERTAligner.phrase_mappings.

        Returns:
            Dict mapping source terms (lowercase) to list of target terms (lowercase)
        """
        if not self._compiled:
            self.compile()

        mappings = defaultdict(list)

        for entry in self.entries:
            # Use lowercase for BERT matching
            source_key = entry.source.lower()
            target_value = entry.target.lower()

            if target_value not in mappings[source_key]:
                mappings[source_key].append(target_value)

        return dict(mappings)

    def verify_translation(
        self,
        source_text: str,
        translated_text: str,
        context: Optional[str] = None
    ) -> Dict:
        """
        Verify that glossary terms were correctly translated.

        Args:
            source_text: Original text
            translated_text: Translated text
            context: Optional context

        Returns:
            Dict with verification results:
            {
                "compliant": bool,
                "violations": [{"entry": GlossaryEntry, "found": str}, ...],
                "correct": [GlossaryEntry, ...]
            }
        """
        matches = self.get_matching_entries(source_text, context)

        violations = []
        correct = []

        for entry, start, end in matches:
            # Check if target term appears in translation
            if entry.case_sensitive:
                found = entry.target in translated_text
            else:
                found = entry.target.lower() in translated_text.lower()

            if found:
                correct.append(entry)
            else:
                violations.append({
                    "entry": entry,
                    "source_term": source_text[start:end],
                    "expected_target": entry.target
                })

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "correct": correct,
            "total_terms": len(matches)
        }

    def save_to_json(self, json_path: str):
        """
        Save glossary to JSON file.

        Args:
            json_path: Path to output JSON file
        """
        data = {
            "entries": [asdict(entry) for entry in self.entries]
        }

        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(self.entries)} entries to {json_path}")

    def __len__(self):
        return len(self.entries)

    def __repr__(self):
        return f"TerminologyGlossary({len(self.entries)} entries)"


def create_sample_glossary(output_path: str = "glossary.json"):
    """
    Create a sample glossary file for Canadian government translation.

    Args:
        output_path: Path to save sample glossary
    """
    glossary = TerminologyGlossary()

    # Canadian government terms
    glossary.add_entry("Senate", "Sénat", case_sensitive=True, priority=10,
                      notes="Canadian Senate (upper house)")
    glossary.add_entry("House of Commons", "Chambre des communes", priority=10)
    glossary.add_entry("Parliament", "Parlement", case_sensitive=True, priority=10)
    glossary.add_entry("federal government", "gouvernement fédéral", priority=8)
    glossary.add_entry("provincial government", "gouvernement provincial", priority=8)
    glossary.add_entry("municipal government", "gouvernement municipal", priority=8)

    # Disability accommodation terms
    glossary.add_entry("invisible disability", "handicap invisible", priority=9)
    glossary.add_entry("accommodation", "mesure d'adaptation",
                      context="disability", priority=9,
                      notes="In disability context, not housing")
    glossary.add_entry("accommodation request", "demande de mesure d'adaptation", priority=9)
    glossary.add_entry("assessment", "évaluation", priority=5)
    glossary.add_entry("wait time", "temps d'attente", priority=5)
    glossary.add_entry("implementation", "mise en œuvre", priority=5)

    # Common government terms
    glossary.add_entry("employee", "employé", priority=3)
    glossary.add_entry("employer", "employeur", priority=3)
    glossary.add_entry("manager", "gestionnaire", priority=3)
    glossary.add_entry("workplace", "milieu de travail", priority=3)

    glossary.save_to_json(output_path)
    print(f"✅ Created sample glossary with {len(glossary)} entries at {output_path}")


def main():
    """Example usage and testing."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "create-sample":
        output = sys.argv[2] if len(sys.argv) > 2 else "glossary.json"
        create_sample_glossary(output)
        return

    # Demo usage
    print("=" * 80)
    print("Terminology Glossary Demo")
    print("=" * 80)

    # Create sample glossary
    glossary = TerminologyGlossary()
    glossary.add_entry("Senate", "Sénat", case_sensitive=True, priority=10)
    glossary.add_entry("invisible disability", "handicap invisible", priority=9)
    glossary.add_entry("accommodation", "mesure d'adaptation", priority=8)
    glossary.compile()

    # Test text
    text = "Employees with an invisible disability may request accommodation from the Senate."

    print(f"\nOriginal text:\n{text}\n")

    # Get prompt context
    print("Prompt context:")
    print(glossary.get_prompt_context(text))
    print()

    # Get BERT phrase mappings
    print("BERT phrase mappings:")
    bert_mappings = glossary.get_bert_phrase_mappings()
    for src, tgts in bert_mappings.items():
        print(f"  '{src}' → {tgts}")
    print()

    # Get matching entries
    matches = glossary.get_matching_entries(text)
    print(f"Found {len(matches)} glossary terms in text:")
    for entry, start, end in matches:
        print(f"  - '{text[start:end]}' → '{entry.target}' (priority: {entry.priority})")
    print()

    # Test verification
    good_translation = "Les employés ayant un handicap invisible peuvent demander une mesure d'adaptation au Sénat."
    bad_translation = "Les employés avec une disability invisible peuvent demander accommodation du Senate."

    print("Verifying GOOD translation:")
    result = glossary.verify_translation(text, good_translation)
    print(f"  Compliant: {result['compliant']}")
    print(f"  Correct: {len(result['correct'])}/{result['total_terms']}")
    print()

    print("Verifying BAD translation:")
    result = glossary.verify_translation(text, bad_translation)
    print(f"  Compliant: {result['compliant']}")
    print(f"  Violations: {len(result['violations'])}")
    for v in result['violations']:
        print(f"    - Expected '{v['expected_target']}' for '{v['source_term']}'")


if __name__ == "__main__":
    main()
