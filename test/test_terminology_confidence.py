#!/usr/bin/env python
"""
Quick sanity check for terminology confidence wiring.

Verifies that:
- The system prompt shows the same confidence threshold as config.terminology_min_confidence
- The local filtering in memory._parse_terminology_entries uses the same threshold
"""

from config import Config
from prompts import build_terminology_system_prompt
from memory import _parse_terminology_entries, TerminologyEntry


def extract_threshold_line(prompt: str) -> str:
    """Return the line that contains the confidence threshold text."""
    for line in prompt.splitlines():
        if "Only keep entries with confidence >=" in line:
            return line.strip()
    return ""


def demo_prompt_threshold():
    cfg = Config()
    min_conf = cfg.terminology_min_confidence
    prompt = build_terminology_system_prompt(min_conf)
    line = extract_threshold_line(prompt)
    print("Config.terminology_min_confidence:", min_conf)
    print("Prompt threshold line:", line)


def demo_filtering():
    raw = [
        {"eng": "Bryer", "zh": "布赖尔", "type": "person", "confidence": 0.8, "evidence_ids": [20]},
        {"eng": "Chris", "zh": "克里斯", "type": "person", "confidence": 0.5, "evidence_ids": [2]},
    ]

    print("\nFiltering with min_confidence = 0.6:")
    parsed_high = _parse_terminology_entries(raw, min_confidence=0.6)
    for e in parsed_high:
        print("  kept:", TerminologyEntry.to_dict(e))

    print("\nFiltering with min_confidence = 0.4:")
    parsed_low = _parse_terminology_entries(raw, min_confidence=0.4)
    for e in parsed_low:
        print("  kept:", TerminologyEntry.to_dict(e))


if __name__ == "__main__":
    demo_prompt_threshold()
    demo_filtering()

