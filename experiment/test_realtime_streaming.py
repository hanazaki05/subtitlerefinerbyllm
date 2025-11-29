#!/usr/bin/env python3
"""
Test script for real-time streaming output with -vvv flag.

This demonstrates the difference between:
- No verbose: No progress indication
- -v (verbose): Dots for progress
- -vvv (debug_prompts): Real-time LLM output
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment.config_sdk import load_config_sdk
from experiment.llm_client_sdk import refine_chunk_sdk_streaming
from pairs import SubtitlePair
from memory import GlobalMemory


def test_realtime_streaming():
    """Test real-time streaming output with different verbosity levels."""

    # Create test subtitle pairs
    test_pairs = [
        SubtitlePair(
            id=0,
            eng="hello,world!how are you today?",
            chinese="你好世界！你今天怎么样"
        ),
        SubtitlePair(
            id=1,
            eng="i'm fine,thank you.what about you?",
            chinese="我很好谢谢。你呢"
        ),
        SubtitlePair(
            id=2,
            eng="i'm doing great!let's go for a walk.",
            chinese="我很好！我们去散步吧"
        ),
    ]

    # Create global memory
    global_memory = GlobalMemory()

    print("=" * 70)
    print("Real-time Streaming Output Test")
    print("=" * 70)

    # Test 1: Verbose mode (-v) - should show dots
    print("\n" + "=" * 70)
    print("Test 1: Verbose Mode (-v)")
    print("Expected: Progress dots while streaming")
    print("=" * 70)

    config_verbose = load_config_sdk(verbose=True, debug_prompts=False)

    def verbose_callback(chunk_text: str):
        if config_verbose.debug_prompts:
            print(chunk_text, end="", flush=True)
        elif config_verbose.verbose:
            print(".", end="", flush=True)

    print("\nProcessing with verbose mode...")
    print("  Streaming: ", end="", flush=True)

    try:
        corrected_pairs, usage, response = refine_chunk_sdk_streaming(
            test_pairs,
            global_memory,
            config_verbose,
            chunk_callback=verbose_callback
        )
        print()  # New line after dots
        print(f"✅ Completed: {usage.completion_tokens} tokens")
    except Exception as e:
        print(f"\n❌ Failed: {str(e)}")

    # Test 2: Debug mode (-vvv) - should show real-time LLM output
    print("\n" + "=" * 70)
    print("Test 2: Debug Mode (-vvv)")
    print("Expected: Real-time LLM output (actual JSON response)")
    print("=" * 70)

    config_debug = load_config_sdk(debug_prompts=True)

    def debug_callback(chunk_text: str):
        if config_debug.debug_prompts:
            print(chunk_text, end="", flush=True)
        elif config_debug.verbose:
            print(".", end="", flush=True)

    print("\nProcessing with debug mode...")
    print("  LLM Output (real-time):")
    print("  " + "-" * 58)
    print("  ", end="", flush=True)

    try:
        corrected_pairs, usage, response = refine_chunk_sdk_streaming(
            test_pairs,
            global_memory,
            config_debug,
            chunk_callback=debug_callback
        )
        print()  # New line after output
        print("  " + "-" * 58)
        print(f"✅ Completed: {usage.completion_tokens} tokens")
    except Exception as e:
        print(f"\n❌ Failed: {str(e)}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
Verbosity Levels for Streaming:

1. No flags:
   - No progress indication
   - Wait for completion silently

2. -v (verbose):
   - Shows progress dots: .........
   - Indicates streaming is happening
   - Doesn't show actual content

3. -vvv (debug_prompts):
   - Shows real-time LLM output
   - See JSON response as it's generated
   - Useful for debugging and monitoring

Usage Examples:

# Just progress dots
python main_sdk.py input.ass output.ass --streaming -v

# Real-time LLM output
python main_sdk.py input.ass output.ass --streaming -vvv

# Or edit config.yaml:
runtime:
  debug_prompts: true  # Enable real-time output
    """)


if __name__ == "__main__":
    try:
        test_realtime_streaming()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
