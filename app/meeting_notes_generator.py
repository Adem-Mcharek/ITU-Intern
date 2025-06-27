"""
Meeting Notes Generator for ITU/UN Meetings
Generates professional .docx meeting notes with consistent formatting
based on transcript_speakers.txt files.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from flask import current_app

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available. Meeting notes generation will be disabled.")

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.shared import OxmlElement, qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. Meeting notes generation will be disabled.")

# Concise meeting notes prompt for ITU style (similar to attached examples)
MEETING_NOTES_PROMPT = """
You are an ITU intern creating concise, professional meeting notes similar to UN/ITU diplomatic style.

Create structured meeting notes that are:
- CONCISE and focused (2-3 pages max when printed)
- FORMAL diplomatic language 
- CLEAR section structure
- FACTUAL and objective

Use this EXACT structure:

**MEETING OVERVIEW**
Brief purpose, key participants, main themes (2-3 sentences only)

**KEY DISCUSSIONS**
Main topics with speaker attribution. Format: "[Speaker Name, Organization] emphasized that..."
Focus on: decisions, commitments, technical points, policy matters

**POSITIONS & RECOMMENDATIONS**  
Member state positions and organizational viewpoints
Areas of consensus/disagreement (be concise)

**DECISIONS & ACTION ITEMS**
• Specific decisions made
• Action items with responsible parties  
• Timelines and next steps

**TECHNICAL MATTERS** (only if significant technical content)
Standards, specifications, implementation issues

**CAPACITY BUILDING** (only if discussed)
Training needs, technical assistance, support for developing countries

STYLE REQUIREMENTS:
- Use formal UN/ITU language but keep concise
- Third person: "[Representative] stated..." not "I stated..."
- Speaker attribution: "[Name, Organization] noted that..."
- Each section should be 2-4 paragraphs maximum
- Use bullet points for lists and action items
- Focus on substance, not process details
- Highlight key decisions and commitments

EXAMPLE FORMAT:
**MEETING OVERVIEW**
The session addressed digital transformation in least developed countries, with representatives from ITU, UN DESA, World Bank, and several member states participating.

**KEY DISCUSSIONS**
[Technical Expert, ITU] outlined the challenges of 5G deployment in developing regions, emphasizing spectrum allocation issues. [Policy Advisor, UN DESA] highlighted the persistent digital divide and the need for coordinated international support.

Generate concise meeting notes from this transcript:

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

def extract_meeting_metadata(speakers_file_path: Path, meeting_title: str) -> Dict[str, Any]:
    """Extract metadata from meeting content for document header"""
    try:
        with open(speakers_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract basic information
        speakers = []
        organizations = set()
        
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('[') and line.strip().endswith(']'):
                # Parse speaker info
                speaker_info = line.strip()[1:-1]  # Remove brackets
                if ',' in speaker_info:
                    parts = speaker_info.split(',', 1)
                    speaker_name = parts[0].strip()
                    org = parts[1].strip()
                    speakers.append(speaker_name)
                    organizations.add(org)
                else:
                    speakers.append(speaker_info.strip())
        
        return {
            'title': meeting_title,
            'date': datetime.now().strftime('%B %d, %Y'),
            'total_speakers': len(set(speakers)),
            'organizations': list(organizations),
            'content_length': len(content)
        }
    
    except Exception as e:
        print(f"Error extracting meeting metadata: {e}")
        return {
            'title': meeting_title,
            'date': datetime.now().strftime('%B %d, %Y'),
            'total_speakers': 0,
            'organizations': [],
            'content_length': 0
        }

def generate_meeting_notes_content(transcript_content: str) -> Optional[str]:
    """Generate professional meeting notes using Gemini API"""
    if not transcript_content.strip():
        return None
    
    model = setup_gemini_api()
    if not model:
        print("Warning: Gemini API not available. Cannot generate meeting notes.")
        return None
    
    try:
        # Prepare the full prompt
        full_prompt = MEETING_NOTES_PROMPT + "\n\n" + transcript_content + "\n\nGenerate comprehensive meeting notes:"
        
        # Generate notes with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating meeting notes (attempt {attempt + 1}/{max_retries})...")
                response = model.generate_content(full_prompt)
                
                # Clean up response
                notes_content = response.text.strip()
                
                # Validate response quality  
                if len(notes_content) < 100:
                    print(f"Notes too short ({len(notes_content)} chars), retrying...")
                    continue
                
                print(f"Successfully generated meeting notes ({len(notes_content)} characters)")
                return notes_content
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
                
                # Wait before retry
                import time
                time.sleep(2 ** attempt)
        
        return None
        
    except Exception as e:
        print(f"Error generating meeting notes: {e}")
        return None

def create_formatted_document(notes_content: str, metadata: Dict[str, Any]) -> Optional[Document]:
    """Create a professionally formatted Word document with the meeting notes"""
    if not DOCX_AVAILABLE:
        print("Warning: python-docx not available. Cannot create formatted document.")
        return None
    
    try:
        # Create new document
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add ITU header
        header = doc.sections[0].header
        header_para = header.paragraphs[0]
        header_para.text = "International Telecommunication Union"
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Document title
        title = doc.add_heading('MEETING NOTES', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Meeting title
        meeting_title = doc.add_heading(metadata['title'], 1)
        meeting_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add document info
        info_para = doc.add_paragraph()
        info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_run = info_para.add_run(f"Date: {metadata['date']}")
        info_run.italic = True
        
        # Add separator line
        doc.add_paragraph("_" * 80).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add meeting overview if organizations present
        if metadata.get('organizations'):
            overview_para = doc.add_paragraph()
            overview_para.add_run("Participating Organizations: ").bold = True
            overview_para.add_run(", ".join(metadata['organizations'][:8]))  # Limit to first 8
            if len(metadata['organizations']) > 8:
                overview_para.add_run(" and others")
        
        # Add blank line
        doc.add_paragraph()
        
        # Process and add the generated content
        _add_formatted_content(doc, notes_content)
        
        # Add footer with generation info
        footer = doc.sections[0].footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M UTC')} | ITU INTERN (AI generated)"
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        return doc
        
    except Exception as e:
        print(f"Error creating formatted document: {e}")
        return None

def _add_formatted_content(doc: Document, content: str):
    """Add formatted content to the document with proper styling"""
    lines = content.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a section header (starts with ** and ends with **)
        if line.startswith('**') and line.endswith('**'):
            section_title = line[2:-2].strip()
            heading = doc.add_heading(section_title, 2)
            heading.space_before = Pt(12)
            heading.space_after = Pt(6)
            current_section = section_title
            
        # Check if line is a subsection (starts with single bullet or dash)
        elif line.startswith('•') or line.startswith('-') or line.startswith('◦'):
            para = doc.add_paragraph(line[1:].strip(), style='List Bullet')
            para.space_after = Pt(3)
            
        # Check if line appears to be a speaker/participant identifier
        elif line.startswith('[') and ']' in line:
            para = doc.add_paragraph()
            speaker_run = para.add_run(line)
            speaker_run.bold = True
            speaker_run.font.color.rgb = RGBColor(0, 32, 96)  # ITU blue
            para.space_before = Pt(6)
            para.space_after = Pt(3)
            
        # Regular paragraph
        else:
            para = doc.add_paragraph(line)
            para.space_after = Pt(6)
            
            # Apply special formatting for certain keywords
            for run in para.runs:
                text = run.text.lower()
                if any(keyword in text for keyword in ['recommendation', 'decision', 'resolution', 'action item']):
                    run.bold = True

def save_meeting_notes_document(doc: Document, meeting_dir: Path, meeting_title: str) -> Optional[Path]:
    """Save the meeting notes document to the meeting directory"""
    try:
        # Create safe filename
        safe_title = "".join(c for c in meeting_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        
        filename = f"Meeting_Notes_{safe_title}_{datetime.now().strftime('%Y%m%d')}.docx"
        notes_path = meeting_dir / filename
        
        # Save document
        doc.save(str(notes_path))
        print(f"Meeting notes saved to: {notes_path}")
        
        return notes_path
        
    except Exception as e:
        print(f"Error saving meeting notes document: {e}")
        return None

def create_meeting_notes(meeting_id: int, speakers_file_path: Path, meeting_title: str) -> Optional[Path]:
    """
    Main function to create professional meeting notes
    
    Args:
        meeting_id: Database ID of the meeting
        speakers_file_path: Path to the transcript_speakers.txt file
        meeting_title: Title of the meeting
        
    Returns:
        Path to generated .docx file or None if failed
    """
    print(f"\n=== Generating Meeting Notes for Meeting {meeting_id} ===")
    
    # Check dependencies
    if not GEMINI_AVAILABLE or not DOCX_AVAILABLE:
        print("Error: Required dependencies not available (google-generativeai and/or python-docx)")
        return None
    
    # Check if file exists
    if not speakers_file_path.exists():
        print(f"Error: Transcript speakers file not found: {speakers_file_path}")
        return None
    
    # Extract metadata
    print("Step 1: Extracting meeting metadata...")
    metadata = extract_meeting_metadata(speakers_file_path, meeting_title)
    
    # Extract transcript content (reuse from summarizer)
    print("Step 2: Extracting transcript content...")
    from app.meeting_summarizer import extract_transcript_content
    transcript_content = extract_transcript_content(speakers_file_path)
    
    if not transcript_content:
        print("Error: No content extracted from transcript file")
        return None
    
    print(f"Extracted {len(transcript_content)} characters of transcript content")
    
    # Generate meeting notes content
    print("Step 3: Generating professional meeting notes with Gemini...")
    notes_content = generate_meeting_notes_content(transcript_content)
    
    if not notes_content:
        print("Error: Failed to generate meeting notes content")
        return None
    
    # Create formatted document
    print("Step 4: Creating professionally formatted Word document...")
    doc = create_formatted_document(notes_content, metadata)
    
    if not doc:
        print("Error: Failed to create formatted document")
        return None
    
    # Save document
    print("Step 5: Saving meeting notes document...")
    meeting_dir = speakers_file_path.parent
    notes_path = save_meeting_notes_document(doc, meeting_dir, meeting_title)
    
    if notes_path:
        print(f"✅ Successfully generated meeting notes: {notes_path}")
        return notes_path
    else:
        print("❌ Failed to save meeting notes document")
        return None

def save_notes_path_to_database(meeting_id: int, notes_path: Path) -> bool:
    """
    Save the meeting notes file path to the database
    
    Args:
        meeting_id: Database ID of the meeting
        notes_path: Path to the generated notes file
        
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
        
        # Update notes path field (we need to add this to the model)
        # For now, we'll store it relative to the uploads directory
        relative_path = notes_path.relative_to(notes_path.parent.parent)
        meeting.notes_path = str(relative_path)
        db.session.commit()
        
        print(f"✅ Saved meeting notes path to database for meeting {meeting_id}")
        return True
        
    except Exception as e:
        print(f"Error saving notes path to database: {e}")
        return False

def process_meeting_notes(meeting_id: int, meeting_dir: Path, meeting_title: str) -> bool:
    """
    Complete workflow to process meeting notes
    
    Args:
        meeting_id: Database ID of the meeting
        meeting_dir: Directory containing meeting files
        meeting_title: Title of the meeting
        
    Returns:
        True if processed successfully, False otherwise
    """
    try:
        # Locate speakers file
        speakers_file = meeting_dir / 'transcript_speakers.txt'
        
        # Generate notes
        notes_path = create_meeting_notes(meeting_id, speakers_file, meeting_title)
        
        if notes_path:
            # Save path to database
            return save_notes_path_to_database(meeting_id, notes_path)
        
        return False
        
    except Exception as e:
        print(f"Error in meeting notes workflow: {e}")
        return False