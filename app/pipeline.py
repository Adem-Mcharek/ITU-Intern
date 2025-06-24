"""
WebTV Processing Pipeline - Enhanced Implementation
Based on the comprehensive standalone script with improvements for:
- Better UN WebTV URL handling
- Enhanced audio format selection (prioritizing English)
- **NEW: Integrated SRT to JSON conversion and Gemini speaker diarization**
- **NEW: Advanced speaker organization with database integration**
"""
import os
import re
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import timedelta
import threading
import random
import math

# Optional imports for AI functionality
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("Warning: yt-dlp not available. Video processing will be disabled.")

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
    TORCH_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    TORCH_AVAILABLE = False
    print("Warning: openai-whisper not available. Transcription will be disabled.")

try:
    import requests
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available. Speaker separation will be disabled.")

# Configuration constants
PARTNER_ID = "2503451"  # constant for all UN WebTV assets

# Gemini configuration from upgrade files
MODEL_NAME = "gemini-2.5-flash-lite-preview-06-17"
MAX_TOKENS_PER_BATCH = 10000  # Smaller batches to avoid truncated responses
ESTIMATED_TOKENS_PER_SEGMENT = 100  # Conservative estimate
MAX_SEGMENTS_PER_BATCH = MAX_TOKENS_PER_BATCH // ESTIMATED_TOKENS_PER_SEGMENT

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1  # Base delay in seconds
MAX_DELAY = 60  # Maximum delay in seconds

# Enhanced Gemini prompt for better speaker separation
GEMINI_PROMPT_FOR_CONTEXT = '''
You are an expert in transcript analysis and speaker identification.

Your task is to analyze the following transcript text and extract information about all the speakers mentioned.

Please identify:
1. Speaker names (when they introduce themselves or are introduced)
2. Their positions/titles (e.g., "Minister", "Undersecretary General", "CEO")
3. Organizations they represent (e.g., "UN Office for Digital and Emerging Technologies", "Dominican Republic", "World Bank")
4. Countries they represent (if applicable)

Look for patterns like:
- "My name is [Name]"
- Direct introductions: "Please welcome [Name] who is [Title] at [Organization]"
- References to titles and positions
- Country representations

Return your findings as a JSON object with this structure:
{
    "speakers": [
        {
            "name": "Speaker Name",
            "title": "Their title/position",
            "organization": "Organization they represent",
            "country": "Country (if applicable)",
            "description": "Brief description for identification"
        }
    ]
}

Transcript text:
'''

def setup_gemini_api():
    """Initialize Gemini API with configured key"""
    if not GEMINI_AVAILABLE:
        return None
    
    # Try to get API key from Flask config or environment
    api_key = None
    try:
        from flask import current_app
        api_key = current_app.config.get('GEMINI_API_KEY')
    except RuntimeError:
        # No Flask app context, try environment directly
        api_key = os.environ.get('GEMINI_API_KEY')
    
    if api_key:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(MODEL_NAME)
    return None

def _slug_to_entry_id(slug: str) -> str:
    """Convert UN WebTV slug to Kaltura entry ID."""
    if not slug.startswith("k1"):
        raise ValueError(f"Unexpected slug format: {slug}")
    return "1_" + slug[2:]

def _extract_slug(url: str) -> str:
    """Extract the slug from a UN WebTV URL."""
    m = re.search(r"/asset/[^/]+/([A-Za-z0-9]+)$", url)
    if not m:
        raise ValueError("URL does not look like a UN Web TV asset link.")
    return m.group(1)

def download_audio(url: str, out_dir: str) -> Tuple[Path, Dict]:
    """
    Enhanced UN WebTV audio download with English audio prioritization
    Returns: (audio_path, metadata)
    """
    if not YT_DLP_AVAILABLE:
        raise Exception("yt-dlp is not installed. Please install it to enable video processing.")
    
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Extract slug and convert to Kaltura URL for UN WebTV
        slug = _extract_slug(url)
        entry_id = _slug_to_entry_id(slug)
        kaltura_url = f"kaltura:{PARTNER_ID}:{entry_id}"
    except ValueError:
        # Fallback to original URL if not UN WebTV format
        kaltura_url = url
        slug = "unknown"
        entry_id = "unknown"
    
    # Enhanced format selector to prioritize English audio
    format_selectors = [
        # First priority: explicitly look for English audio
        "bestaudio[language=en]/bestaudio[language=eng]/bestaudio[language=English]",
        # Second priority: look for audio tracks that might contain "english" in description
        "bestaudio[format_note*=english]/bestaudio[format_note*=English]/bestaudio[format_note*=EN]",
        # Third priority: avoid known non-English languages and get best remaining
        "bestaudio[language!=ar][language!=ara][language!=arabic][language!=fr][language!=spa][language!=es]",
        # Final fallback: best audio
        "bestaudio/best"
    ]
    
    # Configure yt-dlp options for MP3 conversion
    audio_path = out_dir / 'audio.mp3'
    base = str(audio_path.with_suffix(''))
    
    ydl_opts = {
        'format': "/".join(format_selectors),
        'outtmpl': base + '.%(ext)s',
        'extractaudio': True,
        'audioformat': 'mp3',
        'audioquality': '192k',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
        'no_warnings': False,
        'quiet': False,
        'writeinfojson': True,  # This helps us see what languages are available
    }
    
    metadata = {}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First, extract info to see available formats
            try:
                info = ydl.extract_info(kaltura_url, download=False)
                formats = info.get('formats', [])
                
                # Extract metadata
                metadata = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'UN WebTV'),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', ''),
                    'formats_count': len(formats),
                    'slug': slug,
                    'entry_id': entry_id
                }
                
                # Log available audio formats
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                print(f"Found {len(audio_formats)} audio formats, prioritizing English")
                
            except Exception as e:
                print(f"Warning: Could not extract format info: {e}")
                metadata = {'title': 'Unknown', 'duration': 0, 'uploader': 'Unknown'}
            
            # Download with enhanced format selector
            ydl.download([kaltura_url])
            
            # Clean up info.json file
            info_json_path = out_dir / f"audio.info.json"
            if info_json_path.exists():
                info_json_path.unlink()
                
            # Ensure we have the MP3 file
            if not audio_path.exists():
                # Look for any audio file that was downloaded
                for file in out_dir.iterdir():
                    if file.suffix.lower() in ['.mp3', '.m4a', '.wav', '.ogg']:
                        file.rename(audio_path)
                        break
                        
            if not audio_path.exists():
                raise FileNotFoundError("Audio file not found after download")
                
            metadata['file_size'] = audio_path.stat().st_size
            
    except Exception as e:
        raise Exception(f"Failed to download audio: {str(e)}")
    
    return audio_path, metadata

def transcribe_audio(audio_path: Path, out_dir: str, model_size: str = "medium.en") -> Tuple[Path, Path]:
    """
    Enhanced transcription with GPU support and better error handling
    Returns: (transcript_path, srt_path)
    """
    if not WHISPER_AVAILABLE:
        raise Exception("openai-whisper is not installed. Please install it to enable transcription.")
    
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use GPU if available
        device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model '{model_size}' on {device.upper()}")
        
        # Load Whisper model
        model = whisper.load_model(model_size, device=device)
        
        # Transcribe with English language specification
        print(f"Transcribing audio using {device.upper()}")
        result = model.transcribe(str(audio_path), language="en", verbose=False)
        
        # Save raw transcript
        transcript_path = out_dir / 'transcript.txt'
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(result['text'].strip())
        
        # Generate enhanced SRT file
        srt_path = out_dir / 'transcript.srt'
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result['segments'], 1):
                start_time = format_srt_time(segment['start'])
                end_time = format_srt_time(segment['end'])
                text = segment['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        print(f"Transcription complete. Text: {len(result['text'])} chars, Segments: {len(result['segments'])}")
        return transcript_path, srt_path
        
    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {str(e)}")

def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"

# ===== NEW FUNCTIONS FROM UPGRADE FILES =====

def srt_to_json(srt_path: Path, json_path: Path):
    """Convert SRT file to JSON format - exact logic from srt_to_json.py"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    cues = []
    for match in re.finditer(r'(\d+)\n([\d:,]+) --> ([\d:,]+)\n(.*?)(?=\n\n\d+\n|$)', srt_content, re.DOTALL):
        index = int(match.group(1))
        start = match.group(2).replace(',', '.')
        end = match.group(3).replace(',', '.')
        text = match.group(4).strip().replace('\n', ' ')

        cues.append({
            "index": index,
            "start": start,
            "end": end,
            "speaker": "",
            "text": text
        })

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(cues, f, indent=2, ensure_ascii=False)
    
    print(f'Successfully converted {srt_path} to {json_path}')
    return cues

def estimate_tokens(text):
    """Rough estimation of tokens based on character count."""
    return len(text) // 3  # Rough approximation: ~3 chars per token

def extract_speaker_info_from_txt(transcript_text):
    """Extract speaker information from the full transcript text using Gemini API."""
    print("\nStep 1: Extracting speaker information from transcript.txt...")
    
    # Get API key
    api_key = None
    try:
        from flask import current_app
        api_key = current_app.config.get('GEMINI_API_KEY')
    except RuntimeError:
        api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("Warning: No Gemini API key found. Skipping speaker context extraction.")
        return {"speakers": []}
    
    if not GEMINI_AVAILABLE:
        print("Warning: Gemini not available. Skipping speaker context extraction.")
        return {"speakers": []}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        
        prompt = GEMINI_PROMPT_FOR_CONTEXT + transcript_text + "\n\nReturn ONLY the JSON object, no other text."
        
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip()
        
        # Clean up JSON markers
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        speaker_info = json.loads(cleaned_response.strip())
        
        print(f"Successfully extracted information for {len(speaker_info.get('speakers', []))} speakers:")
        for speaker in speaker_info.get('speakers', []):
            print(f"  - {speaker.get('name', 'Unknown')}: {speaker.get('title', '')} at {speaker.get('organization', '')}")
        
        return speaker_info
        
    except Exception as e:
        print(f"Error extracting speaker information: {e}")
        print("Continuing without speaker context...")
        return {"speakers": []}

def create_global_speaker_context(speaker_info):
    """Create a comprehensive speaker context from the extracted speaker information."""
    if not speaker_info.get('speakers'):
        return ""
    
    context = "\n\nKNOWN SPEAKERS IN THIS TRANSCRIPT:\n"
    context += "=" * 50 + "\n"
    
    for speaker in speaker_info.get('speakers', []):
        name = speaker.get('name', 'Unknown')
        title = speaker.get('title', '')
        org = speaker.get('organization', '')
        country = speaker.get('country', '')
        desc = speaker.get('description', '')
        
        context += f"• {name}"
        if title:
            context += f" - {title}"
        if org:
            context += f" at {org}"
        if country:
            context += f" (representing {country})"
        if desc:
            context += f"\n  Description: {desc}"
        context += "\n"
    
    context += "=" * 50 + "\n"
    context += "IMPORTANT: Use these EXACT speaker names when you recognize them in the transcript segments.\n"
    context += "For speakers not in this list, use descriptive labels like 'Participant 1', 'Moderator', etc.\n\n"
    
    return context

def create_batches(transcript_data, max_segments_per_batch):
    """Split transcript data into manageable batches."""
    batches = []
    for i in range(0, len(transcript_data), max_segments_per_batch):
        batch = transcript_data[i:i + max_segments_per_batch]
        batches.append(batch)
    
    print(f"Split transcript into {len(batches)} batches of maximum {max_segments_per_batch} segments each.")
    return batches

def create_speaker_context(all_filled_segments):
    """Create a context summary of identified speakers from previous batches."""
    speaker_examples = {}
    
    # Collect examples of each speaker's speech
    for segment in all_filled_segments:
        if segment.get("speaker") and segment["speaker"] != "":
            speaker_name = segment["speaker"]
            if speaker_name not in speaker_examples:
                speaker_examples[speaker_name] = []
            
            # Store up to 2 examples per speaker
            if len(speaker_examples[speaker_name]) < 2:
                speaker_examples[speaker_name].append(segment["text"][:200])  # First 200 chars
    
    if not speaker_examples:
        return ""
    
    context = "\n\nPreviously identified speakers in earlier batches:\n"
    for speaker, examples in speaker_examples.items():
        context += f"- {speaker}: {' | '.join(examples)}\n"
    
    return context

def call_gemini_with_retry(model, prompt, batch_number, total_batches):
    """Call Gemini API with retry logic and exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  Attempt {attempt + 1}/{MAX_RETRIES} for batch {batch_number}/{total_batches}...")
            response = model.generate_content(prompt)
            return response
        
        except Exception as e:
            error_msg = str(e)
            print(f"  Attempt {attempt + 1} failed: {error_msg}")
            
            # If this is the last attempt, don't wait
            if attempt == MAX_RETRIES - 1:
                print(f"  All {MAX_RETRIES} attempts failed for batch {batch_number}")
                return None
            
            # Calculate delay with exponential backoff and jitter
            delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
            print(f"  Waiting {delay:.1f} seconds before retry...")
            time.sleep(delay)
    
    return None

def fill_speakers_in_batch(batch_data, batch_number, total_batches, global_speaker_context="", previous_speaker_context=""):
    """Uses the Gemini API to fill in the speaker fields for a batch of transcript segments."""
    print(f"\nStep 2: Processing batch {batch_number}/{total_batches} ({len(batch_data)} segments)...")

    batch_string = json.dumps(batch_data, indent=2)
    
    # Estimate tokens for this batch
    estimated_tokens = estimate_tokens(batch_string)
    print(f"Estimated tokens for this batch: {estimated_tokens}")
    
    if estimated_tokens > MAX_TOKENS_PER_BATCH:
        print(f"WARNING: Batch may exceed token limit. Consider reducing MAX_SEGMENTS_PER_BATCH.")

    # Get API key
    api_key = None
    try:
        from flask import current_app
        api_key = current_app.config.get('GEMINI_API_KEY')
    except RuntimeError:
        api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("Warning: No Gemini API key found. Returning batch with empty speakers.")
        return batch_data
    
    if not GEMINI_AVAILABLE:
        print("Warning: Gemini not available. Returning batch with empty speakers.")
        return batch_data

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=MODEL_NAME)
    except Exception as e:
        print(f"Error setting up Gemini model: {e}")
        return batch_data

    prompt = f"""
You are an expert in transcript analysis and speaker diarization.
Your task is to analyze the following JSON transcript batch (part {batch_number} of {total_batches}). 
This transcript contains segments of speech, each with an empty "speaker" field.

Based on the content of the "text" field in each segment, identify who is speaking. 
Use the speaker information and context provided below to maintain accurate and consistent speaker labels.

{global_speaker_context}

{previous_speaker_context}

INSTRUCTIONS:
1. Use the EXACT speaker names from the "KNOWN SPEAKERS" list when you recognize them
3. Maintain consistency with speakers identified in previous batches
4. Base your identification on speech patterns, content, and context clues

Please return the **complete and valid JSON object**, identical in structure to the input, 
but with the "speaker" field correctly filled for every segment.

Input Transcript Batch:
```json
{batch_string}
```

Your output should be ONLY the filled JSON, starting with `[` and ending with `]`.
"""

    # Call Gemini with retry logic
    response = call_gemini_with_retry(model, prompt, batch_number, total_batches)
    
    if response is None:
        print(f"\nFailed to get response from Gemini API after {MAX_RETRIES} attempts for batch {batch_number}")
        return batch_data

    try:
        # Clean up the response to ensure it's valid JSON
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        # Check if JSON response appears to be truncated
        cleaned_response = cleaned_response.strip()
        if not cleaned_response.endswith(']') and not cleaned_response.endswith('}'):
            print(f"Warning: Response appears to be truncated for batch {batch_number}")
            print(f"Response ends with: '{cleaned_response[-50:]}'")
            raise ValueError("Response appears to be truncated - incomplete JSON")

        filled_data = json.loads(cleaned_response)
        
        # Validate that we got the expected number of segments
        if len(filled_data) != len(batch_data):
            print(f"Warning: Expected {len(batch_data)} segments, got {len(filled_data)} for batch {batch_number}")
            raise ValueError(f"Segment count mismatch: expected {len(batch_data)}, got {len(filled_data)}")
        
        print(f"Successfully processed batch {batch_number}/{total_batches}")
        return filled_data
    except Exception as e:
        print(f"\nAn error occurred while parsing response for batch {batch_number}: {e}")
        print("--- API Response Text ---")
        try:
            response_preview = response.text[:2000] + "..." if len(response.text) > 2000 else response.text
            print(response_preview)
            print(f"\nResponse length: {len(response.text)} characters")
            print(f"Response ends with: '{response.text[-100:]}'")
        except:
            print("Could not display response text")
        print("------------------------")
        return batch_data

def fill_speakers_in_json(transcript_data, global_speaker_context):
    """Uses the Gemini API to fill in the speaker fields in a transcript JSON using batching."""
    print(f"\nStep 2: Processing transcript with {len(transcript_data)} segments...")
    
    # Create batches
    batches = create_batches(transcript_data, MAX_SEGMENTS_PER_BATCH)
    
    all_filled_segments = []
    
    for i, batch in enumerate(batches, 1):
        # Create speaker context from previously processed segments
        previous_speaker_context = create_speaker_context(all_filled_segments)
        
        # Process the batch with both global and previous context
        filled_batch = fill_speakers_in_batch(
            batch, i, len(batches), 
            global_speaker_context, 
            previous_speaker_context
        )
        
        if filled_batch is None:
            print(f"Failed to process batch {i}. Using original data.")
            filled_batch = batch
        
        # Add to our collection of filled segments
        all_filled_segments.extend(filled_batch)
    
    print(f"\nSuccessfully processed all {len(batches)} batches.")
    print(f"Total segments processed: {len(all_filled_segments)}")
    
    return all_filled_segments

def parse_speaker_info(speaker_name):
    """Advanced parser to extract speaker name and representing organization/country - exact logic from organize_speakers_table.py"""
    if not speaker_name or speaker_name.strip() == "":
        return "Unknown Speaker", "Unknown"
    
    speaker_name = speaker_name.strip()
    original_name = speaker_name
    
    import re
    
    # Define comprehensive patterns and keywords
    country_indicators = [
        'Afghanistan', 'Albania', 'Algeria', 'Argentina', 'Australia', 'Austria', 'Bangladesh', 
        'Belgium', 'Brazil', 'Canada', 'China', 'Colombia', 'Denmark', 'Egypt', 'France', 
        'Germany', 'India', 'Indonesia', 'Iran', 'Iraq', 'Italy', 'Japan', 'Jordan', 
        'Kenya', 'Malaysia', 'Mexico', 'Morocco', 'Netherlands', 'Nigeria', 'Norway', 
        'Pakistan', 'Philippines', 'Poland', 'Russia', 'Saudi Arabia', 'South Africa', 
        'Spain', 'Sweden', 'Switzerland', 'Turkey', 'Ukraine', 'United Kingdom', 'UK', 
        'United States', 'USA', 'Venezuela', 'Vietnam', 'Yemen', 'Zimbabwe',
        'Dominican Republic', 'East African'
    ]
    
    org_indicators = [
        'UN', 'United Nations', 'UNESCO', 'UNICEF', 'WHO', 'IMF', 'World Bank',
        'European Union', 'EU', 'African Union', 'AU', 'ASEAN', 'NATO', 'OSCE',
        'Ministry', 'Department', 'Office', 'Committee', 'Council', 'Commission',
        'Organization', 'Organisation', 'Government', 'Embassy', 'Delegation',
        'Secretariat', 'Agency', 'Bureau', 'Institute', 'Foundation', 'Society',
        'Association', 'Federation', 'Union', 'Alliance', 'Coalition',
        'ADB', 'Asian Development Bank', 'Drupal', 'Project Liberty'
    ]
    
    title_indicators = [
        'Secretary-General', 'Secretary General', 'Undersecretary', 'Under-Secretary',
        'Assistant Secretary', 'Special Representative', 'Special Envoy', 'Special Advisor',
        'Ambassador', 'Permanent Representative', 'Minister', 'Deputy Minister',
        'Director-General', 'Director General', 'Executive Director', 'President',
        'Vice President', 'Chairman', 'Chair', 'Moderator', 'Commissioner',
        'Representative', 'Delegate', 'Coordinator', 'Adviser', 'Advisor', 'CEO',
        'Expert', 'Analyst', 'Consultant', 'Researcher'
    ]
    
    # Pattern 1: "Name (Organization/Country)"
    paren_match = re.match(r'^(.+?)\s*\((.+?)\)$', speaker_name)
    if paren_match:
        name_part = paren_match.group(1).strip()
        org_part = paren_match.group(2).strip()
        return name_part, org_part
    
    # Pattern 2: "Name - Organization" or "Name – Organization"
    dash_match = re.match(r'^(.+?)\s*[–-]\s*(.+)$', speaker_name)
    if dash_match:
        name_part = dash_match.group(1).strip()
        org_part = dash_match.group(2).strip()
        return name_part, org_part
    
    # Pattern 3: "Name, Title, Organization"
    comma_parts = speaker_name.split(',')
    if len(comma_parts) >= 2:
        name_part = comma_parts[0].strip()
        remaining = ', '.join(comma_parts[1:]).strip()
        # Check if remaining parts contain organization indicators
        if any(indicator.lower() in remaining.lower() for indicator in org_indicators + country_indicators):
            return name_part, remaining
    
    # Pattern 4: "Organization: Name" or "Country: Name"
    colon_match = re.match(r'^(.+?):\s*(.+)$', speaker_name)
    if colon_match:
        first_part = colon_match.group(1).strip()
        second_part = colon_match.group(2).strip()
        # Usually organization comes first in this pattern
        return second_part, first_part
    
    # Pattern 5: Check for titles that indicate representing organization
    for title in title_indicators:
        if title.lower() in speaker_name.lower():
            # Look for "of", "for", "from" patterns
            title_patterns = [
                rf'{re.escape(title)}\s+(?:of|for|from)\s+(.+?)(?:\s|$)',
                rf'(.+?)\s+{re.escape(title)}',  # "Country Minister"
                rf'{re.escape(title)}.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'  # Extract proper nouns after title
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, speaker_name, re.IGNORECASE)
                if title_match:
                    org_extract = title_match.group(1).strip()
                    if len(org_extract) > 2:  # Avoid single letters
                        # If it's a known country or organization
                        if any(indicator.lower() in org_extract.lower() for indicator in country_indicators + org_indicators):
                            return speaker_name, org_extract
    
    # Pattern 6: Country names in speaker name
    for country in country_indicators:
        if country.lower() in speaker_name.lower():
            # Check for government context
            if any(word in speaker_name.lower() for word in ['minister', 'government', 'representative', 'ambassador']):
                return speaker_name, f"{country} Government"
            else:
                return speaker_name, country
    
    # Pattern 7: Organization names in speaker name
    for org in org_indicators:
        if org.lower() in speaker_name.lower():
            # Special handling for specific organizations
            if "world bank" in speaker_name.lower():
                return speaker_name, "World Bank"
            elif "asian development bank" in speaker_name.lower() or "adb" in speaker_name.lower():
                return speaker_name, "Asian Development Bank"
            elif "drupal" in speaker_name.lower():
                return speaker_name, "Drupal Foundation"
            elif "project liberty" in speaker_name.lower():
                return speaker_name, "Project Liberty Institute"
            elif "east african" in speaker_name.lower():
                return speaker_name, "East African Community"
            elif "un" in speaker_name.lower() or "united nations" in speaker_name.lower():
                # Try to be more specific about UN agency
                if "office" in speaker_name.lower():
                    return speaker_name, "UN Office"
                elif "special" in speaker_name.lower():
                    return speaker_name, "UN Special Office"
                else:
                    return speaker_name, "United Nations"
            else:
                return speaker_name, org
    
    # Pattern 8: Special cases for common roles
    special_cases = {
        'moderator': 'Event Moderator',
        'chair': 'Session Chair', 
        'chairperson': 'Session Chair',
        'host': 'Event Host',
        'facilitator': 'Session Facilitator'
    }
    
    for role, representing in special_cases.items():
        if role.lower() in speaker_name.lower():
            return speaker_name, representing
    
    # Pattern 9: If name contains "of" followed by organization/country
    of_pattern = r'^(.+?)\s+of\s+(.+)$'
    of_match = re.match(of_pattern, speaker_name, re.IGNORECASE)
    if of_match:
        name_part = of_match.group(1).strip()
        org_part = of_match.group(2).strip()
        # Clean up common artifacts
        if org_part.startswith("the "):
            org_part = org_part[4:]
        return name_part, org_part
    
    # Pattern 10: Check if entire name is just an organization
    if any(indicator.lower() in speaker_name.lower() for indicator in org_indicators):
        # If it's mostly uppercase or contains clear org indicators
        if speaker_name.isupper() or any(word in speaker_name.lower() for word in ['ministry', 'department', 'office', 'un ']):
            return speaker_name, speaker_name
    
    # Pattern 11: Look for name patterns (First Last format) vs organization patterns
    words = speaker_name.split()
    if len(words) >= 2:
        # Check if it looks like a person's name (First Last pattern)
        if (words[0][0].isupper() and words[1][0].isupper() and 
            len(words[0]) > 1 and len(words[1]) > 1 and
            not any(indicator.lower() in speaker_name.lower() for indicator in org_indicators)):
            # Looks like a person's name without clear organization
            return speaker_name, "Not specified"
    
    # Clean up the speaker name (remove excessive descriptive text)
    clean_name = speaker_name
    if " - " in clean_name and len(clean_name.split(" - ")) == 2:
        parts = clean_name.split(" - ")
        if len(parts[0]) < len(parts[1]):  # Shorter part is likely the name
            clean_name = parts[0].strip()
        else:
            clean_name = parts[1].strip()
    elif " (" in clean_name:
        clean_name = clean_name.split(" (")[0].strip()
    
    # Default case: No clear organization pattern found
    return clean_name, "Not specified"

def group_consecutive_segments(transcript_data):
    """Group consecutive segments from the same speaker into single entries - exact logic from organize_speakers_table.py"""
    if not transcript_data:
        return []
    
    # Helper function to safely convert time to float
    def safe_time_convert(time_value, default=0.0):
        try:
            if time_value is None:
                return default
            
            # If it's already a number, return it
            if isinstance(time_value, (int, float)):
                return float(time_value)
            
            # If it's a string in HH:MM:SS.mmm format, convert to seconds
            if isinstance(time_value, str) and ':' in time_value:
                time_parts = time_value.split(':')
                if len(time_parts) == 3:
                    hours = float(time_parts[0])
                    minutes = float(time_parts[1])
                    seconds = float(time_parts[2])
                    return hours * 3600 + minutes * 60 + seconds
            
            # Try to convert as is
            return float(time_value)
            
        except (ValueError, TypeError):
            return default
    
    grouped_segments = []
    current_group = {
        'speaker': transcript_data[0].get('speaker', 'Unknown'),
        'text_parts': [transcript_data[0].get('text', '')],
        'start_time': safe_time_convert(transcript_data[0].get('start', 0)),
        'end_time': safe_time_convert(transcript_data[0].get('end', 0)),
        'segment_count': 1
    }
    
    for i in range(1, len(transcript_data)):
        segment = transcript_data[i]
        current_speaker = segment.get('speaker', 'Unknown')
        previous_speaker = current_group['speaker']
        
        # If same speaker, add to current group
        if current_speaker == previous_speaker:
            current_group['text_parts'].append(segment.get('text', ''))
            current_group['end_time'] = safe_time_convert(segment.get('end', current_group['end_time']))
            current_group['segment_count'] += 1
        else:
            # Different speaker, save current group and start new one
            current_group['combined_text'] = ' '.join(current_group['text_parts'])
            grouped_segments.append(current_group.copy())
            
            # Start new group
            current_group = {
                'speaker': current_speaker,
                'text_parts': [segment.get('text', '')],
                'start_time': safe_time_convert(segment.get('start', 0)),
                'end_time': safe_time_convert(segment.get('end', 0)),
                'segment_count': 1
            }
    
    # Don't forget the last group
    current_group['combined_text'] = ' '.join(current_group['text_parts'])
    grouped_segments.append(current_group)
    
    return grouped_segments

def create_speakers_table(transcript_data, meeting_id):
    """Create a structured table from the transcript data matching the database schema - exact logic from organize_speakers_table.py"""
    print(f"Processing {len(transcript_data)} transcript segments...")
    
    # Group consecutive segments from same speaker
    grouped_segments = group_consecutive_segments(transcript_data)
    print(f"Grouped into {len(grouped_segments)} speaker turns...")
    
    # Create table data
    table_data = []
    
    for i, group in enumerate(grouped_segments):
        speaker_name = group['speaker']
        clean_speaker, representing = parse_speaker_info(speaker_name)
        
        # Create row matching the database schema
        row = {
            'speaker': clean_speaker,
            'representing': representing,
            'content': group['combined_text'],
            'start_time': group['start_time'],
            'end_time': group['end_time'],
            'duration_seconds': group['end_time'] - group['start_time'],
            'segment_count': group['segment_count']  # Extra info: how many segments were combined
        }
        
        table_data.append(row)
    
    return table_data

def run_full_pipeline(url: str, title: str, target_dir: str) -> Dict:
    """
    Run the enhanced WebTV processing pipeline with the new logic from upgrade files
    Returns: Dictionary with file paths and processing results
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'audio': None,
        'transcript': None,
        'srt': None,
        'speakers': None,
        'segments': [],
        'metadata': {},
        'errors': []
    }
    
    try:
        print(f"Starting enhanced pipeline for: {title}")
        
        # Step 1: Download audio with English prioritization
        print("Step 1: Downloading audio...")
        audio_path, metadata = download_audio(url, str(target_dir))
        results['audio'] = str(audio_path.relative_to(target_dir.parent))
        results['metadata'] = metadata
        
        # Step 2: Transcribe audio with GPU support
        print("Step 2: Transcribing audio...")
        transcript_path, srt_path = transcribe_audio(audio_path, str(target_dir))
        results['transcript'] = str(transcript_path.relative_to(target_dir.parent))
        results['srt'] = str(srt_path.relative_to(target_dir.parent))
        
        # Step 3: Convert SRT to JSON using exact logic from srt_to_json.py
        print("Step 3: Converting SRT to JSON...")
        json_path = target_dir / 'transcript.json'
        transcript_json = srt_to_json(srt_path, json_path)
        
        # Step 4: Extract speaker context from full transcript using Gemini
        print("Step 4: Extracting speaker context from transcript...")
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        speaker_info = extract_speaker_info_from_txt(transcript_text)
        global_speaker_context = create_global_speaker_context(speaker_info)
        
        # Step 5: Fill speaker information using exact logic from gemini_speaker_diarization_copy.py
        print("Step 5: Filling speaker information using Gemini...")
        filled_transcript = fill_speakers_in_json(transcript_json, global_speaker_context)
        
        # Save filled transcript
        filled_json_path = target_dir / 'transcript_speaker_filled.json'
        with open(filled_json_path, 'w', encoding='utf-8') as f:
            json.dump(filled_transcript, f, indent=2, ensure_ascii=False)
        
        # Step 6: Create structured segments using exact logic from organize_speakers_table.py
        print("Step 6: Creating structured speaker segments...")
        structured_segments = create_speakers_table(filled_transcript, 1)  # meeting_id will be set by calling function
        
        # Step 7: Create speaker transcript file
        print("Step 7: Creating speaker transcript file...")
        speakers_path = target_dir / 'transcript_speakers.txt'
        with open(speakers_path, 'w', encoding='utf-8') as f:
            f.write(f"# Speaker-separated transcript for: {title}\n\n")
            for segment in structured_segments:
                speaker = segment['speaker']
                representing = segment['representing']
                content = segment['content']
                start_time = segment['start_time']
                end_time = segment['end_time']
                
                # Format speaker header
                if representing and representing != "Not specified":
                    speaker_header = f"[{speaker}, {representing}]"
                else:
                    speaker_header = f"[{speaker}]"
                
                # Add timing if available
                if start_time is not None and end_time is not None:
                    # Format timing as MM:SS for readability
                    start_min = int(start_time // 60)
                    start_sec = int(start_time % 60)
                    end_min = int(end_time // 60)
                    end_sec = int(end_time % 60)
                    timing_info = f" ({start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d})"
                    speaker_header += timing_info
                
                f.write(f"{speaker_header}\n")
                f.write(f"{content}\n\n")
        
        results['speakers'] = str(speakers_path.relative_to(target_dir.parent))
        results['segments'] = structured_segments
        
        print("Pipeline completed successfully!")
        
        # Clean up intermediate files
        print("Cleaning up intermediate files...")
        if json_path.exists():
            json_path.unlink()
        if filled_json_path.exists():
            filled_json_path.unlink()
        
    except Exception as e:
        error_msg = str(e)
        results['errors'].append(error_msg)
        print(f"Pipeline failed: {error_msg}")
        raise
    
    return results 