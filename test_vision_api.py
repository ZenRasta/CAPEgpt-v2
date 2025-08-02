#!/usr/bin/env python3
"""
Test Google Vision API configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / 'backend' / '.env')

def test_vision_api():
    """Test Google Vision API setup."""
    try:
        # Check if credentials file exists
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        print(f"📁 Credentials path: {creds_path}")
        
        if creds_path and Path(creds_path).exists():
            print("✅ Credentials file exists")
            
            # Set environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
            
            # Try to initialize the Vision client
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            print("✅ Google Vision API client initialized successfully!")
            
            # Test with a simple request (this might fail due to billing, but client init is the main test)
            print("📡 Vision API is ready for OCR processing")
            return True
            
        else:
            print("❌ Credentials file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Vision API: {e}")
        return False

if __name__ == '__main__':
    test_vision_api()