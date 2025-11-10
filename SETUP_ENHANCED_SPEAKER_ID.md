# Setup Guide: Enhanced Speaker Identification

This guide walks you through setting up the enhanced speaker identification system with Azure OpenAI (GPT-4).

## Prerequisites

- Python 3.8 or higher
- Active Azure subscription
- Access to Azure OpenAI Service

## Step 1: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `openai>=1.0.0` - Azure OpenAI client library
- All other existing dependencies

## Step 2: Create Azure OpenAI Resource

### 2.1 Create Resource in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Azure OpenAI"
4. Click "Create"
5. Fill in the required information:
   - **Subscription**: Your Azure subscription
   - **Resource group**: Create new or use existing
   - **Region**: Choose a region (e.g., East US, West Europe)
   - **Name**: Choose a unique name (e.g., `my-openai-resource`)
   - **Pricing tier**: Standard S0
6. Click "Review + Create" → "Create"

### 2.2 Deploy GPT-4 Model

1. Go to your Azure OpenAI resource
2. Click "Model deployments" → "Manage Deployments"
3. This opens Azure OpenAI Studio
4. Click "Deployments" → "Create new deployment"
5. Fill in deployment details:
   - **Model**: Select `gpt-4` or `gpt-4-turbo`
   - **Deployment name**: `gpt-4-turbo` (or your preferred name)
   - **Model version**: Latest available
6. Click "Create"

### 2.3 Get API Credentials

1. In Azure Portal, go to your Azure OpenAI resource
2. Click "Keys and Endpoint" in the left menu
3. Copy the following values:
   - **KEY 1** or **KEY 2** (either one works)
   - **Endpoint** (looks like: `https://your-resource.openai.azure.com/`)
4. Note the **API Version** from the overview (usually `2024-12-01-preview` or similar)
5. Note your **Deployment Name** from step 2.2

## Step 3: Configure Environment Variables

### 3.1 Create `.env` File

If you don't have a `.env` file yet:

```bash
cp env.example .env
```

### 3.2 Add Azure OpenAI Configuration

Edit `.env` and add your Azure OpenAI credentials:

```bash
# Azure OpenAI API for enhanced speaker identification
AZURE_OPENAI_API_KEY=your-actual-api-key-from-step-2.3
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo
```

**Replace:**
- `your-actual-api-key-from-step-2.3` with your KEY 1 or KEY 2
- `your-resource` with your actual resource name
- Deployment name if you chose a different one

### 3.3 (Optional) Keep Gemini for Fallback

For maximum reliability, also configure Gemini as a fallback:

```bash
# Google Gemini API Key for speaker identification (fallback)
GEMINI_API_KEY=your-gemini-api-key-here
```

Get a Gemini API key from: https://makersuite.google.com/app/apikey

## Step 4: Verify Configuration

### 4.1 Test the Application

Start the application:

```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

### 4.2 Process a Test Meeting

1. Open http://127.0.0.1:5000 in your browser
2. Log in (create an account if needed)
3. Submit a meeting URL
4. Watch the processing logs

You should see messages like:
```
🔍 Enhanced Speaker Extraction with GPT-4 (Multi-Pass)
  Pass 1: Extracting all speaker mentions...
  ✓ Found 12 speaker mentions
  Pass 2: Building speaker profiles with validation...
  ✓ Created profiles for 8 speakers

🚀 Enhanced Speaker Identification with GPT-4
   Total segments: 456
   Batch size: 50
   Overlap: 5 segments

   Detected 15 potential speaker boundaries
```

### 4.3 Verify Speaker Quality

After processing:
1. Check the `transcript_speakers.txt` file
2. Verify that speakers are correctly identified
3. Check for speaker name consistency

Expected improvement:
- **Before**: 2-5 unique speakers, often "Unknown Speaker"
- **After**: 5-15 unique speakers with names and organizations

## Troubleshooting

### Issue: "Azure OpenAI not configured"

**Cause**: Missing or incorrect environment variables

**Solution**:
1. Check that `.env` file exists in project root
2. Verify all four Azure OpenAI variables are set
3. Ensure no typos in variable names
4. Restart the application after changing `.env`

### Issue: "Authentication failed"

**Cause**: Invalid API key or endpoint

**Solution**:
1. Verify API key is correct (copy again from Azure Portal)
2. Check endpoint URL format (must include `https://` and trailing `/`)
3. Ensure the resource is active in Azure Portal

### Issue: "Deployment not found"

**Cause**: Deployment name mismatch

**Solution**:
1. Go to Azure OpenAI Studio → Deployments
2. Check the exact deployment name
3. Update `AZURE_OPENAI_DEPLOYMENT_NAME` in `.env`
4. Deployment names are case-sensitive

### Issue: "Rate limit exceeded"

**Cause**: Too many API calls

**Solution**:
1. Wait a few minutes and try again
2. Check your Azure OpenAI quota in Azure Portal
3. Consider reducing batch sizes in `app/pipeline.py`:
   ```python
   MAX_SEGMENTS_PER_GPT_BATCH = 30  # Reduce from 50
   ```

### Issue: Falls back to Gemini for all batches

**Cause**: GPT-4 processing is failing

**Solution**:
1. Check error messages in console
2. Verify model deployment is complete in Azure
3. Check API version compatibility
4. Try with a smaller test transcript first

### Issue: "Module 'openai' has no attribute 'AzureOpenAI'"

**Cause**: Old version of openai package

**Solution**:
```bash
pip install --upgrade openai>=1.0.0
```

## Cost Considerations

### Typical Costs (as of 2024)

For a 1-hour meeting (~1000 segments):

**Input tokens** (prompts):
- ~50,000 tokens per meeting
- GPT-4 Turbo: ~$0.50 per meeting

**Output tokens** (responses):
- ~30,000 tokens per meeting
- GPT-4 Turbo: ~$1.50 per meeting

**Total**: ~$2.00 per 1-hour meeting

### Cost Optimization Tips

1. **Use GPT-4 Turbo**: Much cheaper than GPT-4
2. **Tune batch sizes**: Larger batches = fewer API calls
3. **Use Gemini fallback**: Gemini is much cheaper
4. **Process selectively**: Only use GPT-4 for important meetings
5. **Monitor usage**: Check Azure Portal regularly

### Cost vs. Quality Trade-offs

| Configuration | Cost | Accuracy | Speed |
|--------------|------|----------|-------|
| GPT-4 only (small batches) | $$$$$ | Excellent | Slow |
| GPT-4 only (large batches) | $$$ | Very Good | Medium |
| GPT-4 + Gemini fallback | $$ | Very Good | Fast |
| Gemini only | $ | Good | Very Fast |

**Recommended**: GPT-4 + Gemini fallback for best reliability

## Best Practices

1. **Start Small**: Test with a short meeting first
2. **Monitor Costs**: Check Azure billing dashboard regularly
3. **Keep Both APIs**: Configure both Azure OpenAI and Gemini
4. **Review Quality**: Check a few results manually to ensure quality
5. **Adjust Parameters**: Tune batch sizes based on your meeting types

## Security Notes

1. **Never commit `.env`**: It contains sensitive API keys
2. **Use separate keys**: Different keys for dev/staging/prod
3. **Rotate keys regularly**: Change API keys every few months
4. **Monitor access**: Check Azure logs for unusual activity
5. **Limit permissions**: Use minimum required permissions

## Getting Help

If you encounter issues:

1. Check application logs: `logs/itu_intern.log`
2. Review Azure OpenAI logs in Azure Portal
3. Check [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
4. Test with a simple transcript first
5. Verify all dependencies are installed

## Next Steps

- Read [ENHANCED_SPEAKER_IDENTIFICATION.md](ENHANCED_SPEAKER_IDENTIFICATION.md) for detailed system information
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command reference
- Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details

---

**Setup Complete!** 🎉

The enhanced speaker identification system is now ready to use.

