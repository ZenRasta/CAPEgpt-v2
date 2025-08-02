#!/usr/bin/env python3
"""
Complete test of the enhanced linking system with simulated chunk upload
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

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_complete_linking_workflow():
    """Test the complete enhanced linking workflow with document chunk."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker, DocumentChunk, ChunkType
        
        print("🔧 Initializing chunker with enhanced linking...")
        chunker = IntelligentChunker()
        
        if chunker.llm_client:
            print("✅ LLM client available for enhanced linking")
        else:
            print("⚠️  LLM client not available - will use basic keyword matching")
        
        # Create a test question chunk
        test_chunk = DocumentChunk(
            content="Find the derivative of f(x) = 3x³ - 2x² + 5x - 1 using differentiation rules",
            chunk_type=ChunkType.QUESTION,
            subject="Pure Mathematics",
            year=2024,
            paper="Paper 2",
            question_id="2a",
            topic="Calculus",
            sub_topic="Differentiation",
            confidence_score=0.95
        )
        
        print(f"\n📝 Testing complete workflow with sample question:")
        print(f"Subject: {test_chunk.subject}")
        print(f"Content: {test_chunk.content}")
        print(f"Question ID: {test_chunk.question_id}")
        
        # Test the complete upload workflow (which includes automatic mapping)
        print("\n🚀 Testing complete upload workflow with topic mapping...")
        
        success = chunker.upload_chunks_to_supabase([test_chunk])
        
        if success:
            print("✅ Successfully uploaded chunk with automatic topic mapping!")
            
            # Verify the mapping was created by checking the database
            try:
                # Get the most recent question to find its ID
                recent_questions = chunker.supabase.table('question_chunks').select('id, content').order('id', desc=True).limit(1).execute()
                
                if recent_questions.data:
                    question_id = recent_questions.data[0]['id']
                    print(f"📍 Created question chunk with ID: {question_id}")
                    
                    # Check if topic mappings were created
                    mappings = chunker.supabase.table('question_topic_mappings').select('*').eq('question_id', question_id).execute()
                    
                    if mappings.data:
                        print(f"✅ Created {len(mappings.data)} topic mappings:")
                        for i, mapping in enumerate(mappings.data, 1):
                            confidence = mapping['confidence_score']
                            mapping_type = mapping['mapping_type']
                            topic_id = mapping['topic_id']
                            
                            # Get topic details
                            topic_details = chunker.supabase.table('syllabus_chunks').select('topic_title, chunk_text').eq('id', topic_id).execute()
                            topic_name = topic_details.data[0]['topic_title'] if topic_details.data else 'Unknown'
                            
                            print(f"  {i}. Topic: {topic_name}")
                            print(f"     Confidence: {confidence:.2f}")
                            print(f"     Type: {mapping_type}")
                    else:
                        print("⚠️  No topic mappings found for the uploaded chunk")
                else:
                    print("❌ Could not find the uploaded chunk")
                    
            except Exception as e:
                print(f"❌ Error verifying upload: {e}")
        else:
            print("❌ Failed to upload chunk")
        
        print("\n🎉 Complete linking workflow test finished!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_complete_linking_workflow()