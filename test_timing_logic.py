#!/usr/bin/env python3
"""
Simple test file for timing matching logic
"""
from app.pipeline import parse_srt_file, match_speakers_with_timing, parse_speaker_response, save_speakers_with_timing
from pathlib import Path

def test_timing_matching():
    """Test the timing matching process step by step"""
    print("=== Testing Timing Matching Logic ===")
    
    try:
        # Step 1: Parse SRT file
        print("\n1. Parsing SRT file...")
        srt_path = Path('uploads/meeting_11/transcript.srt')
        if not srt_path.exists():
            print(f"ERROR: {srt_path} does not exist!")
            return
            
        srt_segments = parse_srt_file(srt_path)
        print(f"   ✓ Found {len(srt_segments)} SRT segments")
        
        if srt_segments:
            print(f"   ✓ First SRT segment: {srt_segments[0]['start_time']:.1f}s-{srt_segments[0]['end_time']:.1f}s")
            print(f"     Content: '{srt_segments[0]['content'][:60]}...'")
        
        # Step 2: Parse speaker file
        print("\n2. Parsing speaker file...")
        speaker_path = Path('uploads/meeting_11/transcript_speakers.txt')
        if not speaker_path.exists():
            print(f"ERROR: {speaker_path} does not exist!")
            return
            
        with open(speaker_path, 'r', encoding='utf-8') as f:
            speaker_text = f.read()
        
        speaker_segments = parse_speaker_response(speaker_text)
        print(f"   ✓ Found {len(speaker_segments)} speaker segments")
        
        if speaker_segments:
            first_speaker = speaker_segments[0]
            print(f"   ✓ First speaker: '{first_speaker.get('speaker', 'Unknown')}'")
            content = first_speaker.get('content', first_speaker.get('text', ''))
            print(f"     Content length: {len(content)} characters")
            print(f"     Content start: '{content[:100]}...'")
        
        # Step 3: Test matching with just first few segments
        print("\n3. Testing matching with first 3 speakers...")
        test_speakers = speaker_segments[:3]
        test_srt = srt_segments[:50]  # First 50 SRT segments for faster testing
        
        print(f"   Testing {len(test_speakers)} speakers against {len(test_srt)} SRT segments")
        
        enhanced_segments = match_speakers_with_timing(test_speakers, test_srt)
        
        # Step 4: Show results
        print("\n4. Results:")
        for i, seg in enumerate(enhanced_segments):
            speaker = seg.get('speaker', 'Unknown')
            start_time = seg.get('start_time')
            end_time = seg.get('end_time')
            
            if start_time is not None and end_time is not None:
                print(f"   ✓ Speaker {i+1} '{speaker}': {start_time:.1f}s - {end_time:.1f}s")
            else:
                print(f"   ✗ Speaker {i+1} '{speaker}': No timing found")
        
        # Step 5: Test full matching if the test worked
        if any(seg.get('start_time') is not None for seg in enhanced_segments):
            print("\n5. Running full matching...")
            full_enhanced = match_speakers_with_timing(speaker_segments, srt_segments)
            
            matched_count = sum(1 for seg in full_enhanced if seg.get('start_time') is not None)
            print(f"   ✓ Full matching: {matched_count}/{len(speaker_segments)} speakers matched")
            
            # Save results
            print("\n6. Saving enhanced file...")
            save_speakers_with_timing(full_enhanced, Path('uploads/meeting_11/transcript_speakers_enhanced.txt'))
            print("   ✓ Saved to transcript_speakers_enhanced.txt")
        else:
            print("\n5. Skipping full matching - test failed")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timing_matching() 