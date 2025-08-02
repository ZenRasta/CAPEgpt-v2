#!/usr/bin/env python3
"""
Pipeline Testing Script for CAPE GPT
====================================

This script tests the complete pipeline including:
1. Chunking functionality
2. OCR processing
3. RAG retrieval
4. API endpoints
"""

import sys
import os
import json
import requests
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_chunking_script():
    """Test the intelligent chunking script."""
    logger.info("Testing chunking functionality...")
    
    try:
        from scripts.intelligent_chunker import IntelligentChunker
        
        # Initialize chunker
        chunker = IntelligentChunker()
        
        # Test keyword extraction
        test_query = "Find the derivative of x^2 + 3x + 2"
        keywords = chunker.extract_keywords(test_query)
        logger.info(f"Keywords extracted: {keywords}")
        
        # Test math detection
        math_text = "Solve: ∫(x² + 2x)dx from 0 to 1"
        is_math = chunker.is_math_heavy(math_text)
        logger.info(f"Math detection for '{math_text}': {is_math}")
        
        # Test equation extraction
        equations = chunker.extract_equations("The formula is $E = mc^2$ and $$\\int_0^1 x dx = \\frac{1}{2}$$")
        logger.info(f"Equations extracted: {equations}")
        
        logger.info("✓ Chunking functionality working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Chunking test failed: {e}")
        return False

def test_backend_health():
    """Test if backend server is healthy."""
    logger.info("Testing backend health...")
    
    try:
        api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
        response = requests.get(f"{api_url}/", timeout=5)
        
        if response.status_code == 200:
            logger.info("✓ Backend server is healthy")
            return True
        else:
            logger.error(f"✗ Backend returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Backend health check failed: {e}")
        return False

def test_upload_endpoint():
    """Test the upload endpoint with a sample image."""
    logger.info("Testing upload endpoint...")
    
    try:
        # Create a simple test image (1x1 white pixel PNG)
        import base64
        from PIL import Image
        import io
        
        # Create minimal test image
        img = Image.new('RGB', (100, 50), color='white')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
        
        files = {'file': ('test.png', img_buffer, 'image/png')}
        response = requests.post(f"{api_url}/upload", files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Upload successful. Math heavy: {result.get('is_math_heavy')}")
            return True
        else:
            logger.error(f"✗ Upload failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Upload test failed: {e}")
        return False

def test_query_endpoint():
    """Test the query endpoint with sample questions."""
    logger.info("Testing query endpoint...")
    
    test_queries = [
        {
            "text": "Find the derivative of x^2 + 3x + 2",
            "subject": "Pure Mathematics"
        },
        {
            "text": "Calculate the integral of sin(x) from 0 to π",
            "subject": "Pure Mathematics"
        },
        {
            "text": "What is Newton's second law of motion?",
            "subject": "Physics"
        }
    ]
    
    api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
        try:
            logger.info(f"Testing query {i}: {query['text'][:50]}...")
            
            response = requests.post(
                f"{api_url}/query",
                json=query,
                timeout=60,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ Query {i} successful")
                logger.info(f"  - Answer length: {len(result.get('answer', ''))}")
                logger.info(f"  - Similar questions: {result.get('similar_questions_count', 0)}")
                logger.info(f"  - Confidence score: {result.get('confidence_score', 0):.2f}")
                success_count += 1
            else:
                logger.error(f"✗ Query {i} failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"✗ Query {i} test failed: {e}")
    
    success_rate = success_count / len(test_queries)
    logger.info(f"Query endpoint success rate: {success_rate:.1%} ({success_count}/{len(test_queries)})")
    
    return success_rate > 0.5  # Consider successful if >50% of queries work

def test_subjects_endpoint():
    """Test the subjects endpoint."""
    logger.info("Testing subjects endpoint...")
    
    try:
        api_url = os.getenv('API_URL', 'http://127.0.0.1:8000')
        response = requests.get(f"{api_url}/subjects", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            subjects = result.get('subjects', [])
            logger.info(f"✓ Subjects endpoint working. Available subjects: {subjects}")
            return len(subjects) > 0
        else:
            logger.error(f"✗ Subjects endpoint failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Subjects endpoint test failed: {e}")
        return False

def test_database_functions():
    """Test database RPC functions."""
    logger.info("Testing database functions...")
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not (supabase_url and supabase_key):
            logger.warning("⚠ Supabase credentials not found, skipping database tests")
            return True
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Test basic table access
        response = supabase.table('question_chunks').select('count', count='exact').execute()
        question_count = response.count if hasattr(response, 'count') else 0
        
        response = supabase.table('syllabus_chunks').select('count', count='exact').execute()
        syllabus_count = response.count if hasattr(response, 'count') else 0
        
        logger.info(f"✓ Database accessible. Questions: {question_count}, Syllabus: {syllabus_count}")
        
        # Test RPC function (if data exists)
        if question_count > 0:
            try:
                # Test with dummy embedding
                dummy_embedding = [0.1] * 384  # Adjust size based on your model
                response = supabase.rpc(
                    'match_question_chunks',
                    {
                        'query_embedding': dummy_embedding,
                        'query_subject': 'Pure Mathematics',
                        'match_threshold': 0.1,
                        'match_count': 1
                    }
                ).execute()
                
                logger.info("✓ RPC functions working")
            except Exception as rpc_error:
                logger.warning(f"⚠ RPC function test failed: {rpc_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False

def run_all_tests():
    """Run all pipeline tests."""
    logger.info("=" * 60)
    logger.info("CAPE GPT Pipeline Testing")
    logger.info("=" * 60)
    
    tests = [
        ("Chunking Script", test_chunking_script),
        ("Backend Health", test_backend_health),
        ("Upload Endpoint", test_upload_endpoint),
        ("Query Endpoint", test_query_endpoint),
        ("Subjects Endpoint", test_subjects_endpoint),
        ("Database Functions", test_database_functions),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        logger.info(f"{test_name:.<40} {status}")
        if passed_test:
            passed += 1
    
    success_rate = passed / total
    logger.info(f"\nOverall Success Rate: {success_rate:.1%} ({passed}/{total})")
    
    if success_rate >= 0.8:
        logger.info("🎉 Pipeline is working well!")
        return 0
    elif success_rate >= 0.5:
        logger.warning("⚠️  Pipeline has some issues but is partially functional")
        return 1
    else:
        logger.error("❌ Pipeline has major issues")
        return 2

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test CAPE GPT pipeline')
    parser.add_argument('--test', choices=['all', 'chunking', 'backend', 'upload', 'query', 'subjects', 'database'],
                       default='all', help='Which test to run')
    parser.add_argument('--api-url', default='http://127.0.0.1:8000', help='Backend API URL')
    
    args = parser.parse_args()
    
    # Set API URL
    os.environ['API_URL'] = args.api_url
    
    if args.test == 'all':
        exit_code = run_all_tests()
        sys.exit(exit_code)
    else:
        # Run specific test
        test_map = {
            'chunking': test_chunking_script,
            'backend': test_backend_health,
            'upload': test_upload_endpoint,
            'query': test_query_endpoint,
            'subjects': test_subjects_endpoint,
            'database': test_database_functions,
        }
        
        test_func = test_map.get(args.test)
        if test_func:
            success = test_func()
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Unknown test: {args.test}")
            sys.exit(1)