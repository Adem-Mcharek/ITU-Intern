# Azure OpenAI GPT-4 Setup for ITU Transcribe

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your `.env` File

Create or edit `.env` in the project root:

```bash
# Azure OpenAI GPT-4 Configuration
AZURE_OPENAI_API_KEY=your-actual-api-key-here
AZURE_OPENAI_ENDPOINT=https://z-openai-openai4tsb-dev-chn.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=GPT-4

# Optional: Gemini as fallback (recommended)
GEMINI_API_KEY=your-gemini-api-key-here
```

**Important:** Replace `your-actual-api-key-here` with your actual Azure OpenAI API key.

### 3. Test the Connection

Run the test script:
```bash
python test_azure_openai.py
```

You should see:
```
✅ SUCCESS! Azure OpenAI GPT-4 is configured correctly.
```

### 4. Run the Application

```bash
python run.py
```

Visit http://127.0.0.1:5000

## Configuration Details

### Your Azure OpenAI Setup

| Parameter | Value |
|-----------|-------|
| **Endpoint** | `https://z-openai-openai4tsb-dev-chn.openai.azure.com/` |
| **Deployment Name** | `GPT-4` |
| **Model** | GPT-4o |
| **API Version** | `2024-12-01-preview` |

### How It Works

The system uses GPT-4 with the following parameters:

```python
response = client.chat.completions.create(
    model="GPT-4",  # Your deployment name
    messages=[...],
    temperature=0.1,  # Low for consistent results
    top_p=1.0,
    max_tokens=8000  # Varies by task
)
```

**Note:** We use `temperature=0.1` (not 1.0) for speaker identification because we need consistent, structured output.

## Verification Checklist

- [ ] `openai` package installed (`pip install openai>=1.0.0`)
- [ ] `.env` file created with all 4 Azure OpenAI variables
- [ ] API key is correct (from Azure Portal)
- [ ] Test script runs successfully
- [ ] Application starts without errors

## Expected Output When Processing

When GPT-4 is active, you'll see:

```
🔍 Enhanced Speaker Extraction with GPT-4 (Multi-Pass)
  Pass 1: Extracting all speaker mentions...
  ✓ Found 12 speaker mentions
  Pass 2: Building speaker profiles with validation...
  ✓ Created profiles for 8 speakers:
    • Dr. Jane Smith: Director at UN Office
    • John Doe: Minister at Dominican Republic
    ... and 6 more

🚀 Enhanced Speaker Identification with GPT-4
   Total segments: 456
   Batch size: 50
   Overlap: 5 segments

   Detected 15 potential speaker boundaries

📝 Processing batch 1/10 with GPT-4 (50 segments)...
  Attempt 1/3...
  ✓ Successfully processed batch 1/10
```

## Troubleshooting

### "Authentication failed"
→ Double-check your API key in `.env`

### "Deployment not found"
→ Verify deployment name is exactly `GPT-4` (case-sensitive)

### "Falls back to Gemini"
→ Check console for specific error messages
→ Run `python test_azure_openai.py` to diagnose

### "Module 'openai' not found"
```bash
pip install openai>=1.0.0
```

## API Call Details

### Speaker Extraction (Pass 1)
- **Purpose:** Extract all speaker mentions
- **Max Tokens:** 2000
- **Temperature:** 0.1

### Speaker Extraction (Pass 2)
- **Purpose:** Build comprehensive speaker profiles
- **Max Tokens:** 3000
- **Temperature:** 0.1

### Batch Processing
- **Purpose:** Identify speakers in transcript segments
- **Max Tokens:** 8000
- **Temperature:** 0.1
- **Batches:** ~25 per 1-hour meeting

## Cost Estimate

For a 1-hour meeting (~1000 segments):

- **API Calls:** ~27 calls
- **Input Tokens:** ~50,000 tokens
- **Output Tokens:** ~30,000 tokens
- **Estimated Cost:** ~$2.00 per meeting (GPT-4 pricing)

## Fallback System

If GPT-4 fails or is unavailable:
1. System automatically retries (3 attempts with exponential backoff)
2. Falls back to Gemini for that specific batch
3. Continues processing without data loss

This ensures 100% reliability even if GPT-4 has temporary issues.

## Default Values

If environment variables are not set, the system uses these defaults:

| Variable | Default Value |
|----------|--------------|
| `AZURE_OPENAI_ENDPOINT` | `https://z-openai-openai4tsb-dev-chn.openai.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `GPT-4` |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` |

**Note:** `AZURE_OPENAI_API_KEY` has no default - you must set it!

---

**Ready to process meetings with GPT-4!** 🚀

Run `python test_azure_openai.py` first to verify everything works.

