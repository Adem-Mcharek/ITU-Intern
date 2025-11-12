# OpenAI GPT-5 Setup Guide

## Overview
This guide shows you how to configure OpenAI API (GPT-5) as your primary AI model for speaker identification and diarization.

## Priority Order
After setup, the system will try models in this order:
1. **OpenAI API (GPT-5)** ← Primary (NEW)
2. **Azure OpenAI (GPT-4)** ← Secondary (Fallback)
3. **Ollama (Gemma 3)** ← Tertiary (Local fallback)
4. **Google Gemini** ← Legacy features only

## Step 1: Get Your OpenAI API Key

### 1.1 Create/Login to OpenAI Account
- Go to: https://platform.openai.com
- Sign up or log in

### 1.2 Generate API Key
- Navigate to: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Give it a name (e.g., "ITU-Transcribe-Production")
- Copy the key **immediately** (you won't see it again!)

### 1.3 Check Your Organization ID (Optional)
- Go to: https://platform.openai.com/settings/organization
- Copy your Organization ID if you have one (format: `org-xxxxx`)

## Step 2: Update Your .env File

### 2.1 Copy the Template
```bash
cp env.example .env
```

### 2.2 Add Your OpenAI Credentials
Open `.env` and update the PRIMARY section:

```env
# -----------------------------------------------------------------------------
# PRIMARY: OpenAI API (GPT-5) - Direct connection to OpenAI
# -----------------------------------------------------------------------------
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL_NAME=gpt-5

# Optional: If you have an organization
# OPENAI_ORG_ID=org-xxxxxxxxxxxxxxxxxxxxx

# Optional: Custom endpoint (usually not needed)
# OPENAI_BASE_URL=https://api.openai.com/v1
```

### 2.3 Keep Azure as Fallback (Optional)
If you want Azure OpenAI as a fallback, keep these lines:

```env
# -----------------------------------------------------------------------------
# SECONDARY: Azure OpenAI API (GPT-4) - Fallback if OpenAI unavailable
# -----------------------------------------------------------------------------
AZURE_OPENAI_API_KEY=your-azure-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=GPT-4
```

To disable Azure fallback, simply leave these fields empty or remove the API key.

## Step 3: Verify Model Name

### Important: GPT-5 Model Name
OpenAI's actual model names might be:
- `gpt-5` (if released)
- `gpt-5-turbo` (likely name for faster version)
- `gpt-4.5` (interim release)
- `gpt-4-turbo` (current latest as of this writing)

**Check the latest model names at:**
https://platform.openai.com/docs/models

Update your `.env` with the correct name:
```env
OPENAI_MODEL_NAME=gpt-5-turbo  # or whatever the actual name is
```

## Step 4: Test Your Configuration

### 4.1 Create a Test Script
Create `test_openai_connection.py`:

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Test connection
def test_openai():
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL_NAME', 'gpt-4-turbo')
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'OpenAI connection successful!' in one sentence."}
            ],
            max_tokens=50
        )
        
        print(f"✅ OpenAI connection successful!")
        print(f"   Model: {model}")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

if __name__ == "__main__":
    test_openai()
```

### 4.2 Run the Test
```bash
python test_openai_connection.py
```

Expected output:
```
✅ OpenAI connection successful!
   Model: gpt-5
   Response: OpenAI connection successful!
```

## Step 5: Cost Considerations

### GPT-5 Pricing (Estimated)
Check current pricing at: https://openai.com/pricing

As of this guide, typical costs might be:
- **Input tokens**: ~$X per 1M tokens
- **Output tokens**: ~$X per 1M tokens

### For your use case:
- **Speaker Extraction**: ~10k-50k tokens per meeting
- **Diarization**: ~100k-500k tokens per long meeting
- **Estimated cost**: $X-$X per meeting

### Cost Control Tips:
1. Set usage limits in OpenAI dashboard
2. Monitor token usage in the pipeline output
3. Use Azure OpenAI as fallback for cost savings
4. Use Ollama (local) for development/testing

## Step 6: Update Pipeline Code (Next Step)

After setting up your `.env`, you'll need to:
1. Add `setup_openai_client()` function to `app/pipeline.py`
2. Update priority order to check OpenAI first
3. Add error handling for GPT-5 specific features

**Ready for me to implement these changes in the pipeline?**

## Troubleshooting

### Error: "Invalid API Key"
- Check your API key in .env (no quotes, no spaces)
- Verify key is active at: https://platform.openai.com/api-keys
- Ensure key hasn't been revoked or expired

### Error: "Model not found"
- Check model name at: https://platform.openai.com/docs/models
- Update `OPENAI_MODEL_NAME` in `.env`
- Try `gpt-4-turbo` if GPT-5 isn't available yet

### Error: "Rate limit exceeded"
- Check your usage limits at: https://platform.openai.com/settings/organization/limits
- Add rate limiting delays in the code
- Consider Azure OpenAI for higher rate limits

### Error: "Insufficient quota"
- Add billing method at: https://platform.openai.com/settings/organization/billing
- Check your account balance
- Use Azure or Ollama as fallback

## Environment Variable Reference

### Required
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL_NAME=gpt-5
```

### Optional
```env
OPENAI_ORG_ID=org-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

### For Azure Fallback
```env
AZURE_OPENAI_API_KEY=xxxxx
AZURE_OPENAI_ENDPOINT=https://xxxxx.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=GPT-4
```

## Next Steps
1. ✅ Set up `.env` file with OpenAI credentials
2. ✅ Test connection with test script
3. ⏭️ Update `app/pipeline.py` to use OpenAI as primary
4. ⏭️ Test with a sample meeting
5. ⏭️ Monitor token usage and costs

---

**Need help updating the pipeline code?** Let me know and I'll implement the changes!

