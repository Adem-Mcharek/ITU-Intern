"""
Meeting Summarizer for ITU-focused Content
Generates concise, relevant summaries from transcript_speakers files
focusing on ICT, digital transformation, AI, and ITU priority areas.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from flask import current_app

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available. Meeting summaries will be disabled.")

# ITU-focused summary prompt
ITU_SUMMARY_PROMPT = """
You are an ITU staff member writing a brief internal summary for colleagues. Analyze this meeting transcript and write a concise summary focusing ONLY on what matters to ITU's work.

WRITE FROM ITU EMPLOYEE PERSPECTIVE:
- What should ITU colleagues know about this meeting?
- How does this impact our standardization, development, or radiocommunication work?
- Are there opportunities for ITU engagement or follow-up?

ITU FOCUS AREAS (prioritize what's most relevant):
• Standards & Technical work (ITU-T, ITU-R)
• Digital inclusion & development (ITU-D)
• Emerging tech (AI, 5G/6G, IoT)
• Cybersecurity & trust
• Spectrum management
• Digital transformation initiatives
• ICT capacity building

WRITING STYLE:
- Internal memo tone, like briefing a colleague
- Maximum 150 words total
- Bullet points for key items
- Mention specific countries/organizations when relevant
- Focus on actionable insights and opportunities

FORMAT:
**Key ITU-Relevant Points:**
• [Most important point for ITU]
• [Second priority point]

**Potential ITU Actions/Opportunities:**
• [What ITU could/should do based on this meeting]

IMPORTANT:
- Skip general discussions - focus on concrete ITU-relevant content
- If minimal ICT content: write "Limited relevance to ITU mandate - primarily [topic]"
- Be specific about which ITU sector (ITU-T/ITU-R/ITU-D) would be most interested

MEETING TRANSCRIPT:
"""

def setup_gemini_api() -> Optional[Any]:
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
        return genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")
    return None

def extract_transcript_content(speakers_file_path: Path) -> str:
    """Extract clean text content from transcript_speakers.txt file"""
    try:
        with open(speakers_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean up the content - remove headers and formatting, keep speaker attribution
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and main header
            if not line or line.startswith('#'):
                continue
            # Keep speaker headers and content
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    except Exception as e:
        print(f"Error reading transcript file {speakers_file_path}: {e}")
        return ""

def generate_itu_summary(transcript_content: str) -> Optional[str]:
    """Generate ITU-focused summary using Gemini API"""
    if not transcript_content.strip():
        return None
    
    model = setup_gemini_api()
    if not model:
        print("Warning: Gemini API not available. Cannot generate summary.")
        return None
    
    try:
        # Prepare the full prompt
        full_prompt = ITU_SUMMARY_PROMPT + "\n\n" + transcript_content + "\n\nProvide your ITU-focused summary:"
        
        # Generate summary with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating ITU summary (attempt {attempt + 1}/{max_retries})...")
                response = model.generate_content(full_prompt)
                
                # Clean up response
                summary = response.text.strip()
                
                # Validate response quality
                if len(summary) < 30:
                    print(f"Summary too short ({len(summary)} chars), retrying...")
                    continue
                
                if "Limited relevance to ITU mandate" in summary:
                    print("Meeting has limited ITU-relevant content")
                    return summary
                
                print(f"Successfully generated ITU summary ({len(summary)} characters)")
                return summary
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
                
                # Wait before retry
                import time
                time.sleep(2 ** attempt)
        
        return None
        
    except Exception as e:
        print(f"Error generating ITU summary: {e}")
        return None

def create_meeting_summary(meeting_id: int, speakers_file_path: Path) -> Optional[str]:
    """
    Main function to create ITU-focused meeting summary
    
    Args:
        meeting_id: Database ID of the meeting
        speakers_file_path: Path to the transcript_speakers.txt file
        
    Returns:
        Generated summary text or None if failed
    """
    print(f"\n=== Generating ITU Summary for Meeting {meeting_id} ===")
    
    # Check if file exists
    if not speakers_file_path.exists():
        print(f"Error: Transcript speakers file not found: {speakers_file_path}")
        return None
    
    # Extract transcript content
    print("Step 1: Extracting transcript content...")
    transcript_content = extract_transcript_content(speakers_file_path)
    
    if not transcript_content:
        print("Error: No content extracted from transcript file")
        return None
    
    print(f"Extracted {len(transcript_content)} characters of transcript content")
    
    # Generate ITU-focused summary
    print("Step 2: Generating ITU-focused summary with Gemini...")
    summary = generate_itu_summary(transcript_content)
    
    if summary:
        print(f"✅ Successfully generated ITU summary ({len(summary)} characters)")
        return summary
    else:
        print("❌ Failed to generate ITU summary")
        return None

def save_summary_to_database(meeting_id: int, summary: str) -> bool:
    """
    Save the generated summary to the database
    
    Args:
        meeting_id: Database ID of the meeting
        summary: Generated summary text
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        from app import db
        from app.models import Meeting
        
        # Get meeting record
        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            print(f"Error: Meeting {meeting_id} not found in database")
            return False
        
        # Update summary field
        meeting.itu_summary = summary
        db.session.commit()
        
        print(f"✅ Saved ITU summary to database for meeting {meeting_id}")
        return True
        
    except Exception as e:
        print(f"Error saving summary to database: {e}")
        return False

def process_meeting_summary(meeting_id: int, meeting_dir: Path) -> bool:
    """
    Complete workflow to process meeting summary
    
    Args:
        meeting_id: Database ID of the meeting
        meeting_dir: Directory containing meeting files
        
    Returns:
        True if processed successfully, False otherwise
    """
    try:
        # Locate speakers file
        speakers_file = meeting_dir / 'transcript_speakers.txt'
        
        # Generate summary
        summary = create_meeting_summary(meeting_id, speakers_file)
        
        if summary:
            # Save to database
            return save_summary_to_database(meeting_id, summary)
        
        return False
        
    except Exception as e:
        print(f"Error in meeting summary workflow: {e}")
        return False 