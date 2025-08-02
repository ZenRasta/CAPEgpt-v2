#!/usr/bin/env python3
"""
Test script for the enhanced linking system
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
logger = logging.getLogger(__name__)

def test_enhanced_linking():
    """Test the enhanced linking system functionality."""
    try:
        from scripts.intelligent_chunker import IntelligentChunker
        
        print("🔧 Initializing chunker with enhanced linking...")
        chunker = IntelligentChunker()
        
        # Check if LLM client is available
        if chunker.llm_client:
            print("✅ LLM client initialized for enhanced linking")
        else:
            print("⚠️  LLM client not available - will use basic keyword matching")
        
        # Test sample question content
        test_questions = [
            {
                "content": "Find the derivative of f(x) = 3x² + 2x - 5 using the power rule",
                "subject": "Pure Mathematics"
            },
            {
                "content": "Calculate the force required to accelerate a 10kg object at 5 m/s²",
                "subject": "Physics"
            },
            {
                "content": "Balance the equation: CH₄ + O₂ → CO₂ + H₂O",
                "subject": "Chemistry"
            }
        ]
        
        print("\n📝 Testing topic mapping for sample questions...")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Test Question {i} ---")
            print(f"Subject: {question['subject']}")
            print(f"Content: {question['content']}")
            
            # Test the enhanced topic mapping
            try:
                # Simulate a question chunk ID (normally this would come from database)
                mock_question_id = 1000 + i
                
                # Test enhanced topic mappings
                mappings = chunker.create_enhanced_topic_mappings(
                    mock_question_id, 
                    question['content'], 
                    question['subject']
                )
                
                if mappings:
                    print(f"✅ Created {len(mappings)} topic mappings:")
                    for j, mapping in enumerate(mappings, 1):
                        confidence = mapping.get('confidence_score', 0)
                        mapping_type = mapping.get('mapping_type', 'unknown')
                        reasoning = mapping.get('reasoning', 'No reasoning provided')
                        print(f"  {j}. Confidence: {confidence:.2f} | Type: {mapping_type}")
                        if reasoning != 'No reasoning provided':
                            print(f"     Reasoning: {reasoning}")
                else:
                    print("❌ No topic mappings created")
                    
            except Exception as e:
                print(f"❌ Error testing question {i}: {e}")
        
        # Test validation system
        print("\n🔍 Testing mapping validation system...")
        
        # Create mock mappings with different confidence levels
        mock_mappings = [
            {
                'question_id': 1001,
                'topic_id': 101,
                'confidence_score': 0.95,
                'mapping_type': 'llm_enhanced',
                'reasoning': 'Direct match for differentiation using power rule concepts'
            },
            {
                'question_id': 1001,
                'topic_id': 102,
                'confidence_score': 0.65,
                'mapping_type': 'keyword_based',
                'common_keywords': ['derivative', 'function']
            },
            {
                'question_id': 1001,
                'topic_id': 103,
                'confidence_score': 0.25,
                'mapping_type': 'keyword_based',
                'common_keywords': ['x']
            }
        ]
        
        validated = chunker.validate_mapping_quality(mock_mappings)
        print(f"✅ Validated {len(validated)} out of {len(mock_mappings)} mappings")
        
        for mapping in validated:
            confidence = mapping['confidence_score']
            notes = mapping.get('validation_notes', 'No adjustments')
            print(f"  - Confidence: {confidence:.2f} | {notes}")
        
        print("\n🎉 Enhanced linking system test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_enhanced_linking()