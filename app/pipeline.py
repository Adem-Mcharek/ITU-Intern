"""
WebTV Processing Pipeline - Enhanced Implementation
Based on the comprehensive standalone script with improvements for:
- Better UN WebTV URL handling
- Enhanced audio format selection (prioritizing English)
- Chunking for Gemini API
- Robust error handling and retries
- **NEW: SRT timing integration with speaker segments**
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
from difflib import SequenceMatcher

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
except ImportError:
    WHISPER_AVAILABLE = False
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
CHUNK_SIZE = 12000  # characters for Gemini chunking
OVERLAP = 500  # overlap between chunks

# Enhanced Gemini prompt for better speaker separation
GEMINI_PROMPT = '''You are a helpful assistant who reads a transcript or meeting text. Your task is to split it into segments, each with a clear speaker label, as in the following format:

[SPEAKER NAME]
Content ...

Identify chair, panelists, delegates, and use their titles, country, or best-guess if the name is unclear. Skip repetitive formalities, focus on main interventions. Keep speaker turns clear and readable.

Example:
[Chair]
Thank you. The meeting is called to order...

[Mr. Smith, UNDP]
Thank you, Chair. Our work this year focused on...

---
Here is the transcript to process:
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
        return genai.GenerativeModel('gemini-pro')
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
        device = "cuda" if torch.cuda.is_available() else "cpu"
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

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    """Split long text into overlapping chunks for Gemini processing."""
    starts = range(0, len(text), chunk_size - overlap)
    return [text[s:s + chunk_size] for s in starts]

def _parse_gemini_response(data: dict) -> str:
    """Safely extract generated text from Gemini response JSON."""
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError):
        return ""

def _call_gemini_rest(prompt: str, api_key: str, max_out_tokens: int = 2048, retry: bool = True) -> str:
    """Call Gemini API directly using REST API."""
    model = "gemini-1.5-flash"
    rest_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_out_tokens,
        },
    }
    
    try:
        resp = requests.post(
            rest_url, 
            headers={"Content-Type": "application/json"}, 
            data=json.dumps(payload), 
            timeout=90
        )
        
        if resp.status_code != 200:
            error_msg = f"Gemini API error {resp.status_code}: {resp.text[:400]}"
            print(f"ERROR: {error_msg}")
            if retry:
                print("Retrying with smaller output...")
                time.sleep(2)
                return _call_gemini_rest(prompt, api_key, max_out_tokens=1024, retry=False)
            raise RuntimeError(error_msg)

        data = resp.json()
        text = _parse_gemini_response(data)

        # If no text and we haven't retried yet
        if text == "" and retry:
            new_max = max(int(max_out_tokens * 0.5), 512)
            print(f"No text in response. Retrying with max_tokens={new_max}...")
            time.sleep(2)
            return _call_gemini_rest(prompt, api_key, max_out_tokens=new_max, retry=False)

        return text
    except Exception as e:
        if retry:
            print(f"Error calling Gemini API: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            return _call_gemini_rest(prompt, api_key, max_out_tokens=max_out_tokens, retry=False)
        raise

def separate_speakers(transcript_path: Path, out_dir: str, meeting_title: str = "") -> Tuple[Path, List[Dict]]:
    """
    Enhanced speaker separation using chunking and improved prompts
    Returns: (speakers_transcript_path, segments_list)
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    # Get API key
    api_key = None
    try:
        from flask import current_app
        api_key = current_app.config.get('GEMINI_API_KEY')
    except RuntimeError:
        api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("Warning: No Gemini API key found. Creating fallback speaker transcript.")
        return create_fallback_speakers(transcript_text, out_dir)
    
    try:
        print(f"Processing transcript ({len(transcript_text)} characters) with Gemini")
        
        if len(transcript_text) <= CHUNK_SIZE:
            # Single chunk processing
            full_prompt = GEMINI_PROMPT + transcript_text
            result_text = _call_gemini_rest(full_prompt, api_key)
        else:
            # Multi-chunk processing
            chunks = chunk_text(transcript_text)
            outputs = []
            total = len(chunks)
            
            print(f"Processing transcript in {total} chunks")
            for idx, chunk in enumerate(chunks, 1):
                print(f"Processing chunk {idx}/{total}")
                chunk_prompt = GEMINI_PROMPT + f"(Part {idx} of {total})\n" + chunk
                chunk_result = _call_gemini_rest(chunk_prompt, api_key)
                outputs.append(chunk_result)
                
                # Small delay between requests
                if idx < total:
                    time.sleep(1)
            
            result_text = "\n\n".join(outputs)
        
        # Parse the result into segments
        segments = parse_speaker_response(result_text)
        
        # Save speaker-separated transcript
        speakers_path = out_dir / 'transcript_speakers.txt'
        with open(speakers_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
        
        print(f"Speaker separation complete. Generated {len(segments)} segments.")
        return speakers_path, segments
        
    except Exception as e:
        print(f"Speaker separation failed: {e}")
        # Fallback to simple speaker separation
        return create_fallback_speakers(transcript_text, out_dir)

def create_fallback_speakers(transcript_text: str, out_dir: Path) -> Tuple[Path, List[Dict]]:
    """Create a fallback speaker transcript when AI processing fails."""
    segments = [{
        'speaker': 'Unknown Speaker',
        'representing': '',
        'content': transcript_text.strip(),
        'start_time': None,
        'end_time': None
    }]
    
    speakers_path = out_dir / 'transcript_speakers.txt'
    with open(speakers_path, 'w', encoding='utf-8') as f:
        f.write("# Speaker separation unavailable - showing original transcript\n\n")
        f.write("[Unknown Speaker]\n")
        f.write(transcript_text)
    
    return speakers_path, segments

def parse_speaker_response(response_text: str) -> List[Dict]:
    """Parse Gemini's response to extract speaker segments."""
    segments = []
    lines = response_text.split('\n')
    current_segment = {}
    
    for line in lines:
        line = line.strip()
        
        # Look for speaker headers like [Speaker Name] or [Chair]
        speaker_match = re.match(r'\[([^\]]+)\]', line)
        if speaker_match:
            # Save previous segment if it exists
            if current_segment.get('content'):
                segments.append(current_segment)
            
            # Start new segment
            speaker_full = speaker_match.group(1)
            
            # Try to parse speaker and representing
            if ',' in speaker_full:
                parts = speaker_full.split(',', 1)
                speaker = parts[0].strip()
                representing = parts[1].strip()
            else:
                speaker = speaker_full.strip()
                representing = ''
            
            current_segment = {
                'speaker': speaker,
                'representing': representing,
                'content': '',
                'start_time': None,
                'end_time': None
            }
        elif current_segment and line and not line.startswith('#'):
            # Add content to current segment
            current_segment['content'] += line + ' '
    
    # Add final segment
    if current_segment.get('content'):
        segments.append(current_segment)
    
    # Clean up content
    for segment in segments:
        segment['content'] = segment['content'].strip()
    
    return segments

def parse_srt_file(srt_path: Path) -> List[Dict]:
    """
    Parse SRT file to extract timing and content information
    Returns: List of segments with start_time, end_time, and content
    """
    segments = []
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except Exception as e:
        print(f"Warning: Could not read SRT file {srt_path}: {e}")
        return segments
    
    # Split by double newlines to get individual segments
    srt_blocks = re.split(r'\n\s*\n', content)
    
    for block in srt_blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
            
        try:
            # Line 1: sequence number (ignore)
            # Line 2: timing
            timing_line = lines[1]
            # Line 3+: content
            text_content = ' '.join(lines[2:]).strip()
            
            # Parse timing: "00:00:00,000 --> 00:00:06,799"
            timing_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timing_line)
            if not timing_match:
                continue
                
            # Convert to seconds
            start_h, start_m, start_s, start_ms = map(int, timing_match.groups()[:4])
            end_h, end_m, end_s, end_ms = map(int, timing_match.groups()[4:])
            
            start_seconds = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000.0
            end_seconds = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000.0
            
            segments.append({
                'start_time': start_seconds,
                'end_time': end_seconds,
                'content': text_content
            })
            
        except Exception as e:
            print(f"Warning: Could not parse SRT block: {e}")
            continue
    
    print(f"Parsed {len(segments)} segments from SRT file")
    return segments

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings (0-1) with improved normalization"""
    # Normalize texts more aggressively
    def normalize_text(text):
        # Remove punctuation, extra spaces, convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Remove common filler words that might not match exactly
        text = re.sub(r'\b(um|uh|ah|er|the|and|or|but|in|on|at|to|for|of|with|by)\b', ' ', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    text1_norm = normalize_text(text1)
    text2_norm = normalize_text(text2)
    
    if not text1_norm or not text2_norm:
        return 0.0
    
    # Use SequenceMatcher for similarity
    similarity = SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    # Bonus for word overlap (helps with different word order)
    words1 = set(text1_norm.split())
    words2 = set(text2_norm.split())
    if words1 and words2:
        word_overlap = len(words1 & words2) / len(words1 | words2)
        # Combine sequence similarity with word overlap
        similarity = (similarity * 0.7) + (word_overlap * 0.3)
    
    return min(similarity, 1.0)

def match_speakers_with_timing(speaker_segments: List[Dict], srt_segments: List[Dict]) -> List[Dict]:
    """
    Enhanced matching of speaker segments with SRT timing data.
    Uses improved text similarity and sophisticated partial matching strategies.
    """
    print(f"Matching {len(speaker_segments)} speaker segments with {len(srt_segments)} SRT segments")
    
    matched_segments = []
    used_srt_indices = set()
    
    for speaker_idx, speaker_seg in enumerate(speaker_segments):
        # Use 'content' field if available, otherwise 'text'
        speaker_content = speaker_seg.get('content', speaker_seg.get('text', '')).strip()
        if not speaker_content:
            matched_segments.append(speaker_seg)
            continue
        
        best_match = None
        best_similarity = 0.0
        best_srt_indices = []
        
        print(f"\nMatching speaker {speaker_idx + 1}: '{speaker_seg.get('speaker', 'Unknown')[:30]}...'")
        
        # Strategy 1: Try different window sizes to find the best match
        # Speaker segments are typically much longer than individual SRT segments
        for window_size in range(1, min(21, len(srt_segments) + 1)):  # Try windows up to 20 segments
            for start_idx in range(len(srt_segments) - window_size + 1):
                end_idx = start_idx + window_size
                
                # Skip if any segment in window is already used
                if any(idx in used_srt_indices for idx in range(start_idx, end_idx)):
                    continue
                
                # Combine content from window - fix field name
                combined_content = ' '.join(
                    srt_segments[idx]['content'] for idx in range(start_idx, end_idx)
                ).strip()
                
                if not combined_content:
                    continue
                
                # Calculate similarity
                similarity = calculate_text_similarity(speaker_content, combined_content)
                
                # Bonus for reasonable length match (prefer segments that aren't too short or too long)
                length_ratio = len(combined_content) / max(len(speaker_content), 1)
                if 0.3 <= length_ratio <= 2.0:  # Reasonable length ratio
                    similarity += 0.05
                
                # Bonus for consecutive segments (more likely to be a single speaker)
                if window_size > 1:
                    similarity += 0.02
                
                # Update best match if this is better
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        'start_time': srt_segments[start_idx]['start_time'],
                        'end_time': srt_segments[end_idx - 1]['end_time'],
                        'content': combined_content,
                        'window_size': window_size
                    }
                    best_srt_indices = list(range(start_idx, end_idx))
        
        # Strategy 2: If no good match found, try partial matching with relaxed criteria
        if best_similarity < 0.4:
            print(f"   No good direct match (best: {best_similarity:.3f}), trying partial matching...")
            
            # Look for smaller chunks within the speaker content
            speaker_words = speaker_content.split()
            chunk_size = min(50, len(speaker_words) // 3)  # Try smaller chunks
            
            for chunk_start in range(0, len(speaker_words), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(speaker_words))
                speaker_chunk = ' '.join(speaker_words[chunk_start:chunk_end])
                
                # Try to match this chunk against SRT segments
                for window_size in range(1, min(11, len(srt_segments) + 1)):
                    for start_idx in range(len(srt_segments) - window_size + 1):
                        end_idx = start_idx + window_size
                        
                        if any(idx in used_srt_indices for idx in range(start_idx, end_idx)):
                            continue
                        
                        combined_content = ' '.join(
                            srt_segments[idx]['content'] for idx in range(start_idx, end_idx)
                        ).strip()
                        
                        similarity = calculate_text_similarity(speaker_chunk, combined_content)
                        
                        if similarity > best_similarity and similarity > 0.3:
                            best_similarity = similarity
                            best_match = {
                                'start_time': srt_segments[start_idx]['start_time'],
                                'end_time': srt_segments[end_idx - 1]['end_time'],
                                'content': combined_content,
                                'window_size': window_size
                            }
                            best_srt_indices = list(range(start_idx, end_idx))
        
        # Strategy 3: For very low similarity, try to at least estimate timing based on position
        if best_similarity < 0.25 and speaker_idx > 0:
            print(f"   Very low similarity ({best_similarity:.3f}), estimating based on position...")
            
            # Find the last matched segment's end time
            prev_end_time = None
            for prev_seg in reversed(matched_segments):
                if prev_seg.get('end_time') is not None:
                    prev_end_time = prev_seg['end_time']
                    break
            
            if prev_end_time is not None:
                # Look for unused SRT segments after the previous segment
                candidate_segments = []
                for idx, srt_seg in enumerate(srt_segments):
                    if idx not in used_srt_indices and srt_seg['start_time'] >= prev_end_time:
                        candidate_segments.append((idx, srt_seg))
                
                if candidate_segments:
                    # Take a reasonable number of segments for this speaker
                    num_segments = min(5, len(candidate_segments))
                    selected_indices = [idx for idx, _ in candidate_segments[:num_segments]]
                    
                    best_match = {
                        'start_time': candidate_segments[0][1]['start_time'],
                        'end_time': candidate_segments[num_segments-1][1]['end_time'],
                        'content': 'Estimated timing based on position',
                        'window_size': num_segments
                    }
                    best_srt_indices = selected_indices
                    best_similarity = 0.3  # Assign a reasonable similarity for estimation
        
        # Apply the best match found
        if best_match and best_similarity > 0.25:  # Lower threshold for acceptance
            speaker_seg['start_time'] = best_match['start_time']
            speaker_seg['end_time'] = best_match['end_time']
            used_srt_indices.update(best_srt_indices)
            
            print(f"   ✓ Matched with similarity {best_similarity:.3f}, timing {best_match['start_time']:.1f}s-{best_match['end_time']:.1f}s (window: {best_match.get('window_size', 1)})")
        else:
            print(f"   ✗ No suitable timing match found (best similarity: {best_similarity:.3f})")
        
        matched_segments.append(speaker_seg)
    
    # Post-processing: Fill gaps between matched segments
    print(f"\n--- Post-processing: Filling timing gaps ---")
    for i in range(len(matched_segments)):
        current_seg = matched_segments[i]
        
        # If this segment has no timing but neighbors do, interpolate
        if current_seg.get('start_time') is None:
            prev_end = None
            next_start = None
            
            # Find previous segment with timing
            for j in range(i-1, -1, -1):
                if matched_segments[j].get('end_time') is not None:
                    prev_end = matched_segments[j]['end_time']
                    break
            
            # Find next segment with timing
            for j in range(i+1, len(matched_segments)):
                if matched_segments[j].get('start_time') is not None:
                    next_start = matched_segments[j]['start_time']
                    break
            
            # Interpolate if we have both bounds
            if prev_end is not None and next_start is not None and prev_end < next_start:
                gap_duration = next_start - prev_end
                estimated_start = prev_end + (gap_duration * 0.1)  # Small buffer
                estimated_end = next_start - (gap_duration * 0.1)
                
                current_seg['start_time'] = estimated_start
                current_seg['end_time'] = estimated_end
                print(f"   ✓ Interpolated timing for '{current_seg.get('speaker', 'Unknown')[:20]}...': {estimated_start:.1f}s-{estimated_end:.1f}s")
    
    # Count successful matches
    matched_count = sum(1 for seg in matched_segments if seg.get('start_time') is not None)
    print(f"\n=== SUMMARY ===")
    print(f"Successfully matched timing for {matched_count}/{len(speaker_segments)} speaker segments")
    print(f"Used {len(used_srt_indices)}/{len(srt_segments)} SRT segments")
    
    return matched_segments

def save_speakers_with_timing(segments: List[Dict], speakers_path: Path):
    """
    Save speaker segments with timing information to file
    Enhanced format includes timing data when available
    """
    try:
        with open(speakers_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                speaker = segment.get('speaker', 'Unknown Speaker')
                representing = segment.get('representing', '')
                content = segment.get('content', '')
                start_time = segment.get('start_time')
                end_time = segment.get('end_time')
                
                # Format speaker header
                if representing:
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
                
        print(f"Saved enhanced speaker transcript with timing to {speakers_path}")
        
    except Exception as e:
        print(f"Warning: Could not save enhanced speakers file: {e}")

def run_full_pipeline(url: str, title: str, target_dir: str) -> Dict:
    """
    Run the enhanced WebTV processing pipeline with timing integration
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
        
        # Step 3: Separate speakers with chunking
        print("Step 3: Separating speakers...")
        speakers_path, segments = separate_speakers(transcript_path, str(target_dir), title)
        
        # Step 4: Parse SRT file and match timing with speaker segments
        print("Step 4: Parsing SRT file and matching timing with speaker segments...")
        srt_segments = parse_srt_file(srt_path)
        if srt_segments:
            matched_segments = match_speakers_with_timing(segments, srt_segments)
            
            # Step 5: Save enhanced speaker transcript with timing
            print("Step 5: Saving enhanced speaker transcript with timing...")
            save_speakers_with_timing(matched_segments, speakers_path)
            
            # Update segments with timing information
            segments = matched_segments
        else:
            print("Warning: No SRT segments found, proceeding without timing")
        
        results['speakers'] = str(speakers_path.relative_to(target_dir.parent))
        results['segments'] = segments
        
        print("Pipeline completed successfully!")
        
    except Exception as e:
        error_msg = str(e)
        results['errors'].append(error_msg)
        print(f"Pipeline failed: {error_msg}")
        raise
    
    return results 