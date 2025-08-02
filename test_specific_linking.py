#!/usr/bin/env python3
"""
Test specific linking with chemistry example that should match better
"""

import os
import sys
from pathlib import Path
import logging

# Add the project root to path
sys.path.append(str(Path(__file__).parent))

# Set environment variables from backend/.env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / 'backend' / '.env')

# Configure logging to see debug info
logging.basicConfig(level=logging.DEBUG)

def test_specific_linking():
    """Test linking with chemistry example that should have good keyword matches."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker, DocumentChunk, ChunkType
        
        print("🔧 Initializing chunker...")
        chunker = IntelligentChunker()
        
        # Test with chemistry question that should match our sample syllabus
        test_chunk = DocumentChunk(
            content="Balance the chemical equation: C₂H₆ + O₂ → CO₂ + H₂O. Explain the types of chemical reactions involved.",
            chunk_type=ChunkType.QUESTION,
            subject="Chemistry",
            year=2024,
            paper="Paper 1",
            question_id="3b",
            topic="Chemical Reactions",
            sub_topic="Balancing Equations",
            confidence_score=0.95
        )
        
        print(f"\n📝 Testing with chemistry question:")
        print(f"Content: {test_chunk.content}")
        
        # First, let's see what syllabus chunks exist for Chemistry
        chemistry_syllabus = chunker.get_syllabus_chunks("Chemistry")
        print(f"\n📚 Found {len(chemistry_syllabus)} Chemistry syllabus chunks:")
        for syllabus in chemistry_syllabus:
            print(f"  - {syllabus['topic_title']}: {syllabus['chunk_text'][:100]}...")
        
        # Test topic mapping directly
        print(f"\n🔗 Testing topic mapping...")
        mappings = chunker.create_enhanced_topic_mappings(999, test_chunk.content, test_chunk.subject)
        
        if mappings:
            print(f"✅ Created {len(mappings)} topic mappings:")
            for i, mapping in enumerate(mappings, 1):
                confidence = mapping.get('confidence_score', 0)
                mapping_type = mapping.get('mapping_type', 'unknown')
                topic_id = mapping.get('topic_id')
                
                # Get topic details
                topic_details = [s for s in chemistry_syllabus if s['id'] == topic_id]
                topic_name = topic_details[0]['topic_title'] if topic_details else 'Unknown'
                
                print(f"  {i}. Topic: {topic_name}")
                print(f"     Confidence: {confidence:.2f}")
                print(f"     Type: {mapping_type}")
                
                if mapping.get('common_keywords'):
                    print(f"     Keywords: {mapping['common_keywords']}")
        else:
            print("❌ No topic mappings created")
            
            # Debug: let's see what keywords are extracted
            question_keywords = chunker.extract_keywords(test_chunk.content)
            print(f"\n🔍 Debug - Question keywords: {question_keywords}")
            
            for syllabus in chemistry_syllabus:
                syllabus_text = f"{syllabus['topic_title']} {syllabus['chunk_text']}"
                syllabus_keywords = chunker.extract_keywords(syllabus_text)
                common = set(question_keywords).intersection(set(syllabus_keywords))
                print(f"  Syllabus '{syllabus['topic_title']}' keywords: {syllabus_keywords}")
                print(f"  Common keywords: {list(common)}")
        
        print("\n🎉 Specific linking test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_specific_linking()