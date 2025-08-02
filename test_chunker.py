#!/usr/bin/env python3
"""
Simple test script to demonstrate PDF chunking without database upload
"""

import os
import sys
from pathlib import Path

# Add the project root to path
sys.path.append(str(Path(__file__).parent))

# Set environment variables
os.environ['SUPABASE_URL'] = 'https://ocdjqofrcrobgrjyjqox.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9jZGpxb2ZyY3JvYmdyanlqcW94Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjQzOTU3OSwiZXhwIjoyMDY4MDE1NTc5fQ.CsP6jzBuJtPUFkHdWPyle2dgFOaY6096zTddYfORnPM'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/anthonyzamore/Projects/CAPE-GPT2/backend/gen-lang-client-0319019466-5d5a620ae060.json'

def test_chunking():
    """Test the chunking functionality on the PDF files."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker
        
        print("🔧 Initializing chunker...")
        chunker = IntelligentChunker()
        print("✅ Chunker initialized successfully!")
        
        # Test files
        pdf_files = [
            "/Users/anthonyzamore/Downloads/CAPE Pure Mathematics (1).pdf",
            "/Users/anthonyzamore/Downloads/Pure Maths 2023 U1 P2.pdf"
        ]
        
        for pdf_file in pdf_files:
            if not Path(pdf_file).exists():
                print(f"❌ File not found: {pdf_file}")
                continue
                
            print(f"\n📄 Processing: {Path(pdf_file).name}")
            
            # Process PDF and create chunks (without uploading)
            chunks = chunker.process_pdf(pdf_file)
            
            if chunks:
                print(f"✅ Created {len(chunks)} chunks")
                
                # Show some sample chunks
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    print(f"\n--- Chunk {i+1} ---")
                    print(f"Subject: {chunk.subject}")
                    print(f"Year: {chunk.year}")
                    print(f"Paper: {chunk.paper}")
                    print(f"Question ID: {chunk.question_id}")
                    print(f"Math Heavy: {chunk.is_math_heavy}")
                    print(f"Content preview: {chunk.content[:200]}...")
                    if chunk.equations:
                        print(f"Equations found: {len(chunk.equations)}")
                    if chunk.images:
                        print(f"Images processed: {len(chunk.images)}")
                
                # Ask user if they want to upload to database
                response = input(f"\n🤔 Upload these {len(chunks)} chunks to Supabase? (y/N): ")
                if response.lower() == 'y':
                    print("📤 Uploading to database...")
                    success = chunker.upload_chunks_to_supabase(chunks)
                    if success:
                        print("✅ Successfully uploaded to database!")
                    else:
                        print("❌ Failed to upload to database")
                else:
                    print("⏩ Skipping database upload")
            else:
                print("❌ No chunks created")
        
        print("\n🎉 Chunking test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_chunking()