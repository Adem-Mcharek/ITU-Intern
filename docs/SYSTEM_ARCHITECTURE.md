# Meeting Notes Generation - System Architecture

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEETING NOTES GENERATION SYSTEM                     │
└─────────────────────────────────────────────────────────────────────────────┘

                                   INPUT
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            Transcript Files              Meeting Metadata
                    │                               │
        ┌───────────┴───────────┐        (from database)
        │                       │               │
        ▼                       ▼               ▼
    audio.mp3          transcript_speakers.txt  Title, ID
    
                    [EXTRACTION PHASE]
                            │
                    ┌───────┴────────┐
                    │                │
        extract_meeting_metadata()  extract_transcript_content()
        │                          │
        ├─ Speakers count         ├─ Read file
        ├─ Organizations          ├─ Parse lines
        └─ Meeting date           └─ Strip formatting
                    │                │
                    └───────┬────────┘
                            │
                    [CONSOLIDATION]
                            │
            ┌───────────────┴───────────────┐
            │                               │
        Metadata dict               Transcript text
        {title, date,               (59,758 chars)
         speakers,
         orgs}                      MEETING_NOTES_PROMPT
                                            │
                                    ┌───────┴────────┐
                                    │                │
                                    ├─ Instructions
                                    ├─ Format specs
                                    └─ Examples
                                    
                    [AI PROCESSING PHASE]
                            │
                    ┌───────┴────────┐
                    │                │
        Setup Azure Client   Create Full Prompt
        │                    │
        ├─ Get API key       full_prompt =
        ├─ Get endpoint      TEMPLATE +
        ├─ Get deployment    transcript +
        └─ Initialize        "Generate notes:"
        
                    │        │
                    └───────┬┘
                            │
            client.chat.completions.create()
            │
            ├─ model: GPT-4
            ├─ temp: 0.5 (consistent)
            ├─ max_tokens: 2000
            └─ messages: [system, user]
            
                AZURE OPENAI API
                ┌──────────────┐
                │   GPT-4      │ ◄─── Request
                │ (gpt-4o)     │
                └──────────────┘
                      │
                      ├─► Processes prompt
                      ├─► Generates structured notes
                      ├─► Returns response
                      │
                      ▼
                Response object
                ├─ choices[0]
                ├─ message.content
                └─ (Markdown-formatted text)
                
        [RETRY LOOP WITH RATE LIMIT HANDLING] ◄─── THE FIX IS HERE!
                            │
        if response_ok:
        │                           if exception:
        │                           │
        │                   error_str = str(e)
        │                           │
        │           ┌───────────────┴───────────────┐
        │           │                               │
        │       Is rate limit?              Other error?
        │       ("429" or                   ("timeout",
        │        "RateLimitReached")        "connection", etc)
        │           │                               │
        │           │                       ┌───────┴────────┐
        │           │                       │                │
        │       delay = 60s         delay = min(2^i, 30s)
        │       (Azure required)    (exponential backoff)
        │           │                       │
        │           └───────────┬───────────┘
        │                       │
        │             time.sleep(delay)
        │             │
        │         Retry? (max 3 attempts)
        │         ├─ Yes ─→ Loop again
        │         └─ No ──→ Return None (fail)
        │
        ▼
        notes_content (validated)
        ├─ Length > 100 chars ✓
        └─ Markdown format ✓

                    [DOCUMENT CREATION PHASE]
                            │
            create_formatted_document()
            │
            ├─ Create Word document
            ├─ Set margins (1 inch)
            ├─ Add header "International Telecommunication Union"
            ├─ Add title "MEETING NOTES"
            ├─ Add meeting title (from metadata)
            ├─ Add date (from metadata)
            ├─ Add separator line
            ├─ Add participating organizations
            │
            └─► _add_formatted_content(doc, notes_content)
                │
                ├─ Split by lines
                ├─ Pattern matching:
                │  ├─ **SECTION** ──→ add_heading(level=2)
                │  ├─ [Name, Org] ──→ add_paragraph() + BOLD + BLUE
                │  ├─ • / - / ◦   ──→ add_paragraph(style='List Bullet')
                │  └─ Regular text ──→ add_paragraph()
                │
                └─ Special formatting:
                   ├─ Keywords (recommendation, decision, etc) → BOLD
                   ├─ Spacing: 6pt after regular, 3pt after bullets
                   ├─ Colors: ITU Blue (0,32,96) for speakers
                   └─ Alignment: Left for body, Center for headers

                    Document with all formatting
                            │
                    [SAVE PHASE]
                            │
            save_meeting_notes_document()
            │
            ├─ Create safe filename
            ├─ Add timestamp (YYYYMMDD)
            ├─ Generate path: 
            │  uploads/meeting_68/Meeting_Notes_[TITLE]_[DATE].docx
            │
            └─► doc.save(path)

                    .docx file saved
                            │
                    [DATABASE UPDATE]
                            │
            save_notes_path_to_database()
            │
            ├─ Query database for meeting
            ├─ Update notes_path field
            └─ Commit to database

                            OUTPUT
                            │
            ┌───────────────┴───────────────┐
            │                               │
      .docx File                    Database Record
      (on disk)                     (in app.db)
      └─ Meeting_Notes_...          └─ notes_path updated
         .docx                           to file location
```

---

## Critical Path Timeline

### For a Typical Meeting (Normal Case - No Rate Limit)

```
Time    Task                               Duration    Cumulative
─────────────────────────────────────────────────────────────────
0:00s   Extract metadata                   ~0.5s       0.5s
0:01s   Extract transcript content         ~1.0s       1.5s
0:02s   Setup Azure client                 ~0.5s       2.0s
0:03s   Create prompt                      ~0.1s       2.1s
0:04s   Call Azure GPT-4 API               ~15s        17.1s
        (waiting for response)
0:19s   Receive & parse response           ~0.5s       17.6s
0:20s   Validate response                  ~0.1s       17.7s
0:21s   Create Word document               ~1.0s       18.7s
0:22s   Add formatted content              ~1.0s       19.7s
0:23s   Save .docx file                    ~0.5s       20.2s
0:24s   Update database                    ~0.5s       20.7s
────────────────────────────────────────────────────────────────
       TOTAL TIME (no rate limits):       ~20-30 seconds
```

### With One Rate Limit (What Happens Now)

```
Time    Task                               Duration    Cumulative
─────────────────────────────────────────────────────────────────
0:00s   Extract metadata                   ~0.5s       0.5s
0:01s   Extract transcript content         ~1.0s       1.5s
0:02s   Setup Azure client                 ~0.5s       2.0s
0:03s   Create prompt                      ~0.1s       2.1s
0:04s   Call Azure GPT-4 API (Attempt 1)   ~3s         5.1s
0:07s   ✗ 429 RateLimitReached error       ~0.1s       5.2s
0:08s   Detect rate limit                  ~0.0s       5.2s
0:08s   Wait 60 seconds...                 60s         65.2s
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
1:08s   Call Azure GPT-4 API (Attempt 2)   ~15s        80.2s
1:23s   Receive & parse response           ~0.5s       80.7s
1:24s   Validate response                  ~0.1s       80.8s
1:25s   Create Word document               ~1.0s       81.8s
1:26s   Add formatted content              ~1.0s       82.8s
1:27s   Save .docx file                    ~0.5s       83.3s
1:28s   Update database                    ~0.5s       83.8s
────────────────────────────────────────────────────────────────
       TOTAL TIME (with 1 rate limit):    ~80-90 seconds
       Improvement: Recovery successful (old code would fail)
```

---

## Error Handling Decision Tree

```
                    Exception occurs
                            │
                    ┌───────┴────────┐
                    │                │
                Is attempt #3?        No
                (last attempt)        │
                    │                 │
                   Yes           What type?
                    │            │
                 Return      ┌───┴──────┬──────────┐
                  None       │          │          │
                             │          │          │
                         Rate    Timeout   Other
                         Limit   Error     Error
                             │          │          │
                    ┌────────┘          │          │
                    │             ┌─────┴──────┘
                    │             │
            Delay = 60s    Delay = 2^attempt
            (0-60 max)     (cap at 30s)
                    │             │
                    └─────┬───────┘
                          │
                   time.sleep(delay)
                          │
                    Increment attempt
                          │
                   Retry (go back)
```

---

## Module Dependencies

```
meeting_notes_generator.py
│
├─ Imports:
│  ├─ os, json, pathlib         (file I/O)
│  ├─ datetime                  (timestamps)
│  ├─ typing                    (type hints)
│  ├─ flask                     (config access)
│  ├─ google.generativeai       (Gemini API - not used)
│  ├─ openai.AzureOpenAI        ◄─── PRIMARY: Azure client
│  └─ docx.*                    ◄─── Document creation
│
├─ Uses these functions:
│  ├─ setup_azure_openai_client()     ◄─── Initialize client
│  ├─ extract_transcript_content()    (from meeting_summarizer)
│  └─ external: db, models           (for database access)
│
└─ Called by:
   ├─ queue_manager.py (Line 235)
   └─ tasks.py (Line 71)
```

---

## Configuration Flow

```
.env file
   │
   ├─ AZURE_OPENAI_API_KEY
   ├─ AZURE_OPENAI_ENDPOINT
   ├─ AZURE_OPENAI_DEPLOYMENT_NAME
   └─ AZURE_OPENAI_API_VERSION
         │
         ▼
Flask app configuration
   │
   ├─ Loaded via current_app.config.get()
   │
   ├─ Fallback to os.environ.get()
   │
   └─→ setup_azure_openai_client()
       │
       └─ AzureOpenAI(
           api_key=key,
           azure_endpoint=endpoint,
           api_version=version
        )
        │
        └─ client.chat.completions.create(
           model=deployment,
           ...
        )
```

---

## Data Structures

### Metadata Dictionary
```python
metadata = {
    'title': str,              # "Digital Transformation..."
    'date': str,               # "November 14, 2024"
    'total_speakers': int,     # 12
    'organizations': [str],    # ["ITU", "UN DESA", "World Bank"]
    'content_length': int      # 59758
}
```

### Transcript Content
```
Raw string containing:
- Speaker names in format: [Name, Organization]
- Quoted speech/statements
- Timestamps (if present)
- Action items, decisions

Example:
"[Technical Expert, ITU] Our analysis shows 5G deployment barriers...
[Policy Advisor, UN DESA] We must consider development impacts...
[Representative, Ghana] Can you elaborate on infrastructure costs?"
```

### Prompt Template (Simplified)
```
"""
You are an ITU intern creating meeting notes.

Structure:
**MEETING OVERVIEW**
Brief purpose and participants

**KEY DISCUSSIONS**
Main topics with [Speaker, Organization] attribution

**DECISIONS & ACTION ITEMS**
• Specific decisions
• Action items

[Generate notes from transcript]
"""
```

---

## Performance Characteristics

### Input Constraints
```
Min transcript length:  1 KB (but quality suffers)
Typical length:         50-100 KB
Max per API call:       ~500 KB (token limits)
Optimal length:         50-150 KB
```

### Resource Usage
```
Memory:
├─ Document object:     ~5 MB
├─ Transcript in RAM:   ~100 KB - 1 MB
└─ Total per meeting:   ~10 MB

Disk:
├─ Generated .docx:     50-300 KB
└─ With all attachments: ~500 KB

API Calls:
├─ Requests per meeting: 1-3 (with retries)
├─ Tokens per request:   ~1000-5000 tokens
└─ Cost: ~$0.01-$0.05 per meeting (depending on retry)
```

### Bottlenecks
```
1. Azure API latency     (10-30s) ◄─── PRIMARY
2. Rate limit recovery   (0-60s)  ◄─── THE FIX ADDRESSES THIS
3. Document creation     (<2s)
4. Disk I/O            (<1s)
5. Database update      (<1s)
```

---

## Integration Points

### Where It's Called

**In queue_manager.py (Line 235-239)**
```python
from app.meeting_notes_generator import process_meeting_notes

notes_success = process_meeting_notes(
    meeting.id,
    meeting_dir,
    meeting.title
)
```

**In tasks.py (Line 71-72)**
```python
from app.meeting_notes_generator import process_meeting_notes

notes_success = process_meeting_notes(
    meeting_obj.id,
    meeting_dir,
    meeting_obj.title
)
```

### Processing Pipeline Context
```
User uploads video
        ↓
Transcription (Whisper)
        ↓
Speaker identification
        ↓
ITU Summary (Gemini)
        ↓
Meeting Notes (Azure GPT-4) ◄─── YOU ARE HERE
        ↓
Results stored in database
        ↓
User downloads .docx file
```

---

## Security Considerations

```
API Keys:
├─ Stored in .env (not in code) ✓
├─ Loaded from environment ✓
└─ Passed to Azure securely (HTTPS) ✓

File Operations:
├─ Safe filename generation ✓
├─ Path validation ✓
└─ UTF-8 encoding ✓

Data:
├─ Transcript content: Not logged ✓
├─ Generated notes: Stored locally ✓
└─ API responses: Not cached long-term ✓
```

---

## Summary

The system is a **robust, AI-powered document generation pipeline** that:

1. **Extracts** meeting data systematically
2. **Processes** via Azure GPT-4 with intelligent retry logic (THE FIX!)
3. **Transforms** AI output into professional Word documents
4. **Stores** results in database and filesystem
5. **Handles** errors gracefully with proper rate limit awareness

The rate limit fix ensures that **when Azure needs time to recover, the system gives it that time** instead of hammering it with immediate retries.

