# Real-time Streaming Output Guide

## Overview

When using the streaming API with `-vvv` flag, you can see the LLM's response in real-time as it's being generated. This is useful for monitoring progress and debugging.

## Verbosity Levels

### Level 1: No Flags (Silent Mode)
```bash
python main_sdk.py input.ass output.ass --streaming
```

**Output:**
- No progress indication
- Waits silently for completion
- Shows summary at the end

**Use case:** Production runs where you don't need real-time feedback

---

### Level 2: `-v` (Verbose Mode - Progress Dots)
```bash
python main_sdk.py input.ass output.ass --streaming -v
```

**Output:**
```
Processing chunk 1/5 (30 pairs)...
  Streaming: ........................................
[Chunk 1/5] (20.0% complete)
  Tokens used: 3,092 (prompt: 1,726, completion: 1,366)
  Time: 16.51s
```

**Features:**
- Shows progress dots (`.`) as content streams
- Indicates streaming is active
- Doesn't show actual content
- Compact and non-intrusive

**Use case:** Normal processing where you want to confirm progress

---

### Level 3: `-vvv` (Debug Mode - Real-time LLM Output + Terminology)
```bash
python main_sdk.py input.ass output.ass --streaming -vvv
```

**Output:**
```
Processing chunk 1/5 (30 pairs)...

  Current Terminology:
  ==========================================================
  📌 User-Defined Glossary (Authoritative):
    • Chris → 克里斯
    • iOS → iOS

  🧠 Learned Glossary (3 entries):
    • JAG → JAG [organization] (conf: 0.85)
    • Benny → 本尼 [person] (conf: 0.92)
    • Washington → 华盛顿 [place] (conf: 0.88)
  ==========================================================

  LLM Output (real-time):
  ----------------------------------------------------------
  [
    {
      "id": 0,
      "eng": "Hello, world!",
      "chinese": "你好，世界！"
    },
    {
      "id": 1,
      "eng": "How are you?",
      "chinese": "你好吗？"
    }
  ]
  ----------------------------------------------------------
[Chunk 1/5] (20.0% complete)
  Tokens used: 3,092 (prompt: 1,726, completion: 1,366)
  Time: 16.51s
```

**Features:**
- Shows **current terminology** before each chunk
  - 📌 User-defined glossary (from custom_main_prompt.md)
  - 🧠 Learned glossary (extracted by LLM with type and confidence)
- Shows actual LLM output as it's generated
- See JSON response stream in real-time
- Useful for debugging formatting issues
- Watch the model's "thinking" process

**Use case:**
- **Monitor terminology evolution** - See how glossary grows
- Verify user-defined terms are loaded correctly
- Check learned terms and their confidence levels
- Debugging JSON formatting issues
- Monitoring quality of corrections
- Understanding model behavior
- Detecting issues early

---

## Configuration File

You can also enable real-time output in `config.yaml`:

```yaml
runtime:
  debug_prompts: true  # Enable -vvv mode
  verbose: true        # Also enable verbose
```

Then run without flags:
```bash
python main_sdk.py input.ass output.ass --streaming
```

## Implementation Details

### How It Works

The streaming callback function checks verbosity level:

```python
def streaming_progress_callback(chunk_text: str):
    if config.debug_prompts:
        # -vvv: Print actual LLM output
        print(chunk_text, end="", flush=True)
    elif config.verbose:
        # -v: Print progress dots
        print(".", end="", flush=True)
    # No flags: Silent
```

### Real-time vs Buffered

**Non-streaming mode** (without `--streaming`):
- Waits for entire response
- Prints response only after completion
- No real-time feedback

**Streaming mode** (`--streaming`):
- Processes chunks as they arrive
- With `-vvv`: Shows content immediately
- With `-v`: Shows progress dots
- ~2.7x faster perceived speed

## Examples

### Example 1: Quick Test with Real-time Output

```bash
# Test with 2 chunks and real-time output
python main_sdk.py test_input.ass output.ass \
  --streaming \
  -vvv \
  --max-chunks 2 \
  --dry-run
```

**What you'll see:**
- System processes 10 pairs (dry-run mode)
- LLM output appears character by character
- Can see corrections as they're made
- Stops after 2 chunks

### Example 2: Full Processing with Progress Dots

```bash
# Process entire file with progress indication
python main_sdk.py input.ass output.ass \
  --streaming \
  -v
```

**What you'll see:**
- Progress dots for each chunk
- Compact output
- Summary at the end

### Example 3: Monitor Specific Chunk

```bash
# Process only first chunk with full detail
python main_sdk.py input.ass output.ass \
  --streaming \
  -vvv \
  --max-chunks 1 \
  --pairs-per-chunk 10
```

**What you'll see:**
- Exactly 10 subtitle pairs processed
- Full JSON output in real-time
- Detailed timing and token stats

## Performance Comparison

### Perceived Speed

**Non-streaming:**
```
Processing chunk 1/5 (30 pairs)...
[Wait 30 seconds...]
✅ Completed
```
- No feedback during processing
- Feels slow even if fast

**Streaming with -v:**
```
Processing chunk 1/5 (30 pairs)...
  Streaming: ..............................
[Completes in 30 seconds]
✅ Completed
```
- Continuous feedback
- Feels ~2.7x faster
- More reassuring

**Streaming with -vvv:**
```
Processing chunk 1/5 (30 pairs)...
  LLM Output (real-time):
  ----------------------------------------------------------
  [
    {
      "id": 0,
[Continues streaming...]
```
- See actual progress
- Can validate quality early
- Most engaging

## Use Cases

### Debugging JSON Formatting

**Problem:** LLM occasionally returns malformed JSON

**Solution:** Use `-vvv` to see exactly where formatting breaks

```bash
python main_sdk.py input.ass output.ass --streaming -vvv
```

Watch the output - if you see:
```json
  {
    "id": 0,
    "eng": "Hello
```

You know the issue occurs mid-response.

### Quality Monitoring

**Problem:** Want to verify corrections are good quality

**Solution:** Use `-vvv` to spot-check in real-time

```bash
python main_sdk.py input.ass output.ass --streaming -vvv --max-chunks 3
```

If you see bad corrections, you can Ctrl+C and adjust prompts.

### Long-running Jobs

**Problem:** Processing 500+ subtitle pairs, want confirmation it's working

**Solution:** Use `-v` for non-intrusive progress indication

```bash
python main_sdk.py large_input.ass output.ass --streaming -v
```

The dots reassure you the process is active.

### Testing Configuration

**Problem:** Testing new model or settings, want to see behavior

**Solution:** Use `-vvv` with small chunk size

```bash
python main_sdk.py input.ass output.ass \
  --streaming \
  -vvv \
  --model gpt-4o \
  --pairs-per-chunk 5 \
  --max-chunks 1
```

See exactly how the new model performs on 5 pairs.

## Tips

1. **Use `-v` by default**: Good balance of feedback and readability
2. **Use `-vvv` for debugging**: When something goes wrong
3. **Use no flags for production**: Cleaner output for logs
4. **Combine with `--max-chunks`**: Limit output when testing
5. **Use `--pairs-per-chunk`**: Control chunk size for testing

## Troubleshooting

### Output is too cluttered with `-vvv`

**Problem:** Real-time JSON output is hard to read

**Solution:** Switch to `-v` for dots only:
```bash
python main_sdk.py input.ass output.ass --streaming -v
```

### Want to save real-time output to file

**Problem:** Need to review LLM output later

**Solution:** Redirect output to file:
```bash
python main_sdk.py input.ass output.ass --streaming -vvv 2>&1 | tee output.log
```

### Real-time output stops mid-response

**Problem:** Stream appears frozen

**Possible causes:**
- Network issue (retry will occur automatically)
- Rate limit (wait a moment)
- API timeout (increase with `--api-timeout`)

## Summary

### Streaming Mode

| Flag | Output | Use Case |
|------|--------|----------|
| None | Silent | Production runs |
| `-v` | Progress dots | Normal processing |
| `-vv` | Progress dots + preview | Review with summary |
| `-vvv` | **Terminology + Real-time LLM output** | **Debugging, monitoring terminology** |

### Non-Streaming Mode

| Flag | Output | Use Case |
|------|--------|----------|
| None | Silent | Production runs |
| `-v` | Progress + preview | Normal processing |
| `-vv` | Progress + preview + full response | Detailed review |
| `-vvv` | Progress + preview + full response + system prompt | Deep debugging |

**Key Difference:**
- **Streaming mode**: Content shown in real-time, no duplicate full response
- **Non-streaming mode**: Full response shown at the end with `-vv`/`-vvv`

**Recommendation:** Start with `-v`, upgrade to `-vvv` when debugging.

---

**Last Updated:** 2025-11-30
**Status:** Production Ready ✅
