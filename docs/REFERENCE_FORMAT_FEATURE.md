# Reference Format Feature - Implementation Summary

## ✅ What Was Implemented

A flexible reference document system that allows customizing meeting notes format per meeting.

## How It Works

### 1. **Detection** 
- System looks for: `meeting_notes_reference.docx` or `meeting_notes_reference.pdf`
- Location: Meeting folder (e.g., `uploads/meeting_68/`)
- Priority: `.docx` checked first, then `.pdf`

### 2. **Extraction**
- **DOCX**: Uses `python-docx` library (already in dependencies)
- **PDF**: Tries `PyPDF2` or `pdfplumber` (optional install)
- Extracts complete text from reference document

### 3. **Prompt Generation**
If reference found:
```python
full_prompt = """You are an ITU intern creating meeting notes.

CRITICAL: Follow this exact format from the reference example:

[EXTRACTED REFERENCE CONTENT HERE]

Now generate meeting notes in exactly this format for the following transcript:

[MEETING TRANSCRIPT]

Generate meeting notes following the reference format strictly:"""
```

If no reference:
```python
full_prompt = MEETING_NOTES_PROMPT + "\n\n" + transcript
```

### 4. **Fallback**
- If reference can't be read → uses default format (automatic)
- No errors, graceful degradation

## Code Changes

### File: `app/meeting_notes_generator.py`

**New Functions:**
1. `extract_reference_format(meeting_dir: Path)` - Main detection function
2. `_extract_text_from_docx(file_path: Path)` - DOCX extraction
3. `_extract_text_from_pdf(file_path: Path)` - PDF extraction (with fallbacks)

**Modified Functions:**
1. `generate_meeting_notes_content()` - Now accepts optional `meeting_dir` parameter
2. `create_meeting_notes()` - Now passes `meeting_dir` to generation function

## Usage

### Simple Use Case
```
uploads/meeting_68/
├── transcript_speakers.txt
└── meeting_notes_reference.docx  ← Add this file
```

System automatically:
1. Detects the reference
2. Extracts its format
3. Generates notes in that format

### For Developers
```python
notes = generate_meeting_notes_content(
    transcript_content=transcript,
    meeting_dir=Path("uploads/meeting_68")  # Pass directory
)
```

## Features

✅ **Automatic Detection**
- No configuration needed
- File naming convention: `meeting_notes_reference.docx` or `.pdf`

✅ **Format Extraction**
- Extracts complete reference format
- Works with both DOCX and PDF

✅ **Flexible**
- Different format per meeting
- Optional (not required)

✅ **Robust**
- Handles missing files gracefully
- Falls back to default if error occurs
- Handles multiple PDF libraries

✅ **User-Friendly**
- Just add a file to folder
- AI follows it strictly
- No code changes needed

## Supported File Formats

| Format | Support | Library | Notes |
|--------|---------|---------|-------|
| `.docx` | ✅ Built-in | python-docx | Already in dependencies |
| `.pdf` | ✅ Optional | PyPDF2 or pdfplumber | Install separately if needed |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No reference file | Uses default format (silent) |
| Reference file corrupted | Uses default format (warning logged) |
| PDF library not installed | Uses default format (warning) |
| Permission denied reading file | Uses default format (warning) |
| All others | Uses default format (safe fallback) |

## Log Output

### With Reference Found
```
Attempting Azure GPT-4...
  ✓ Reference format found, using as template
  Azure attempt 1/2...
```

### Without Reference
```
Attempting Azure GPT-4...
  Azure attempt 1/2...
```

## Real-World Examples

### Meeting A: Short Format
Place `meeting_notes_reference.docx` with:
```
**OVERVIEW**
[1 sentence]

**ACTIONS**
• Item 1
• Item 2
```
→ Generated notes follow short format

### Meeting B: Detailed Format  
Place `meeting_notes_reference.docx` with:
```
**FULL DISCUSSION**
[Multiple paragraphs]

**ANALYSIS**
[Multiple paragraphs]

**OUTCOMES**
• Item 1
• Item 2
```
→ Generated notes follow detailed format

### Meeting C: No Reference
No reference file → uses default 6-section format

## Dependencies

### Required (Already Have)
- `python-docx` - DOCX support

### Optional (For PDF Support)
- `PyPDF2` - PDF extraction (primary)
- `pdfplumber` - PDF extraction (fallback)

Install if needed:
```bash
pip install PyPDF2
# or
pip install pdfplumber
```

## Testing

To test the feature:

1. Create a reference document:
   ```
   **OVERVIEW**
   Purpose: Brief one-liner
   
   **KEY POINTS**
   • Point 1
   • Point 2
   
   **DECISIONS**
   • Decision 1
   ```

2. Save as `uploads/meeting_68/meeting_notes_reference.docx`

3. Process the meeting - should generate notes in reference format

4. Check logs for: `✓ Reference format found, using as template`

## Future Enhancements

Possible improvements:
- Image extraction from reference (complex, low priority)
- Table formatting from reference
- CSS/formatting preservation
- Template variables (`{date}`, `{participants}`)

## Backward Compatibility

✅ **100% Backward Compatible**
- Old code still works (meeting_dir is optional)
- Default behavior unchanged
- No breaking changes

## Summary

| Aspect | Details |
|--------|---------|
| **Feature** | Optional reference document for custom meeting notes format |
| **Setup** | Add `.docx` or `.pdf` file to meeting folder |
| **File Name** | `meeting_notes_reference.docx` or `meeting_notes_reference.pdf` |
| **Works With** | Azure GPT-4 and Gemini (both providers) |
| **Fallback** | Uses default format if reference unavailable |
| **Code Impact** | 3 new functions, 1 modified function signature |
| **Dependencies** | No new required deps (PDF is optional) |
| **Status** | ✅ Complete and tested |

---

**Next**: See `REFERENCE_FORMAT_USAGE.md` for detailed usage examples

