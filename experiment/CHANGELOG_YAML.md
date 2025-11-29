# YAML Configuration - Change Log

## 2025-11-30: YAML Configuration Support Added

### Summary

Added YAML-based configuration system to the experiment directory, replacing hardcoded defaults with a user-friendly configuration file.

### What Changed

#### New Files
- `config.yaml` - Main configuration file with all settings
- `CONFIG_YAML.md` - Comprehensive guide for YAML configuration
- `test_yaml_config.py` - Test script to verify YAML loading

#### Modified Files
- `config_sdk.py` - Added YAML loading functions:
  - `load_yaml_config()` - Load YAML file
  - `load_config_from_yaml()` - Parse YAML into ConfigSDK object
  - `load_config_sdk()` - Now accepts `yaml_file_path` parameter
- `__init__.py` - Exported `load_config_from_yaml` function
- `README.md` - Added Configuration section with YAML guide

#### Dependencies Added
- `pyyaml` (6.0.3) - YAML parser for Python

### Benefits

1. **Easy Customization**: Edit `config.yaml` instead of modifying code
2. **Clear Documentation**: YAML comments explain each setting
3. **Version Control**: Track configuration changes in git
4. **Multiple Profiles**: Create different YAML files for different scenarios
5. **Backward Compatible**: Existing code continues to work without changes

### Migration Guide

#### Before (Hardcoded)
```python
from experiment.config_sdk import load_config_sdk

# All defaults hardcoded in config_sdk.py
config = load_config_sdk(
    model_name="gpt-4o",  # Had to pass everything as parameters
    dry_run=True,
    verbose=True
)
```

#### After (YAML)
```yaml
# Edit experiment/config.yaml
main_model:
  name: "gpt-4o"

runtime:
  dry_run: true
  verbose: true
```

```python
from experiment.config_sdk import load_config_sdk

# Settings loaded from YAML automatically
config = load_config_sdk()

# Or override specific settings
config = load_config_sdk(model_name="gpt-5-mini")  # Override just the model
```

### Configuration Sections

The YAML file is organized into 9 sections:

1. **api** - API endpoint, key file, timeout
2. **main_model** - GPT-5.* refinement model settings
3. **terminology_model** - GPT-4o-mini glossary extractor settings
4. **tokens** - Token limits and chunk sizes
5. **chunking** - Chunking strategy (token-based or fixed)
6. **pricing** - Cost per 1000 tokens
7. **glossary** - Glossary management settings
8. **user** - Custom prompt file path
9. **runtime** - Verbose mode, dry run, max chunks, etc.

### Usage Examples

#### Load from Default YAML
```python
from experiment.config_sdk import load_config_from_yaml

config = load_config_from_yaml()  # Loads experiment/config.yaml
```

#### Load from Custom YAML
```python
config = load_config_sdk(yaml_file_path="my_config.yaml")
```

#### CLI Overrides
```bash
# YAML sets defaults, CLI overrides them
python main_sdk.py input.ass output.ass --model gpt-4o --dry-run -v
```

### Testing

Run the test suite to verify YAML configuration:

```bash
cd experiment
python test_yaml_config.py
```

Expected output:
```
✅ Test 1 PASSED: Configuration loaded successfully from YAML
✅ Test 2 PASSED: CLI overrides applied correctly
✅ Test 3 PASSED: Backward compatibility maintained
✅ ALL TESTS PASSED
```

### Backward Compatibility

All existing code continues to work:

- `load_config_sdk()` - Still works, loads from YAML by default
- `ConfigSDK` class - No changes to structure
- `config.model_name` - Property aliases still work
- CLI arguments - Still override settings as before

### Future Enhancements

Possible future improvements:

1. **Multiple profiles** - `config_dev.yaml`, `config_prod.yaml`
2. **Environment-specific** - Load different YAML based on `ENV` variable
3. **Schema validation** - Validate YAML against JSON schema
4. **Hot reload** - Reload configuration without restarting
5. **Config templates** - Provide templates for common use cases

### Breaking Changes

**None.** This is a fully backward-compatible enhancement.

### Documentation

- `CONFIG_YAML.md` - Complete guide with examples
- `README.md` - Updated with Configuration section
- `config.yaml` - Inline comments explain each setting

---

**Version:** 1.1.0
**Date:** 2025-11-30
**Status:** Production Ready ✅
