"""
Sample data loader for CAPE GPT database.
This script loads sample questions and syllabus data for testing purposes.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.append(str(Path(__file__).parent.parent))

from backend.main import supabase, embed_text
import json

# Sample CAPE questions for testing
SAMPLE_QUESTIONS = [
    {
        "content": "Solve the quadratic equation x² + 5x + 6 = 0",
        "subject": "Pure Mathematics",
        "year": 2023,
        "paper": "Paper 1",
        "question_id": "1a",
        "topic": "Algebra",
        "sub_topic": "Quadratic Equations"
    },
    {
        "content": "Find the derivative of f(x) = 3x³ - 2x² + 5x - 1",
        "subject": "Pure Mathematics", 
        "year": 2023,
        "paper": "Paper 2",
        "question_id": "2b",
        "topic": "Calculus",
        "sub_topic": "Differentiation"
    },
    {
        "content": "A particle moves in a straight line with velocity v = 2t + 3. Find the displacement after 4 seconds if the initial displacement is 0.",
        "subject": "Applied Mathematics",
        "year": 2022,
        "paper": "Paper 1", 
        "question_id": "3a",
        "topic": "Mechanics",
        "sub_topic": "Kinematics"
    },
    {
        "content": "Calculate the force required to accelerate a 5kg mass at 2 m/s²",
        "subject": "Physics",
        "year": 2023,
        "paper": "Paper 1",
        "question_id": "1c",
        "topic": "Mechanics",
        "sub_topic": "Newton's Laws"
    },
    {
        "content": "Balance the chemical equation: C₂H₆ + O₂ → CO₂ + H₂O",
        "subject": "Chemistry",
        "year": 2022,
        "paper": "Paper 1",
        "question_id": "2a",
        "topic": "Chemical Reactions",
        "sub_topic": "Balancing Equations"
    }
]

# Sample syllabus content
SAMPLE_SYLLABUS = [
    {
        "subject": "Pure Mathematics",
        "module": "Unit 1 Module 1",
        "topic_title": "Algebra and Functions",
        "chunk_text": "Students should be able to solve quadratic equations using factorization, completing the square, and the quadratic formula. They should understand the relationship between roots and coefficients."
    },
    {
        "subject": "Pure Mathematics",
        "module": "Unit 1 Module 2", 
        "topic_title": "Calculus",
        "chunk_text": "Students should be able to differentiate polynomial, exponential, logarithmic, and trigonometric functions. They should understand the concept of limits and continuity."
    },
    {
        "subject": "Applied Mathematics",
        "module": "Unit 1 Module 1",
        "topic_title": "Mechanics",
        "chunk_text": "Students should understand motion in one and two dimensions, including displacement, velocity, and acceleration. They should be able to solve problems involving projectile motion."
    },
    {
        "subject": "Physics",
        "module": "Unit 1 Module 1",
        "topic_title": "Mechanics",
        "chunk_text": "Students should understand Newton's laws of motion and be able to apply them to solve problems involving forces, mass, and acceleration."
    },
    {
        "subject": "Chemistry",
        "module": "Unit 1 Module 1",
        "topic_title": "Chemical Reactions",
        "chunk_text": "Students should be able to balance chemical equations and understand the law of conservation of mass. They should understand different types of chemical reactions."
    }
]

def load_sample_questions():
    """Load sample questions into the database."""
    print("Loading sample questions...")
    
    for question in SAMPLE_QUESTIONS:
        try:
            # Generate embedding
            embedding = embed_text(question["content"])
            
            # Insert into database
            data = {
                "content": question["content"],
                "embedding": embedding,
                "year": question["year"],
                "paper": question["paper"],
                "question_id": question["question_id"],
                "subject": question["subject"],
                "topic": question["topic"],
                "sub_topic": question["sub_topic"]
            }
            
            result = supabase.table("question_chunks").insert(data).execute()
            print(f"✓ Loaded question: {question['question_id']} - {question['content'][:50]}...")
            
        except Exception as e:
            print(f"✗ Error loading question {question['question_id']}: {e}")

def load_sample_syllabus():
    """Load sample syllabus content into the database."""
    print("\nLoading sample syllabus content...")
    
    for syllabus in SAMPLE_SYLLABUS:
        try:
            # Generate embedding
            embedding = embed_text(syllabus["chunk_text"])
            
            # Insert into database
            data = {
                "subject": syllabus["subject"],
                "module": syllabus["module"],
                "topic_title": syllabus["topic_title"],
                "chunk_text": syllabus["chunk_text"],
                "embedding": embedding
            }
            
            result = supabase.table("syllabus_chunks").insert(data).execute()
            print(f"✓ Loaded syllabus: {syllabus['topic_title']} - {syllabus['subject']}")
            
        except Exception as e:
            print(f"✗ Error loading syllabus {syllabus['topic_title']}: {e}")

def create_topic_mappings():
    """Create mappings between questions and syllabus topics."""
    print("\nCreating topic mappings...")
    
    try:
        # Get all questions and syllabus items
        questions = supabase.table("question_chunks").select("*").execute()
        syllabus_items = supabase.table("syllabus_chunks").select("*").execute()
        
        mappings = []
        
        # Simple mapping based on topic matching
        for question in questions.data:
            for syllabus in syllabus_items.data:
                if (question["subject"] == syllabus["subject"] and 
                    question["topic"].lower() in syllabus["topic_title"].lower()):
                    
                    mappings.append({
                        "question_id": question["id"],
                        "topic_id": syllabus["id"],
                        "confidence_score": 0.9
                    })
        
        # Insert mappings
        if mappings:
            result = supabase.table("question_topic_mappings").insert(mappings).execute()
            print(f"✓ Created {len(mappings)} topic mappings")
        
    except Exception as e:
        print(f"✗ Error creating topic mappings: {e}")

def refresh_topic_stats():
    """Refresh the materialized view for topic statistics."""
    print("\nRefreshing topic statistics...")
    
    try:
        # Refresh materialized view
        result = supabase.rpc("refresh_materialized_view", {"view_name": "topic_stats"}).execute()
        print("✓ Topic statistics refreshed")
        
    except Exception as e:
        print(f"✗ Error refreshing topic stats: {e}")
        print("Note: You may need to manually refresh the materialized view in Supabase")

def main():
    """Main function to load all sample data."""
    print("CAPE GPT Sample Data Loader")
    print("=" * 40)
    
    try:
        # Test database connection
        result = supabase.table("question_chunks").select("count", count="exact").execute()
        print(f"Database connected. Current questions: {result.count}")
        
        # Load data
        load_sample_questions()
        load_sample_syllabus()
        create_topic_mappings()
        refresh_topic_stats()
        
        print("\n" + "=" * 40)
        print("✓ Sample data loading completed!")
        print("\nYou can now test the application with these sample questions:")
        for q in SAMPLE_QUESTIONS:
            print(f"  - {q['content']}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your Supabase database with the schema from supabase_db.sql")
        print("2. Added your environment variables to backend/.env")
        print("3. Installed the backend dependencies")

if __name__ == "__main__":
    main()
