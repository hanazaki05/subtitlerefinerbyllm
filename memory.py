"""
Global memory management for subtitle refinement.

Maintains terminology, style notes, and context across chunks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
import re

from pairs import SubtitlePair
from utils import estimate_tokens


@dataclass
class GlobalMemory:
    """
    Global memory structure for cross-chunk information.

    Attributes:
        glossary: List of terminology entries (people, places, organizations)
        style_notes: Style and tone guidelines
        summary: Brief context or plot summary
    """

    glossary: List[Dict[str, str]] = field(default_factory=list)
    style_notes: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "glossary": self.glossary,
            "style_notes": self.style_notes,
            "summary": self.summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalMemory':
        """Create GlobalMemory from dictionary."""
        return cls(
            glossary=data.get("glossary", []),
            style_notes=data.get("style_notes", ""),
            summary=data.get("summary", "")
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def init_global_memory() -> GlobalMemory:
    """
    Initialize empty global memory.

    Returns:
        New GlobalMemory instance
    """
    return GlobalMemory(
        glossary=[],
        style_notes="",
        summary=""
    )


def extract_terminology_from_chunk(pairs: List[SubtitlePair]) -> List[Dict[str, str]]:
    """
    Extract potential terminology from a chunk of subtitle pairs.

    Uses simple heuristics:
    - Capitalized words in English that might be proper nouns
    - Their corresponding positions in Chinese text

    Args:
        pairs: List of SubtitlePair objects

    Returns:
        List of terminology entries
    """
    terminology = []

    # Pattern to find capitalized words (potential proper nouns)
    # Look for words that start with capital letter and are 2+ characters
    proper_noun_pattern = re.compile(r'\b[A-Z][a-z]{1,}(?:\s+[A-Z][a-z]+)*\b')

    # Common words to exclude (not proper nouns)
    exclude_words = {
        "I", "I'm", "I've", "I'll", "The", "This", "That", "These", "Those",
        "What", "When", "Where", "Why", "How", "Who", "Which",
        "Yes", "No", "Okay", "OK", "Well", "So"
    }

    seen_terms = set()

    for pair in pairs:
        # Find capitalized words in English
        matches = proper_noun_pattern.findall(pair.eng)

        for match in matches:
            # Skip if in exclude list
            if match in exclude_words:
                continue

            # Skip if we've already seen this term
            if match in seen_terms:
                continue

            # For now, we don't have a good way to automatically extract
            # the Chinese translation, so we just note the English term
            # In a real system, you might use alignment or ask the LLM
            terminology.append({
                "eng": match,
                "zh": "",  # Would need alignment or LLM extraction
                "type": "unknown"
            })

            seen_terms.add(match)

    return terminology


def update_global_memory(
    memory: GlobalMemory,
    corrected_pairs: List[SubtitlePair]
) -> GlobalMemory:
    """
    Update global memory with information from corrected pairs.

    Args:
        memory: Current GlobalMemory object
        corrected_pairs: List of corrected SubtitlePair objects

    Returns:
        Updated GlobalMemory object
    """
    # Extract new terminology from this chunk
    new_terms = extract_terminology_from_chunk(corrected_pairs)

    # Get existing English terms for deduplication
    existing_terms = {entry.get("eng", "") for entry in memory.glossary}

    # Add only new terms
    for term in new_terms:
        if term["eng"] and term["eng"] not in existing_terms:
            memory.glossary.append(term)
            existing_terms.add(term["eng"])

    # Limit glossary size to prevent unbounded growth
    # Keep most recent entries if we exceed limit
    max_glossary_entries = 100
    if len(memory.glossary) > max_glossary_entries:
        memory.glossary = memory.glossary[-max_glossary_entries:]

    return memory


def estimate_memory_tokens(memory: GlobalMemory, model_name: str = "gpt-4") -> int:
    """
    Estimate token count for global memory.

    Args:
        memory: GlobalMemory object
        model_name: Model name for token estimation

    Returns:
        Estimated token count
    """
    # Convert to the format that will be included in prompt
    from prompts import build_memory_section

    memory_text = build_memory_section(memory)
    return estimate_tokens(memory_text, model_name)


def compress_memory_simple(memory: GlobalMemory, max_entries: int = 50) -> GlobalMemory:
    """
    Simple memory compression by limiting glossary size.

    Args:
        memory: GlobalMemory to compress
        max_entries: Maximum number of glossary entries to keep

    Returns:
        Compressed GlobalMemory
    """
    compressed = GlobalMemory(
        glossary=memory.glossary[-max_entries:] if memory.glossary else [],
        style_notes=memory.style_notes[:500] if memory.style_notes else "",  # Truncate to 500 chars
        summary=memory.summary[:500] if memory.summary else ""
    )

    return compressed


def merge_glossary_entries(glossary: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Merge duplicate glossary entries.

    Args:
        glossary: List of glossary entries

    Returns:
        Deduplicated glossary
    """
    seen = {}
    merged = []

    for entry in glossary:
        eng = entry.get("eng", "")
        if not eng:
            continue

        if eng not in seen:
            seen[eng] = entry
            merged.append(entry)
        else:
            # Update existing entry if new one has more info
            existing = seen[eng]
            if not existing.get("zh") and entry.get("zh"):
                existing["zh"] = entry["zh"]
            if not existing.get("type") and entry.get("type"):
                existing["type"] = entry["type"]

    return merged


def validate_memory_structure(memory_dict: Dict[str, Any]) -> bool:
    """
    Validate that memory dictionary has correct structure.

    Args:
        memory_dict: Dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(memory_dict, dict):
        return False

    # Check required fields exist
    if "glossary" not in memory_dict:
        return False

    # Validate glossary is a list
    if not isinstance(memory_dict["glossary"], list):
        return False

    # Validate glossary entries
    for entry in memory_dict["glossary"]:
        if not isinstance(entry, dict):
            return False
        if "eng" not in entry or "zh" not in entry:
            return False

    return True
