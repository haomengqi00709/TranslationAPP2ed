"""
Phrase-Aware BERT Aligner for PowerPoint Translation
Adapted from phrase_aware_bert_aligner.py with PowerPoint-specific enhancements
"""

import torch
import numpy as np
import logging
from transformers import AutoModel, AutoTokenizer
from typing import List, Tuple, Dict, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from glossary import TerminologyGlossary

logger = logging.getLogger(__name__)


class PowerPointBERTAligner:
    """BERT aligner adapted for PowerPoint with formatting preservation."""

    def __init__(
        self,
        model_name: str = "bert-base-multilingual-cased",
        device: str = "cpu",
        max_phrase_length: int = 4,
        similarity_threshold: float = 0.3,
        glossary: Optional['TerminologyGlossary'] = None
    ):
        """
        Initialize PowerPoint BERT aligner.

        Args:
            model_name: BERT model name
            device: Device to use (cuda, mps, cpu)
            max_phrase_length: Maximum phrase length for alignment
            similarity_threshold: Minimum similarity threshold for alignment
            glossary: Optional terminology glossary for enhanced alignment
        """
        self.device = device
        self.max_phrase_length = max_phrase_length
        self.similarity_threshold = similarity_threshold

        logger.info(f"Loading BERT model {model_name} on device {device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device)
        self.model.eval()

        # Enhanced semantic mappings for phrases
        self.phrase_mappings = {
            # Common English-French phrases
            'invisible': ['invisible', 'caché', 'masqué'],
            'disability': ['handicap', 'invalidité', 'incapacité'],
            'employees': ['employés', 'salariés', 'travailleurs'],
            'with': ['avec', 'ayant', 'portant'],
            'more likely': ['plus susceptibles', 'plus probable'],
            'to be': ['d\'être', 'être'],
            'invisible disability': ['handicap invisible'],
            # Add more mappings as needed
        }

        # Merge glossary mappings if provided
        if glossary:
            glossary_mappings = glossary.get_bert_phrase_mappings()
            for source, targets in glossary_mappings.items():
                if source in self.phrase_mappings:
                    # Merge with existing mappings
                    for target in targets:
                        if target not in self.phrase_mappings[source]:
                            self.phrase_mappings[source].append(target)
                else:
                    # Add new mapping
                    self.phrase_mappings[source] = targets

            logger.info(f"Loaded {len(glossary_mappings)} glossary mappings into BERT aligner")

        logger.info("BERT aligner initialized successfully")

    def simple_tokenize(self, text: str) -> List[str]:
        """
        Simple word-level tokenization that preserves spaces.

        Returns words with their trailing spaces included where appropriate.
        This ensures proper reconstruction of the original text.
        """
        # Split on whitespace but keep track of word boundaries
        words = []
        current_word = ""

        for char in text:
            if char in ' \t\n\r':
                if current_word:
                    # Add word with trailing space
                    words.append(current_word)
                    current_word = ""
                # Continue accumulating spaces
                if words:
                    words[-1] = words[-1] + char
            else:
                current_word += char

        # Add final word if exists
        if current_word:
            words.append(current_word)

        return words

    def get_phrase_embeddings(
        self, text: str
    ) -> Tuple[List[torch.Tensor], List[str], List[Tuple[int, int]]]:
        """
        Get BERT embeddings for words and phrases.

        Returns:
            embeddings: List of embeddings for words and phrases
            phrases: List of phrase strings
            phrase_spans: List of (start_idx, end_idx) for each phrase
        """
        words = self.simple_tokenize(text)
        embeddings = []
        phrases = []
        phrase_spans = []

        # Get embeddings for individual words
        for i, word in enumerate(words):
            # Strip spaces for BERT encoding but keep original word for reconstruction
            word_stripped = word.strip()
            if not word_stripped:
                continue

            encoded = self.tokenizer(word_stripped, return_tensors="pt", truncation=True, padding=True)
            input_ids = encoded["input_ids"].to(self.device)

            with torch.no_grad():
                outputs = self.model(input_ids=input_ids)
                word_embedding = outputs.last_hidden_state[0, 0, :]
                embeddings.append(word_embedding)
                phrases.append(word)  # Keep original with spaces
                phrase_spans.append((i, i))

        # Get embeddings for phrases (2 to max_phrase_length words)
        for length in range(2, min(self.max_phrase_length + 1, len(words) + 1)):
            for start in range(len(words) - length + 1):
                phrase_words = words[start:start + length]
                # Join preserving original spacing
                phrase_text = ''.join(phrase_words).strip()

                if not phrase_text:
                    continue

                encoded = self.tokenizer(phrase_text, return_tensors="pt", truncation=True, padding=True)
                input_ids = encoded["input_ids"].to(self.device)

                with torch.no_grad():
                    outputs = self.model(input_ids=input_ids)
                    phrase_embedding = outputs.last_hidden_state[0, 0, :]
                    embeddings.append(phrase_embedding)
                    phrases.append(''.join(phrase_words))  # Keep original spacing in phrase list
                    phrase_spans.append((start, start + length - 1))

        return embeddings, phrases, phrase_spans

    def compute_phrase_similarity(
        self, src_phrase: str, tgt_phrase: str,
        src_embedding: torch.Tensor, tgt_embedding: torch.Tensor
    ) -> float:
        """Compute semantic similarity between source and target phrases."""
        # 1. BERT embedding similarity
        bert_sim = torch.cosine_similarity(
            src_embedding.unsqueeze(0), tgt_embedding.unsqueeze(0)
        ).item()

        # 2. Semantic mapping bonus
        semantic_bonus = 0.0
        src_lower = src_phrase.lower()
        tgt_lower = tgt_phrase.lower()

        # Check phrase mappings
        if src_lower in self.phrase_mappings:
            if tgt_lower in self.phrase_mappings[src_lower]:
                semantic_bonus = 0.4

        # Check reverse mapping
        for key, values in self.phrase_mappings.items():
            if src_lower in values and tgt_lower == key:
                semantic_bonus = 0.4

        # 3. Exact match bonus
        if src_lower == tgt_lower:
            semantic_bonus = 0.5

        # 4. Length similarity bonus
        src_words = len(src_phrase.split())
        tgt_words = len(tgt_phrase.split())
        length_sim = min(src_words, tgt_words) / max(src_words, tgt_words) if max(src_words, tgt_words) > 0 else 0

        # 5. Character similarity bonus
        char_sim = self._compute_character_similarity(src_phrase, tgt_phrase)

        # Combined score
        final_score = (bert_sim * 0.3) + (semantic_bonus * 0.4) + (length_sim * 0.15) + (char_sim * 0.15)

        return final_score

    def _compute_character_similarity(self, phrase1: str, phrase2: str) -> float:
        """Compute character-level similarity."""
        chars1 = set(phrase1.lower().replace(' ', ''))
        chars2 = set(phrase2.lower().replace(' ', ''))

        if not chars1 or not chars2:
            return 0.0

        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)

        return intersection / union if union > 0 else 0.0

    def find_optimal_alignments(
        self, src_text: str, tgt_text: str, runs: Optional[List[Dict]] = None
    ) -> Tuple[List[Tuple[int, int]], List[str], List[str], List[Tuple[int, int]], List[Tuple[int, int]], np.ndarray]:
        """
        Find optimal phrase alignments using greedy approach.

        Args:
            src_text: Source text
            tgt_text: Target text
            runs: Optional list of source runs (used to determine if phrase has special formatting)

        Returns:
            alignments: List of (src_phrase_idx, tgt_phrase_idx) tuples
            src_phrases: List of source phrases
            tgt_phrases: List of target phrases
            src_spans: List of (start, end) word positions for source phrases
            tgt_spans: List of (start, end) word positions for target phrases
            similarity_matrix: Full similarity matrix (for debugging)
        """
        # Get phrase embeddings
        src_embeddings, src_phrases, src_spans = self.get_phrase_embeddings(src_text)
        tgt_embeddings, tgt_phrases, tgt_spans = self.get_phrase_embeddings(tgt_text)

        # Build map to check if source phrase has special formatting (bold or color)
        phrase_is_formatted = {}
        if runs:
            src_words = self.simple_tokenize(src_text)
            src_char_spans = self._compute_char_spans(src_text, src_words)
            word_to_run = self._map_words_to_runs(src_text, src_words, src_char_spans, runs)

            for phrase_idx, (start, end) in enumerate(src_spans):
                # Check if any word in this phrase has bold or non-default formatting
                is_formatted = False
                for word_idx in range(start, end + 1):
                    if word_idx in word_to_run:
                        run = runs[word_to_run[word_idx]]
                        if run.get("bold") or (run.get("color") and not run.get("color", "").startswith("theme:BACKGROUND")):
                            is_formatted = True
                            break
                phrase_is_formatted[phrase_idx] = is_formatted

        # Compute similarity matrix
        similarity_matrix = np.zeros((len(src_phrases), len(tgt_phrases)))

        for i, src_phrase in enumerate(src_phrases):
            for j, tgt_phrase in enumerate(tgt_phrases):
                similarity = self.compute_phrase_similarity(
                    src_phrase, tgt_phrase, src_embeddings[i], tgt_embeddings[j]
                )
                similarity_matrix[i, j] = similarity

        # Find optimal alignments using greedy approach with overlap prevention
        alignments = []
        used_src_positions = set()
        used_tgt_positions = set()

        # Sort by similarity score (highest first)
        all_pairs = []
        for i in range(len(src_phrases)):
            for j in range(len(tgt_phrases)):
                all_pairs.append((similarity_matrix[i, j], i, j))

        all_pairs.sort(reverse=True)

        # Greedy assignment with overlap prevention
        for score, src_idx, tgt_idx in all_pairs:
            # Use dynamic threshold: higher for formatted text (bold/color)
            threshold = self.similarity_threshold
            if phrase_is_formatted.get(src_idx, False):
                # Require 0.5+ similarity for formatted text (vs 0.3 for normal text)
                threshold = max(0.4, self.similarity_threshold)
                logger.debug(f"Formatted phrase '{src_phrases[src_idx].strip()}' requires threshold {threshold}")

            if score < threshold:
                continue

            src_start, src_end = src_spans[src_idx]
            tgt_start, tgt_end = tgt_spans[tgt_idx]

            # Check for overlaps
            src_overlap = any(pos in used_src_positions for pos in range(src_start, src_end + 1))
            tgt_overlap = any(pos in used_tgt_positions for pos in range(tgt_start, tgt_end + 1))

            if not src_overlap and not tgt_overlap:
                alignments.append((src_idx, tgt_idx))
                used_src_positions.update(range(src_start, src_end + 1))
                used_tgt_positions.update(range(tgt_start, tgt_end + 1))

        # Sort alignments by source position
        alignments.sort(key=lambda x: src_spans[x[0]][0])

        return alignments, src_phrases, tgt_phrases, src_spans, tgt_spans, similarity_matrix

    def align_paragraph_runs(
        self, src_text: str, tgt_text: str, runs: List[Dict]
    ) -> Tuple[List[Dict], Optional[Dict]]:
        """
        Align paragraph and redistribute formatting from source runs to target text.

        Args:
            src_text: Source (English) paragraph text
            tgt_text: Target (French) paragraph text
            runs: List of source runs with formatting metadata

        Returns:
            Tuple of (target_runs, debug_info)
            - target_runs: List of target runs with redistributed formatting
            - debug_info: Dictionary with alignment details for debugging (optional)
        """
        if not src_text.strip() or not tgt_text.strip():
            logger.warning("Empty source or target text, returning default run")
            return [{
                "text": tgt_text,
                "bold": False,
                "italic": False,
                "underline": False,
                "font": None,
                "size": None,
                "color": None,
                "superscript": False,
                "subscript": False,
                "hyperlink": None
            }], None

        # SPECIAL CASE: If there's only ONE source run, just apply its formatting to entire target
        if len(runs) == 1:
            logger.debug(f"Single source run detected, applying uniform formatting")
            debug_info = {
                "alignment_type": "single_run",
                "phrase_alignments": []
            }
            return [{
                "text": tgt_text,
                "bold": runs[0].get("bold", False),
                "italic": runs[0].get("italic", False),
                "underline": runs[0].get("underline", False),
                "font": runs[0].get("font"),
                "size": runs[0].get("size"),
                "color": runs[0].get("color"),
                "superscript": runs[0].get("superscript", False),
                "subscript": runs[0].get("subscript", False),
                "hyperlink": runs[0].get("hyperlink") or runs[0].get("url")
            }], debug_info

        # Get phrase alignments (pass runs to enable dynamic thresholding for formatted text)
        alignments, src_phrases, tgt_phrases, src_spans, tgt_spans, similarity_matrix = \
            self.find_optimal_alignments(src_text, tgt_text, runs)

        # Get word-level tokens
        src_words = self.simple_tokenize(src_text)
        tgt_words = self.simple_tokenize(tgt_text)

        # Compute character spans for target words
        tgt_char_spans = self._compute_char_spans(tgt_text, tgt_words)

        # Build mapping from source words to runs
        src_char_spans = self._compute_char_spans(src_text, src_words)
        word_to_run = self._map_words_to_runs(src_text, src_words, src_char_spans, runs)

        # Map target words to source runs via alignment
        tgt_word_to_run = {}
        for src_phrase_idx, tgt_phrase_idx in alignments:
            src_start, src_end = src_spans[src_phrase_idx]
            tgt_start, tgt_end = tgt_spans[tgt_phrase_idx]

            # Find which run covers the source phrase
            for src_word_idx in range(src_start, src_end + 1):
                if src_word_idx in word_to_run:
                    run_idx = word_to_run[src_word_idx]
                    # Map all target words in this alignment to the same run
                    for tgt_word_idx in range(tgt_start, tgt_end + 1):
                        if tgt_word_idx not in tgt_word_to_run:
                            tgt_word_to_run[tgt_word_idx] = run_idx

        # Create target runs by grouping consecutive words with same formatting
        target_runs = self._create_target_runs(
            tgt_text, tgt_words, tgt_char_spans, tgt_word_to_run, runs
        )

        # Build debug info with detailed phrase alignments
        debug_info = {
            "alignment_type": "multi_run",
            "source_words": [w.strip() for w in src_words],
            "target_words": [w.strip() for w in tgt_words],
            "phrase_alignments": []
        }

        # Add detailed alignment information
        for src_phrase_idx, tgt_phrase_idx in alignments:
            similarity = similarity_matrix[src_phrase_idx, tgt_phrase_idx]
            src_phrase = src_phrases[src_phrase_idx].strip()
            tgt_phrase = tgt_phrases[tgt_phrase_idx].strip()
            src_start, src_end = src_spans[src_phrase_idx]
            tgt_start, tgt_end = tgt_spans[tgt_phrase_idx]

            # Find which run this source phrase belongs to
            run_idx = None
            for src_word_idx in range(src_start, src_end + 1):
                if src_word_idx in word_to_run:
                    run_idx = word_to_run[src_word_idx]
                    break

            alignment_info = {
                "source_phrase": src_phrase,
                "target_phrase": tgt_phrase,
                "similarity": round(float(similarity), 4),
                "source_word_indices": list(range(src_start, src_end + 1)),
                "target_word_indices": list(range(tgt_start, tgt_end + 1)),
                "source_run_index": run_idx,
                "source_formatting": {
                    "bold": runs[run_idx].get("bold", False) if run_idx is not None and run_idx < len(runs) else None,
                    "color": runs[run_idx].get("color") if run_idx is not None and run_idx < len(runs) else None
                }
            }
            debug_info["phrase_alignments"].append(alignment_info)

        # Add top alternative matches for debugging (top 5 rejected matches)
        rejected_matches = []
        for score, src_idx, tgt_idx in sorted([(similarity_matrix[i, j], i, j)
                                                 for i in range(len(src_phrases))
                                                 for j in range(len(tgt_phrases))], reverse=True)[:20]:
            if (src_idx, tgt_idx) not in alignments and score >= 0.2:  # Show near-misses
                rejected_matches.append({
                    "source_phrase": src_phrases[src_idx].strip(),
                    "target_phrase": tgt_phrases[tgt_idx].strip(),
                    "similarity": round(float(score), 4),
                    "reason": "below_threshold" if score < self.similarity_threshold else "overlap"
                })
                if len(rejected_matches) >= 10:
                    break

        debug_info["rejected_matches"] = rejected_matches

        return target_runs, debug_info

    def _compute_char_spans(self, text: str, words: List[str]) -> List[Tuple[int, int]]:
        """
        Compute character spans for words in text.

        Words may include trailing spaces, so we track the actual content span
        (excluding trailing whitespace) for proper alignment.
        """
        spans = []
        pos = 0

        for word in words:
            # Find the word in the text starting from current position
            idx = text.find(word, pos)
            if idx < 0:
                # Fallback: just use current position
                word_stripped = word.strip()
                if word_stripped:
                    idx = text.find(word_stripped, pos)
                    if idx >= 0:
                        spans.append((idx, idx + len(word_stripped)))
                        pos = idx + len(word)
                    else:
                        spans.append((pos, pos))
                else:
                    spans.append((pos, pos))
            else:
                # Span includes the full word with trailing spaces
                spans.append((idx, idx + len(word)))
                pos = idx + len(word)

        return spans

    def _map_words_to_runs(
        self, text: str, words: List[str], char_spans: List[Tuple[int, int]], runs: List[Dict]
    ) -> Dict[int, int]:
        """Map word indices to run indices."""
        word_to_run = {}

        # Compute character spans for runs
        run_char_spans = []
        pos = 0
        for run in runs:
            run_text = run.get("text", "")
            start = pos
            end = pos + len(run_text)
            run_char_spans.append((start, end))
            pos = end

        # Map each word to a run
        for word_idx, (word_start, word_end) in enumerate(char_spans):
            for run_idx, (run_start, run_end) in enumerate(run_char_spans):
                # Check if word overlaps with run
                if word_start < run_end and word_end > run_start:
                    word_to_run[word_idx] = run_idx
                    break

        return word_to_run

    def _create_target_runs(
        self, text: str, words: List[str], char_spans: List[Tuple[int, int]],
        word_to_run: Dict[int, int], runs: List[Dict]
    ) -> List[Dict]:
        """Create target runs by grouping words with same formatting."""
        if not words:
            # Use first run's formatting as default
            default_format = runs[0] if runs else {}
            return [self._create_run(text, default_format)]

        # Find the most common (default) run formatting
        # This is the formatting we'll use for unaligned words
        default_run_idx = self._find_default_run(runs)
        default_format = runs[default_run_idx] if default_run_idx < len(runs) else runs[0] if runs else {}

        target_runs = []
        current_run_idx = None
        current_start = 0

        for word_idx in range(len(words)):
            # Get run index, defaulting to the most common run if no alignment
            run_idx = word_to_run.get(word_idx, default_run_idx)

            # Start new run if formatting changes or this is first word
            if run_idx != current_run_idx:
                # Save previous run
                if word_idx > 0:
                    char_start = char_spans[current_start][0]
                    char_end = char_spans[word_idx - 1][1]
                    run_text = text[char_start:char_end]

                    if current_run_idx is not None and current_run_idx < len(runs):
                        run_format = runs[current_run_idx]
                    else:
                        run_format = default_format

                    target_runs.append(self._create_run(run_text, run_format))

                current_run_idx = run_idx
                current_start = word_idx

        # Add final run
        if current_start < len(words):
            char_start = char_spans[current_start][0]
            char_end = char_spans[-1][1]
            run_text = text[char_start:char_end]

            if current_run_idx is not None and current_run_idx < len(runs):
                run_format = runs[current_run_idx]
            else:
                run_format = default_format

            target_runs.append(self._create_run(run_text, run_format))

        # Merge consecutive runs with identical formatting to reduce fragmentation
        merged_runs = self._merge_identical_runs(target_runs)

        return merged_runs

    def _find_default_run(self, runs: List[Dict]) -> int:
        """
        Find the most appropriate default run (usually the longest non-bold run).
        This represents the "normal" text formatting.
        """
        if not runs:
            return 0

        # Find the longest run that is NOT bold (likely the body text)
        normal_runs = [(i, len(run.get("text", ""))) for i, run in enumerate(runs) if not run.get("bold", False)]

        if normal_runs:
            # Return index of longest normal run
            return max(normal_runs, key=lambda x: x[1])[0]

        # If all runs are bold, just use the longest one
        return max(enumerate(runs), key=lambda x: len(x[1].get("text", "")))[0]

    def _merge_identical_runs(self, runs: List[Dict]) -> List[Dict]:
        """Merge consecutive runs that have identical formatting."""
        if not runs:
            return runs

        merged = [runs[0].copy()]

        for run in runs[1:]:
            last = merged[-1]
            # Check if formatting is identical
            if (last["bold"] == run["bold"] and
                last["italic"] == run["italic"] and
                last["underline"] == run["underline"] and
                last["font"] == run["font"] and
                last["size"] == run["size"] and
                last["color"] == run["color"] and
                last["superscript"] == run["superscript"] and
                last["subscript"] == run["subscript"] and
                last["hyperlink"] == run["hyperlink"]):
                # Merge text into last run
                last["text"] += run["text"]
            else:
                # Different formatting, add as new run
                merged.append(run.copy())

        return merged

    def _create_run(self, text: str, format_dict: Dict) -> Dict:
        """Create a run dictionary with formatting."""
        return {
            "text": text,
            "bold": format_dict.get("bold", False),
            "italic": format_dict.get("italic", False),
            "underline": format_dict.get("underline", False),
            "font": format_dict.get("font"),
            "size": format_dict.get("size"),
            "color": format_dict.get("color"),
            "superscript": format_dict.get("superscript", False),
            "subscript": format_dict.get("subscript", False),
            "hyperlink": format_dict.get("hyperlink") or format_dict.get("url")
        }
