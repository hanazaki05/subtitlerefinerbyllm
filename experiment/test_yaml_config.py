#!/usr/bin/env python3
"""
Test script for YAML-based configuration loading.

Tests that config_sdk can properly load settings from config.yaml.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment.config_sdk import load_config_sdk, load_config_from_yaml


def test_yaml_config_loading():
    """Test loading configuration from YAML file."""
    print("=" * 70)
    print("Test 1: Load configuration from YAML")
    print("=" * 70)

    config = load_config_from_yaml()

    print(f"\nAPI Settings:")
    print(f"  Base URL: {config.api_base_url}")
    print(f"  Timeout: {config.api_timeout}s")
    print(f"  API Key loaded: {'Yes' if config.api_key else 'No'}")

    print(f"\nMain Model Settings:")
    print(f"  Model: {config.main_model.name}")
    print(f"  Max output tokens: {config.main_model.max_output_tokens}")
    print(f"  Reasoning effort: {config.main_model.reasoning_effort}")
    print(f"  Temperature: {config.main_model.temperature}")

    print(f"\nTerminology Model Settings:")
    print(f"  Model: {config.terminology_model.name}")
    print(f"  Max output tokens: {config.terminology_model.max_output_tokens}")
    print(f"  Temperature: {config.terminology_model.temperature}")

    print(f"\nToken Management:")
    print(f"  Max context tokens: {config.max_context_tokens}")
    print(f"  Memory token limit: {config.memory_token_limit}")
    print(f"  Chunk token soft limit: {config.chunk_token_soft_limit}")

    print(f"\nChunking:")
    print(f"  Pairs per chunk: {config.pairs_per_chunk}")

    print(f"\nPricing:")
    print(f"  Prompt tokens: ${config.price_per_1k_prompt_tokens}/1k")
    print(f"  Completion tokens: ${config.price_per_1k_completion_tokens}/1k")

    print(f"\nGlossary Settings:")
    print(f"  Max entries: {config.glossary_max_entries}")
    print(f"  Policy: {config.glossary_policy}")
    print(f"  Min confidence: {config.terminology_min_confidence}")

    print(f"\nRuntime Options:")
    print(f"  Verbose: {config.verbose}")
    print(f"  Very verbose: {config.very_verbose}")
    print(f"  Debug prompts: {config.debug_prompts}")
    print(f"  Stats interval: {config.stats_interval}s")
    print(f"  Dry run: {config.dry_run}")
    print(f"  Max chunks: {config.max_chunks}")

    print("\n✅ Test 1 PASSED: Configuration loaded successfully from YAML")
    return True


def test_yaml_config_with_cli_overrides():
    """Test loading configuration with CLI overrides."""
    print("\n" + "=" * 70)
    print("Test 2: Load configuration with CLI overrides")
    print("=" * 70)

    config = load_config_sdk(
        model_name="gpt-4o",
        dry_run=True,
        max_chunks=5,
        pairs_per_chunk=20,
        verbose=True
    )

    print(f"\nOverridden Settings:")
    print(f"  Model: {config.main_model.name} (should be gpt-4o)")
    print(f"  Dry run: {config.dry_run} (should be True)")
    print(f"  Max chunks: {config.max_chunks} (should be 5)")
    print(f"  Pairs per chunk: {config.pairs_per_chunk} (should be 20)")
    print(f"  Verbose: {config.verbose} (should be True)")

    # Verify overrides worked
    assert config.main_model.name == "gpt-4o", "Model override failed"
    assert config.dry_run == True, "Dry run override failed"
    assert config.max_chunks == 5, "Max chunks override failed"
    assert config.pairs_per_chunk == 20, "Pairs per chunk override failed"
    assert config.verbose == True, "Verbose override failed"

    print("\n✅ Test 2 PASSED: CLI overrides applied correctly")
    return True


def test_backward_compatibility():
    """Test backward compatibility with old config loading method."""
    print("\n" + "=" * 70)
    print("Test 3: Backward compatibility check")
    print("=" * 70)

    config = load_config_sdk()

    # Check that old property aliases still work
    print(f"\nBackward-compatible properties:")
    print(f"  config.model_name: {config.model_name}")
    print(f"  config.terminology_model_name: {config.terminology_model_name}")

    assert config.model_name == config.main_model.name, "model_name alias failed"
    assert config.terminology_model_name == config.terminology_model.name, "terminology_model_name alias failed"

    print("\n✅ Test 3 PASSED: Backward compatibility maintained")
    return True


if __name__ == "__main__":
    try:
        # Run all tests
        all_passed = True
        all_passed &= test_yaml_config_loading()
        all_passed &= test_yaml_config_with_cli_overrides()
        all_passed &= test_backward_compatibility()

        # Summary
        print("\n" + "=" * 70)
        if all_passed:
            print("✅ ALL TESTS PASSED")
            print("=" * 70)
            print("\nYAML configuration system is working correctly!")
            print("You can now edit experiment/config.yaml to customize settings.")
        else:
            print("❌ SOME TESTS FAILED")
            print("=" * 70)
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ TEST FAILED with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
