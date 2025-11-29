#!/usr/bin/env python3
"""
Test script for OpenAI SDK-based subtitle refinement.

This script demonstrates how to use the OpenAI SDK implementation
instead of the HTTP POST approach.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_sdk import load_config_sdk
from llm_client_sdk import (
    test_api_connection_sdk,
    refine_chunk_sdk,
    LLMAPIError
)
from pairs import SubtitlePair
from memory import GlobalMemory


def test_connection():
    """Test API connection using OpenAI SDK."""
    print("=" * 60)
    print("Testing API Connection with OpenAI SDK")
    print("=" * 60)

    config = load_config_sdk(verbose=True)

    print(f"\nUsing model: {config.main_model.name}")
    print(f"API base URL: {config.api_base_url}")
    print(f"API key: {config.api_key[:20]}...\n")

    print("Testing connection...")
    success = test_api_connection_sdk(config)

    if success:
        print("✓ API connection test successful!")
        return True
    else:
        print("✗ API connection test failed!")
        return False


def test_simple_refinement():
    """Test simple subtitle refinement with a few pairs."""
    print("\n" + "=" * 60)
    print("Testing Simple Subtitle Refinement")
    print("=" * 60)

    # Create test subtitle pairs
    test_pairs = [
        SubtitlePair(
            id=0,
            eng="hello world",
            chinese="你好世界"
        ),
        SubtitlePair(
            id=1,
            eng="This is a test",
            chinese="这是一个测试"
        ),
        SubtitlePair(
            id=2,
            eng="goodbye!",
            chinese="再见！"
        )
    ]

    print(f"\nTest pairs ({len(test_pairs)}):")
    for pair in test_pairs:
        print(f"  [{pair.id}] {pair.eng} / {pair.chinese}")

    # Create minimal global memory
    global_memory = GlobalMemory()

    # Load config
    config = load_config_sdk(
        verbose=True,
        model_name="gpt-4o-mini"  # Use cheaper model for testing
    )

    print(f"\nUsing model: {config.main_model.name}")
    print("Sending refinement request...\n")

    try:
        # Call refinement function
        corrected_pairs, usage, response_text = refine_chunk_sdk(
            test_pairs,
            global_memory,
            config
        )

        print("✓ Refinement successful!")
        print(f"\nToken usage:")
        print(f"  Prompt tokens: {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens: {usage.total_tokens}")
        if usage.reasoning_tokens > 0:
            print(f"  Reasoning tokens: {usage.reasoning_tokens}")

        print(f"\nRefined pairs ({len(corrected_pairs)}):")
        for pair in corrected_pairs:
            print(f"  [{pair.id}] {pair.eng} / {pair.chinese}")

        print("\nChanges:")
        for i, (original, corrected) in enumerate(zip(test_pairs, corrected_pairs)):
            if original.eng != corrected.eng:
                print(f"  [ENG {i}] {original.eng} → {corrected.eng}")
            if original.chinese != corrected.chinese:
                print(f"  [CHN {i}] {original.chinese} → {corrected.chinese}")

        return True

    except LLMAPIError as e:
        print(f"✗ Refinement failed: {str(e)}")
        return False


def test_from_file():
    """Test refinement with actual subtitle file."""
    print("\n" + "=" * 60)
    print("Testing Refinement from File")
    print("=" * 60)

    # Check if test_input.ass exists
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_input = os.path.join(parent_dir, "example_input.ass")

    if not os.path.exists(test_input):
        print(f"Test file not found: {test_input}")
        print("Skipping file-based test.")
        return False

    print(f"\nReading from: {test_input}")

    # Import ASS parser
    from ass_parser import parse_ass_file, build_pairs_from_ass_lines

    # Parse file
    header, lines = parse_ass_file(test_input)
    pairs = build_pairs_from_ass_lines(lines)

    print(f"Found {len(pairs)} subtitle pairs")

    # Take first 5 pairs for testing
    test_pairs = pairs[:5]
    print(f"\nTesting with first {len(test_pairs)} pairs:")
    for pair in test_pairs:
        print(f"  [{pair.id}] {pair.eng[:40]}... / {pair.chinese[:40]}...")

    # Create minimal global memory
    global_memory = GlobalMemory()

    # Load config
    config = load_config_sdk(
        verbose=True,
        model_name="gpt-4o-mini"  # Use cheaper model for testing
    )

    print(f"\nUsing model: {config.main_model.name}")
    print("Sending refinement request...\n")

    try:
        # Call refinement function
        corrected_pairs, usage, response_text = refine_chunk_sdk(
            test_pairs,
            global_memory,
            config
        )

        print("✓ Refinement successful!")
        print(f"\nToken usage:")
        print(f"  Prompt tokens: {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens: {usage.total_tokens}")

        print(f"\nRefined {len(corrected_pairs)} pairs")

        # Show first corrected pair as example
        if corrected_pairs:
            print("\nExample refined pair:")
            pair = corrected_pairs[0]
            print(f"  [ENG] {pair.eng}")
            print(f"  [CHN] {pair.chinese}")

        return True

    except LLMAPIError as e:
        print(f"✗ Refinement failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OpenAI SDK Test Suite")
    print("=" * 60)
    print("\nThis script tests the OpenAI SDK-based implementation")
    print("instead of the HTTP POST approach.\n")

    results = []

    # Test 1: API Connection
    results.append(("API Connection", test_connection()))

    # Test 2: Simple Refinement
    if results[0][1]:  # Only if connection test passed
        results.append(("Simple Refinement", test_simple_refinement()))

        # Test 3: File-based Refinement
        results.append(("File Refinement", test_from_file()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)