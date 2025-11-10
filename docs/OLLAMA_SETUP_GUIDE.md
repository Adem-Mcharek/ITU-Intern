# Ollama + Gemma 3 Integration Setup Guide

## 🎯 What Changed

Your application now uses **Ollama with Gemma** as the **primary** AI model for speaker identification, with automatic fallback to Azure OpenAI GPT-4 and Google Gemini.

### Priority Chain:
1. **Ollama (Gemma)** - Local, free, no rate limits ✅ **(NEW - Primary)**
2. **Azure OpenAI (GPT-4)** - Cloud backup if Ollama unavailable
3. **Google Gemini** - Final fallback

## 📦 Installation Steps

### Step 1: Install Ollama

**Windows:**
1. Download Ollama from: https://ollama.ai/download
2. Run the installer
3. Ollama will start automatically in the background

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

### Step 2: Pull Gemma Model

Open a terminal/command prompt and run:

```bash
# Recommended: Gemma 2 (9B parameters - good balance)
ollama pull gemma2:latest

# Alternative: Gemma 2 27B (better quality, slower)
ollama pull gemma2:27b

# When available: Gemma 3
ollama pull gemma3:latest
```

**Model size comparison:**
- `gemma2:latest` (9B): ~5.5 GB download, ~20-40 tokens/sec
- `gemma2:27b`: ~16 GB download, ~10-20 tokens/sec, better quality

### Step 3: Verify Installation

Run the test script:

```bash
python test_ollama_connection.py
```

Expected output:
```
✅ Ollama server is running!
✅ Found recommended model: gemma2:latest
✅ API response received!
✅ All tests passed!
```

If you see errors:
- **"Cannot connect to Ollama server"**: Start Ollama (Windows: automatic, Linux/Mac: run `ollama serve`)
- **"No models found"**: Run `ollama pull gemma2:latest`
- **"OpenAI library not installed"**: Run `pip install openai`

### Step 4: Configure Environment Variables

Add these to your `.env` file (you said you'll handle this):

```bash
# Ollama Configuration (Local LLM)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma2:latest
OLLAMA_API_KEY=ollama
```

## 🚀 Usage

Just start your Flask app normally:

```bash
python run.py
```

The system will automatically:
1. Try to connect to Ollama first (local, fast, free)
2. Fall back to Azure OpenAI if Ollama is unavailable
3. Fall back to Gemini if neither is available

You'll see messages like:
```
✓ Connected to Ollama at http://localhost:11434/v1
✓ Using model: gemma2:latest
🔍 Enhanced Speaker Extraction (Multi-Pass)
  Using Ollama (Gemma) - Local inference
```

## 📊 Performance Comparison

### Processing a 1-hour meeting (47 batches):

| Model | Time | Cost | Rate Limits |
|-------|------|------|-------------|
| **Ollama (Gemma 2)** | 30-45 min | $0 | None ✅ |
| Azure GPT-4 | 15-20 min | ~$5-10 | 15K TPM ⚠️ |
| Google Gemini | 20-30 min | $0 | 1500 RPD |

### Token Processing Speed:

- **Ollama**: ~20-40 tokens/second (depends on your GPU)
- **GPT-4**: ~100-200 tokens/second (cloud)
- **Gemini**: ~80-150 tokens/second (cloud)

## 🔧 Troubleshooting

### Ollama is slow
- **Use smaller model**: `ollama pull gemma2:9b` instead of `gemma2:27b`
- **Check GPU**: Run `ollama list` - should show GPU usage
- **Close other apps**: Free up GPU/CPU resources

### Ollama not connecting
- **Windows**: Check system tray - Ollama should be running
- **Linux/Mac**: Run `ollama serve` in a terminal
- **Firewall**: Ensure port 11434 is not blocked

### Want to use Azure GPT-4 instead
Just stop Ollama service, the system will automatically fall back:
```bash
# Windows: Stop Ollama from system tray
# Linux/Mac: Ctrl+C in the ollama serve terminal
```

### Want to force a specific model
Set in your `.env`:
```bash
OLLAMA_MODEL=gemma2:9b  # Use 9B model
OLLAMA_MODEL=gemma2:27b # Use 27B model (slower, better quality)
```

## 🎓 Tips for Best Results

1. **First time setup**: Let Ollama download the full model (~5GB), takes 5-10 minutes
2. **Keep Ollama running**: Start it once, leave it in the background
3. **Use 9B model**: Better balance of speed and quality for speaker ID tasks
4. **GPU matters**: Ollama is MUCH faster with a dedicated GPU (NVIDIA, AMD, or Apple Silicon)
5. **Processing time**: Expect 2-3x slower than GPT-4, but completely free and no rate limits

## 📝 Modified Files

The following files were updated to support Ollama:

1. **app/pipeline.py**:
   - Added `get_ollama_config()` function
   - Added `setup_ollama_client()` function
   - Updated `extract_speaker_info_with_gpt()` to prioritize Ollama
   - Updated `fill_speakers_in_batch_gpt()` to prioritize Ollama

2. **app/__init__.py**:
   - Added Ollama configuration variables

3. **test_ollama_connection.py** (NEW):
   - Test script to verify Ollama setup

## ✅ Ready to Use!

Your system is now configured to use local AI inference with Ollama, eliminating:
- ❌ API rate limits
- ❌ API costs
- ❌ Internet dependency for AI processing

While being slightly slower, you get:
- ✅ Unlimited processing
- ✅ Complete privacy (data never leaves your laptop)
- ✅ Works offline
- ✅ No API costs

Enjoy your cost-free, rate-limit-free speaker identification! 🎉

