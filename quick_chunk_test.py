#!/usr/bin/env python3
"""
Quick test to process just a few chunks from the Pure Maths 2023 U1 P2.pdf
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv(Path(__file__).parent / 'backend' / '.env')

def quick_chunk_test():
    """Process the PDF and upload a few chunks to test the workflow."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker, DocumentChunk, ChunkType
        
        print("🔧 Initializing chunker...")
        chunker = IntelligentChunker()
        
        # Process the PDF to get chunks (without uploading first)
        pdf_path = "/Users/anthonyzamore/Downloads/Pure Maths 2023 U1 P2.pdf"
        print(f"📄 Processing: {Path(pdf_path).name}")
        
        chunks = chunker.process_pdf(pdf_path)
        
        if chunks:
            print(f"✅ Created {len(chunks)} chunks from PDF")
            
            # Test with just the first 3 chunks to ensure upload works
            test_chunks = chunks[:3]
            print(f"🧪 Testing upload with first {len(test_chunks)} chunks...")
            
            for i, chunk in enumerate(test_chunks, 1):
                print(f"\n--- Chunk {i} ---")
                print(f"Subject: {chunk.subject}")
                print(f"Year: {chunk.year}")
                print(f"Paper: {chunk.paper}")
                print(f"Question ID: {chunk.question_id}")
                print(f"Content preview: {chunk.content[:150]}...")
            
            # Upload test chunks
            success = chunker.upload_chunks_to_supabase(test_chunks)
            
            if success:
                print(f"\n✅ Successfully uploaded {len(test_chunks)} test chunks!")
                
                # Verify they were uploaded with correct metadata
                recent = chunker.supabase.table('question_chunks').select('*').eq('year', 2023).eq('paper', 'U1 P2').execute()
                
                if recent.data:
                    print(f"🎉 Found {len(recent.data)} chunks with correct metadata (Year: 2023, Paper: U1 P2)")
                else:
                    print("⚠️  Chunks uploaded but metadata not found - checking recent uploads...")
                    recent_any = chunker.supabase.table('question_chunks').select('*').order('id', desc=True).limit(3).execute()
                    for chunk in recent_any.data:
                        print(f"  - Year: {chunk.get('year')}, Paper: {chunk.get('paper')}, Subject: {chunk.get('subject')}")
            else:
                print("❌ Failed to upload test chunks")
        else:
            print("❌ No chunks created from PDF")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    quick_chunk_test()