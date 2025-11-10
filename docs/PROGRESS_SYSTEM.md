# Clean Progress Output System

## Overview

The clean progress output system provides minimal, informative terminal output during meeting processing. This reduces visual clutter while keeping users informed of progress.

## Features

### Normal Mode (Default)
- **One line per step**: Each processing step shows on a single line with status
- **Timing information**: Shows total processing time and per-step durations
- **Smart info**: Shows relevant metrics (file size, segment count, speaker count)
- **Clean completion**: Clear summary at the end

### Verbose Mode
- **Detailed output**: Shows internal operations and API calls
- **Debug information**: Extra details about processing decisions
- **Full tracebacks**: Complete error traces for debugging

## Example Output

### Normal Mode (Default)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing: ITU-T Study Group 2 Meeting - Session 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▸ Checking for existing transcripts... ✓ (Not found)
▸ Downloading audio... ✓ (124.5 MB)
▸ Transcribing audio (GPU)... ✓ (842 segments, 8m 34s)
▸ Extracting speakers... ✓ (12 speakers identified)
▸ Organizing segments... ✓ (67 speaker turns)
▸ Generating transcript... ✓
▸ Generating ITU summary... ✓
▸ Generating meeting notes... ✓
▸ Cleaning up... ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Complete in 12m 45s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### With Transcript Reuse
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing: ITU-T Study Group 2 Meeting - Session 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▸ Checking for existing transcripts... ✓ (Found (Meeting #42))
▸ Copying transcripts... ✓ (Saved ~12 minutes)
▸ Extracting speakers... ✓ (12 speakers identified)
▸ Organizing segments... ✓ (67 speaker turns)
▸ Generating transcript... ✓
▸ Generating ITU summary... ✓
▸ Generating meeting notes... ✓
▸ Cleaning up... ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Complete in 3m 12s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Usage

### Enable Normal Mode (Default)
No configuration needed - clean output is the default.

### Enable Verbose Mode
Set the `VERBOSE` environment variable to see all debug logs (including from libraries):

**Windows (PowerShell):**
```powershell
$env:VERBOSE="true"
python run.py
```

**Windows (CMD):**
```cmd
set VERBOSE=true
python run.py
```

**Linux/Mac:**
```bash
export VERBOSE=true
python run.py
```

**Or in .env file:**
```
VERBOSE=true
```

### What Gets Hidden in Normal Mode

In normal mode (VERBOSE=false or not set), the following are suppressed:
- DEBUG and INFO logs from urllib3 (HTTP connection details)
- DEBUG and INFO logs from openai (API request/response details)
- DEBUG and INFO logs from httpcore (Low-level HTTP)
- DEBUG and INFO logs from httpx (HTTP client)
- DEBUG and INFO logs from werkzeug (Flask web server)
- Internal pipeline details (unless errors occur)
- AI model processing details (shown as one-line summaries)

In verbose mode (VERBOSE=true), ALL logs are shown for debugging.

## Implementation

### Core Components

**`app/progress.py`**: Progress logging module
- `ProgressLogger` class for clean output
- Global logger instance with `get_logger()`
- Support for verbose and normal modes

**`app/pipeline.py`**: Main processing pipeline
- Uses progress logger for all output
- Shows timing and metrics
- Silent helper functions

**`app/queue_manager.py`**: Background queue worker
- Minimal output in normal mode
- Detailed output only in verbose mode

### API

```python
from app.progress import get_logger

# Get logger (verbose setting from environment)
logger = get_logger()

# Start processing
logger.start("Meeting Title")

# Show a step
logger.step("Downloading audio")
logger.step_complete("124.5 MB")

# Add detail (only in verbose mode)
logger.step_detail("Using format: mp3")

# Show warning (only in verbose mode)
logger.warning("Optional feature not available")

# Show error (always shown)
logger.error("Failed to process")

# Complete processing
logger.complete()
```

## Benefits

1. **Reduced Clutter**: 90% less terminal output in normal mode
2. **Still Informative**: Key metrics and progress clearly shown
3. **Easy Debugging**: Enable verbose mode when needed
4. **Professional**: Clean, organized output format
5. **Timing Visible**: See how long each step takes
6. **Progress Tracking**: Know exactly where processing is at
7. **Library Logs Suppressed**: No more DEBUG spam from urllib3, openai, httpcore, werkzeug

## Backward Compatibility

- All existing functionality preserved
- No breaking changes to API
- Error messages still shown
- Warnings available in verbose mode

## Testing

Run the demonstration:
```bash
python test_progress_output.py
```

This shows both normal processing and transcript reuse scenarios with clean output.

