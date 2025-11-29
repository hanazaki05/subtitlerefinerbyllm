#!/usr/bin/env python3
"""
Test script for OpenAI SDK streaming API.

This script demonstrates the streaming API implementation,
showing real-time token generation.
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_sdk import load_config_sdk
from llm_client_sdk import (
    refine_chunk_sdk_streaming,
    call_openai_api_sdk_streaming,
    LLMAPIError
)
from pairs import SubtitlePair
from memory import GlobalMemory


def test_streaming_simple():
    """Test simple streaming API call."""
    print("=" * 60)
    print("Testing Streaming API")
    print("=" * 60)

    config = load_config_sdk(model_name="gpt-4o-mini")

    print(f"\nUsing model: {config.main_model.name}")
    print("Testing streaming with simple request...\n")

    messages = [
        {"role": "user", "content": "Count from 1 to 10, one number per line."}
    ]

    # Define callback to print chunks in real-time
    def print_chunk(chunk: str):
        print(chunk, end="", flush=True)

    try:
        print("Streaming output:")
        print("-" * 40)

        response_text, usage = call_openai_api_sdk_streaming(
            messages,
            config,
            model_settings=config.main_model,
            chunk_callback=print_chunk
        )

        print("\n" + "-" * 40)
        print(f"\n✓ Streaming successful!")
        print(f"\nToken usage:")
        print(f"  Prompt tokens: {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens: {usage.total_tokens}")

        return True

    except LLMAPIError as e:
        print(f"\n✗ Streaming failed: {str(e)}")
        return False


def test_streaming_subtitle_refinement():
    """Test subtitle refinement with streaming."""
    print("\n" + "=" * 60)
    print("Testing Streaming Subtitle Refinement")
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
        model_name="gpt-4o-mini"
    )

    print(f"\nUsing model: {config.main_model.name}")
    print("Sending streaming refinement request...\n")

    # Track streaming progress
    char_count = 0
    start_time = time.time()

    def streaming_callback(chunk: str):
        nonlocal char_count
        char_count += len(chunk)
        # Print a dot every 10 characters to show progress
        if char_count % 10 == 0:
            print(".", end="", flush=True)

    try:
        print("Streaming progress: ", end="", flush=True)

        corrected_pairs, usage, response_text = refine_chunk_sdk_streaming(
            test_pairs,
            global_memory,
            config,
            chunk_callback=streaming_callback
        )

        elapsed = time.time() - start_time

        print("\n\n✓ Refinement successful!")
        print(f"\nStreaming stats:")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Characters streamed: {char_count}")
        print(f"  Streaming rate: {char_count/elapsed:.1f} chars/sec")

        print(f"\nToken usage:")
        print(f"  Prompt tokens: {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens: {usage.total_tokens}")

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
        print(f"\n✗ Refinement failed: {str(e)}")
        return False


def test_streaming_with_visual_feedback():
    """Test streaming with visual character-by-character display."""
    print("\n" + "=" * 60)
    print("Testing Streaming with Visual Feedback")
    print("=" * 60)

    config = load_config_sdk(model_name="gpt-4o-mini")

    print(f"\nUsing model: {config.main_model.name}")
    print("Streaming a short story...\n")

    messages = [
        {"role": "user", "content": "Write a very short story (2-3 sentences) about a cat."}
    ]

    # Visual feedback callback
    def visual_callback(chunk: str):
        print(chunk, end="", flush=True)
        # Small delay to make streaming visible
        time.sleep(0.01)

    try:
        print("Story:")
        print("-" * 40)

        response_text, usage = call_openai_api_sdk_streaming(
            messages,
            config,
            model_settings=config.main_model,
            chunk_callback=visual_callback
        )

        print("\n" + "-" * 40)
        print(f"\n✓ Streaming complete!")
        print(f"Total tokens: {usage.total_tokens}")

        return True

    except LLMAPIError as e:
        print(f"\n✗ Streaming failed: {str(e)}")
        return False


def compare_streaming_vs_non_streaming():
    """Compare streaming vs non-streaming performance."""
    print("\n" + "=" * 60)
    print("Comparing Streaming vs Non-Streaming")
    print("=" * 60)

    from llm_client_sdk import call_openai_api_sdk

    config = load_config_sdk(model_name="gpt-4o-mini")

    messages = [
        {"role": "user", "content": "List 5 programming languages."}
    ]

    print("\n1. Non-streaming request...")
    start = time.time()
    try:
        response_text, usage = call_openai_api_sdk(
            messages,
            config,
            model_settings=config.main_model
        )
        non_streaming_time = time.time() - start
        print(f"   ✓ Completed in {non_streaming_time:.2f}s")
        print(f"   Response: {response_text[:60]}...")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    print("\n2. Streaming request...")
    first_chunk_time = None
    start = time.time()

    def timing_callback(chunk: str):
        nonlocal first_chunk_time
        if first_chunk_time is None:
            first_chunk_time = time.time() - start
        print(chunk, end="", flush=True)

    try:
        response_text, usage = call_openai_api_sdk_streaming(
            messages,
            config,
            model_settings=config.main_model,
            chunk_callback=timing_callback
        )
        streaming_time = time.time() - start

        print(f"\n   ✓ Completed in {streaming_time:.2f}s")
        print(f"   Time to first chunk: {first_chunk_time:.2f}s")

        print("\n" + "=" * 60)
        print("Performance Comparison:")
        print(f"  Non-streaming total time: {non_streaming_time:.2f}s")
        print(f"  Streaming total time: {streaming_time:.2f}s")
        print(f"  Time to first token (streaming): {first_chunk_time:.2f}s")
        print(f"  User perceived speedup: {non_streaming_time/first_chunk_time:.1f}x faster")

        return True

    except Exception as e:
        print(f"\n   ✗ Failed: {e}")
        return False


def main():
    """Run all streaming tests."""
    print("\n" + "=" * 60)
    print("OpenAI SDK Streaming Test Suite")
    print("=" * 60)
    print("\nThis script tests the streaming API implementation")
    print("and demonstrates real-time token generation.\n")

    results = []

    # Test 1: Simple streaming
    results.append(("Simple Streaming", test_streaming_simple()))

    # Test 2: Subtitle refinement with streaming
    if results[0][1]:
        results.append(("Subtitle Streaming", test_streaming_subtitle_refinement()))

        # Test 3: Visual feedback
        results.append(("Visual Feedback", test_streaming_with_visual_feedback()))

        # Test 4: Performance comparison
        results.append(("Performance Comparison", compare_streaming_vs_non_streaming()))

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