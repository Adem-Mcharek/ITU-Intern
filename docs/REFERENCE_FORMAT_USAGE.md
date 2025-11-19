# Reference Format Feature - How to Use

## Overview

The system now supports optional reference documents to customize meeting notes format for specific meetings.

## How It Works

### 1. Place Reference Document in Meeting Folder

Add one of these files to your meeting folder:
- `meeting_notes_reference.docx` (Word document)
- `meeting_notes_reference.pdf` (PDF file)

**Location example:**
```
uploads/meeting_68/
├── audio.mp3
├── transcript_speakers.txt
├── transcript.srt
└── meeting_notes_reference.docx  ← Add this
```

### 2. System Detects and Extracts Format

When generating meeting notes, the system will:
1. Check if `meeting_notes_reference.docx` or `.pdf` exists
2. Extract the full text/format from the reference
3. Show: `✓ Reference format found, using as template`

### 3. AI Follows Format Strictly

The AI receives an instruction:
```
CRITICAL: Follow this exact format from the reference example:

[Reference document content here]

Now generate meeting notes in exactly this format for the following transcript:

[Your meeting transcript]
```

### 4. Meeting Notes Generated in Reference Format

The generated notes will match the style, structure, and format of your reference document.

## Examples

### Example 1: Short Format Reference

**Create `meeting_notes_reference.docx` with:**
```
**OVERVIEW**
Brief 1-sentence summary of meeting topic

**KEY POINTS**
• First key point
• Second key point
• Third key point

**ACTION ITEMS**
• Action 1 - Owner
• Action 2 - Owner
```

**Result:** Generated notes will follow this short, bullet-only format

### Example 2: Detailed Format Reference

**Create `meeting_notes_reference.docx` with:**
```
**MEETING OVERVIEW**
Purpose and participants (1-2 paragraphs)

**DISCUSSION HIGHLIGHTS**
Detailed points from the meeting (2-3 paragraphs)

**DECISIONS & NEXT STEPS**
• Decision 1
• Next step 1
• Timeline 1
```

**Result:** Generated notes will follow this more detailed format

### Example 3: Custom Organization Format

**Create `meeting_notes_reference.pdf` with your organization's specific meeting notes template**

**Result:** All future meetings using that folder will generate notes in your format

## When to Use

✅ **Use when:**
- You want consistent format for a series of meetings
- Different meeting types need different formats
- You have a preferred internal format
- Quality control requires specific structure

❌ **Don't use when:**
- Default format meets your needs
- You want system-generated format

## Important Notes

1. **Optional**: If no reference document exists, system uses default format
2. **DOCX first**: If both `.docx` and `.pdf` exist in folder, system uses `.docx`
3. **Format must be valid**: Extract readable text from the reference document
4. **Full content used**: Entire reference document becomes the format template

## Troubleshooting

### "Reference format not detected"
- Check file name is exactly: `meeting_notes_reference.docx` or `.meeting_notes_reference.pdf`
- Check file is in meeting folder, not parent directory
- Ensure file is readable (not corrupted)

### "PDF libraries not available"
- For PDF support, install: `pip install PyPDF2` or `pip install pdfplumber`
- Or use `.docx` format instead

### "Reference format produced wrong results"
- Reference document might be too complex
- Try using a simpler, clearer reference document
- Ensure reference shows the exact desired format

## API/Integration

For developers integrating this:

```python
from pathlib import Path
from app.meeting_notes_generator import generate_meeting_notes_content

meeting_dir = Path("uploads/meeting_68")
transcript = "Your meeting transcript here..."

# System automatically checks for reference
notes = generate_meeting_notes_content(
    transcript_content=transcript,
    meeting_dir=meeting_dir  # Pass meeting directory
)
```

The function automatically:
1. Checks for reference files
2. Extracts format if found
3. Uses custom or default prompt

## File Size Limits

- **DOCX**: Recommended max 10 pages (file size limit)
- **PDF**: Recommended max 5 pages (extraction takes longer)
- **Content**: Full document used as reference

## Examples to Copy

### Minimal Format (copy into meeting_notes_reference.docx)

```
**OVERVIEW**
One sentence about the meeting

**ITEMS**
• Point 1
• Point 2
• Point 3

**ACTIONS**
Action owner: Deadline
```

### Standard Format

```
**MEETING INFORMATION**
Date and participants

**SUMMARY**
Brief overview of discussion

**KEY POINTS**
• Point 1
• Point 2

**DECISIONS**
• Decision 1

**ACTION ITEMS**
• Task 1 - Owner: Deadline
• Task 2 - Owner: Deadline

**NEXT MEETING**
Date and topic
```

### Detailed Format

```
**EXECUTIVE OVERVIEW**
Purpose, scope, and main outcomes

**PARTICIPANTS**
Names and organizations

**DETAILED DISCUSSION**
Topic 1: Key discussion points
Topic 2: Key discussion points

**TECHNICAL MATTERS**
Standards and specifications discussed

**DECISIONS MADE**
• Decision with reasoning

**ACTION ITEMS**
• Item with owner and deadline

**FOLLOW-UP REQUIRED**
Next steps and stakeholders
```

---

**Quick Start**: Create a sample `meeting_notes_reference.docx` and add it to any meeting folder to see it in action!

