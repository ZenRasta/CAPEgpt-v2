#!/usr/bin/env python3
"""
Create topic mappings for existing chunks in the database
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv(Path(__file__).parent / 'backend' / '.env')

def create_mappings_for_existing_chunks():
    """Create topic mappings for existing chunks that don't have them."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker
        
        print("🔧 Initializing chunker...")
        chunker = IntelligentChunker()
        
        # Get recent chunks that might need mappings (sample data and recent uploads)
        recent_chunks = chunker.supabase.table('question_chunks').select('*').order('id', desc=True).limit(10).execute()
        
        print(f"📋 Processing {len(recent_chunks.data)} recent chunks...")
        
        created_mappings = 0
        
        for chunk in recent_chunks.data:
            chunk_id = chunk['id']
            subject = chunk.get('subject')
            content = chunk.get('content', '')
            
            if not subject or not content:
                print(f"⏩ Skipping chunk {chunk_id} - missing subject or content")
                continue
            
            # Check if mappings already exist
            existing = chunker.supabase.table('question_topic_mappings').select('*').eq('question_id', chunk_id).execute()
            
            if existing.data:
                print(f"✅ Chunk {chunk_id} already has {len(existing.data)} mappings")
                continue
            
            print(f"🔗 Creating mappings for chunk {chunk_id} ({subject}):")
            print(f"   Content: {content[:80]}...")
            
            # Create topic mappings
            mappings = chunker.create_enhanced_topic_mappings(chunk_id, content, subject)
            
            if mappings:
                success = chunker.store_topic_mappings(mappings)
                if success:
                    print(f"   ✅ Created {len(mappings)} mappings")
                    created_mappings += len(mappings)
                    
                    # Show mapping details
                    for mapping in mappings:
                        confidence = mapping.get('confidence_score', 0)
                        mapping_type = mapping.get('mapping_type', 'unknown')
                        print(f"     - Confidence: {confidence:.2f}, Type: {mapping_type}")
                else:
                    print(f"   ❌ Failed to store mappings")
            else:
                print(f"   ⚠️  No mappings generated")
        
        print(f"\n🎉 Summary:")
        print(f"   Total mappings created: {created_mappings}")
        
        # Check final database state
        total_mappings = chunker.supabase.table('question_topic_mappings').select('count', count='exact').execute()
        print(f"   Total mappings in database: {total_mappings.count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_mappings_for_existing_chunks()