#!/usr/bin/env python3
"""
Test script to verify streaming configuration from YAML.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiment.config_sdk import load_config_sdk, load_config_from_yaml


def test_streaming_config():
    """Test that streaming config is loaded correctly from YAML."""

    print("=" * 70)
    print("Streaming Configuration Test")
    print("=" * 70)

    # Test 1: Load from YAML (should default to True)
    print("\nTest 1: Load from YAML (default)")
    config = load_config_from_yaml()
    print(f"  use_streaming from YAML: {config.use_streaming}")
    assert config.use_streaming == True, "Default should be True"
    print("  ✅ PASSED")

    # Test 2: CLI override to False
    print("\nTest 2: CLI override to False")
    config = load_config_sdk(use_streaming=False)
    print(f"  use_streaming after override: {config.use_streaming}")
    assert config.use_streaming == False, "Should be overridden to False"
    print("  ✅ PASSED")

    # Test 3: CLI override to True
    print("\nTest 3: CLI override to True (explicit)")
    config = load_config_sdk(use_streaming=True)
    print(f"  use_streaming after override: {config.use_streaming}")
    assert config.use_streaming == True, "Should be overridden to True"
    print("  ✅ PASSED")

    # Test 4: No override (use YAML default)
    print("\nTest 4: No override (use YAML default)")
    config = load_config_sdk()
    print(f"  use_streaming from YAML: {config.use_streaming}")
    assert config.use_streaming == True, "Should use YAML default (True)"
    print("  ✅ PASSED")

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print("\nStreaming configuration system is working correctly!")
    print("\nUsage:")
    print("  - Edit config.yaml to set default: use_streaming: true/false")
    print("  - Override with CLI: --streaming or --no-streaming")
    print("  - Check current setting: config.use_streaming")


if __name__ == "__main__":
    try:
        test_streaming_config()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
