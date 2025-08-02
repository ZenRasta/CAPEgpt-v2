#!/usr/bin/env python3
"""
Check the status of PDF processing and database content
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv(Path(__file__).parent / 'backend' / '.env')

def check_processing_status():
    """Check what has been processed so far."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker
        
        print("🔍 Checking database content...")
        chunker = IntelligentChunker()
        
        # Get total count
        result = chunker.supabase.table('question_chunks').select('count', count='exact').execute()
        total_chunks = result.count
        print(f"📊 Total question chunks in database: {total_chunks}")
        
        # Get chunks by year to see what files have been processed
        print(f"\n📋 Chunks by year and paper:")
        year_groups = {}
        all_chunks = chunker.supabase.table('question_chunks').select('year, paper, subject').execute()
        
        for chunk in all_chunks.data:
            year = chunk.get('year', 'Unknown')
            paper = chunk.get('paper', 'Unknown')  
            subject = chunk.get('subject', 'Unknown')
            key = f"{year} - {paper} ({subject})"
            
            if key not in year_groups:
                year_groups[key] = 0
            year_groups[key] += 1
        
        for key, count in sorted(year_groups.items()):
            print(f"  {key}: {count} chunks")
        
        # Check for Pure Maths 2023 U1 P2 specifically
        pure_maths_2023 = chunker.supabase.table('question_chunks').select('*').eq('year', 2023).ilike('paper', '%U1%P2%').execute()
        
        if pure_maths_2023.data:
            print(f"\n✅ Found {len(pure_maths_2023.data)} chunks from Pure Maths 2023 U1 P2")
            
            # Show sample content
            sample_chunk = pure_maths_2023.data[0]
            content_preview = sample_chunk.get('content', '')[:150] + '...' if len(sample_chunk.get('content', '')) > 150 else sample_chunk.get('content', '')
            print(f"📄 Sample content: {content_preview}")
        else:
            print(f"\n❌ No chunks found specifically from Pure Maths 2023 U1 P2")
            
            # Check for 2023 chunks in general
            chunks_2023 = chunker.supabase.table('question_chunks').select('*').eq('year', 2023).execute()
            if chunks_2023.data:
                print(f"   However, found {len(chunks_2023.data)} chunks from 2023")
                for chunk in chunks_2023.data[:3]:
                    paper = chunk.get('paper', 'Unknown')
                    subject = chunk.get('subject', 'Unknown')
                    content = chunk.get('content', '')[:100] + '...' if len(chunk.get('content', '')) > 100 else chunk.get('content', '')
                    print(f"   - {subject} {paper}: {content}")
        
        # Check topic mappings
        mappings = chunker.supabase.table('question_topic_mappings').select('count', count='exact').execute()
        print(f"\n🔗 Total topic mappings: {mappings.count}")
        
        # Check syllabus chunks  
        syllabus = chunker.supabase.table('syllabus_chunks').select('count', count='exact').execute()
        print(f"📚 Total syllabus chunks: {syllabus.count}")
        
        print(f"\n✅ Database status check completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_processing_status()