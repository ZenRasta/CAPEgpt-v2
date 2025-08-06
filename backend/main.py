from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import io
from google.cloud import vision
import requests
from openai import OpenAI
from supabase import create_client
import numpy as np
import re
import json
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Dict, Any, Tuple, Optional
import hashlib
import base64
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MATHPIX_APP_ID = os.getenv('MATHPIX_APP_ID')
MATHPIX_APP_KEY = os.getenv('MATHPIX_APP_KEY')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Validate required environment variables
required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENROUTER_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

if GOOGLE_CREDENTIALS:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CREDENTIALS

# Initialize clients
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    openai_client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=OPENROUTER_API_KEY)
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Successfully initialized all clients")
    # Debug: Check if API keys are loaded
    logger.info(f"MATHPIX_APP_ID loaded: {'Yes' if MATHPIX_APP_ID else 'No'}")
    logger.info(f"MATHPIX_APP_KEY loaded: {'Yes' if MATHPIX_APP_KEY else 'No'}")
    logger.info(f"GOOGLE_CREDENTIALS path: {GOOGLE_CREDENTIALS}")
    logger.info(f"OPENROUTER_API_KEY loaded: {'Yes' if OPENROUTER_API_KEY else 'No'}")
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    raise

app = FastAPI(
    title="CAPE GPT API",
    description="API for CAPE GPT - AI-powered CAPE exam question solver",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def embed_text(text: str) -> List[float]:
    """Generate embeddings for text using sentence transformers."""
    try:
        return embedding_model.encode(text).tolist()
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embeddings")

def is_math_heavy(image_bytes: bytes) -> bool:
    """Determine if image contains heavy mathematical content."""
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)
        
        if not response.text_annotations:
            return False
            
        text = response.text_annotations[0].description
        
        # Count mathematical symbols and patterns
        math_symbols = len(re.findall(r'[+\-*/=^()∫∑√π∞≤≥≠±∂∇]', text))
        fraction_patterns = len(re.findall(r'\d+/\d+', text))
        equation_patterns = len(re.findall(r'[a-zA-Z]\s*=\s*[^a-zA-Z\s]', text))
        
        # Consider it math-heavy if it has multiple indicators
        return (math_symbols >= 5) or (fraction_patterns >= 2) or (equation_patterns >= 1)
        
    except Exception as e:
        logger.warning(f"Error in math detection, defaulting to non-math: {e}")
        return False

class MathpixResult:
    """Data class for Mathpix processing results."""
    def __init__(self, markdown: str = "", svg: str = "", confidence: float = 0.0, 
                 error: str = None, uses_svg: bool = False):
        self.markdown = markdown
        self.svg = svg
        self.confidence = confidence
        self.error = error
        self.uses_svg = uses_svg

def process_with_mathpix(image_bytes: bytes, filename: str) -> MathpixResult:
    """Enhanced Mathpix processing that returns both Markdown and SVG outputs."""
    try:
        if not (MATHPIX_APP_ID and MATHPIX_APP_KEY):
            return MathpixResult(error="Mathpix credentials not configured")
        
        # First, get Markdown output
        markdown_response = requests.post(
            'https://api.mathpix.com/v3/text',
            files={'file': (filename, image_bytes, 'image/jpeg')},
            headers={
                'app_id': MATHPIX_APP_ID,
                'app_key': MATHPIX_APP_KEY
            },
            data={
                'options_json': json.dumps({
                    'math_inline_delimiters': ['$', '$'],
                    'math_display_delimiters': ['$$', '$$'],
                    'rm_spaces': True,
                    'include_asciimath': True,
                    'include_latex': True
                })
            },
            timeout=30
        )
        
        if not markdown_response.ok:
            return MathpixResult(error=f"Mathpix markdown failed: {markdown_response.status_code}")
        
        markdown_data = markdown_response.json()
        markdown_text = markdown_data.get('text', '')
        confidence = markdown_data.get('confidence', 0.0)
        
        # Try to get SVG output
        svg_text = ""
        try:
            svg_response = requests.post(
                'https://api.mathpix.com/v3/text',
                files={'file': (filename, image_bytes, 'image/jpeg')},
                headers={
                    'app_id': MATHPIX_APP_ID,
                    'app_key': MATHPIX_APP_KEY
                },
                data={
                    'options_json': json.dumps({
                        'formats': ['text', 'html'],
                        'math_inline_delimiters': ['$', '$'],
                        'math_display_delimiters': ['$$', '$$'],
                        'include_svg': True
                    })
                },
                timeout=30
            )
            
            if svg_response.ok:
                svg_data = svg_response.json()
                svg_text = svg_data.get('html', '')
                # Extract SVG content if present in HTML
                if '<svg' in svg_text and '</svg>' in svg_text:
                    import re
                    svg_match = re.search(r'<svg[^>]*>.*?</svg>', svg_text, re.DOTALL)
                    if svg_match:
                        svg_text = svg_match.group(0)
                else:
                    svg_text = ""
        except Exception as e:
            logger.warning(f"SVG extraction failed: {e}")
            svg_text = ""
        
        # Apply heuristic to decide if SVG is needed
        uses_svg = should_use_svg(markdown_text, confidence, svg_text)
        
        return MathpixResult(
            markdown=markdown_text,
            svg=svg_text,
            confidence=confidence,
            uses_svg=uses_svg
        )
        
    except Exception as e:
        logger.error(f"Mathpix processing failed: {e}")
        return MathpixResult(error=str(e))

def should_use_svg(markdown: str, confidence: float, svg: str) -> bool:
    """Heuristic to determine if SVG rendering should be used over Markdown/KaTeX."""
    # Use SVG if confidence is low (likely complex layout)
    if confidence < 0.7:
        return True and bool(svg)
    
    # Use SVG if markdown contains many fallback images or unknown symbols
    fallback_indicators = [
        r'\includegraphics',  # LaTeX image includes
        r'!\[.*?\]\(',       # Markdown images
        r'<img',             # HTML images
        r'\?{3,}',           # Multiple question marks (OCR uncertainty)
        r'\_\_+',            # Multiple underscores (likely diagram/table)
    ]
    
    fallback_count = sum(len(re.findall(pattern, markdown)) for pattern in fallback_indicators)
    if fallback_count >= 3:
        return True and bool(svg)
    
    # Use SVG if content appears to be heavily diagrammatic
    diagram_indicators = ['diagram', 'figure', 'chart', 'graph', 'table']
    if any(indicator in markdown.lower() for indicator in diagram_indicators):
        return True and bool(svg)
    
    # Use SVG if the content is very short (likely a single equation/diagram)
    if len(markdown.strip()) < 50 and svg:
        return True
    
    # Default to Markdown/KaTeX for better performance
    return False

def ocr_image(image_bytes: bytes, is_math: bool) -> str:
    """Extract text from image using appropriate OCR service."""
    try:
        if is_math and MATHPIX_APP_ID and MATHPIX_APP_KEY:
            # Use Mathpix for math-heavy content
            response = requests.post(
                'https://api.mathpix.com/v3/text',
                files={'file': ('image.jpg', image_bytes, 'image/jpeg')},
                headers={
                    'app_id': MATHPIX_APP_ID,
                    'app_key': MATHPIX_APP_KEY
                },
                data={
                    'options_json': json.dumps({
                        'math_inline_delimiters': ['$', '$'],
                        'math_display_delimiters': ['$$', '$$'],
                        'rm_spaces': True
                    })
                },
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                return result.get('text', '')
            else:
                logger.warning(f"Mathpix failed: {response.status_code}, falling back to Google Vision")
        
        # Use Google Vision as fallback or for non-math content
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)
        
        if response.text_annotations:
            return response.text_annotations[0].description
        else:
            return ""
            
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract text from image")

def vector_search(table: str, embedding: List[float], subject: str, limit: int = 8, threshold: float = 0.7) -> List[Dict[str, Any]]:
    """Enhanced vector similarity search with hybrid retrieval."""
    try:
        # Use the RPC function for better vector search
        if table == 'question_chunks':
            response = supabase.rpc(
                'match_question_chunks',
                {
                    'query_embedding': embedding,
                    'query_subject': subject,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
        else:  # syllabus_chunks
            response = supabase.rpc(
                'match_syllabus_sections',
                {
                    'query_embedding': embedding,
                    'query_subject': subject,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
        
        results = response.data if response.data else []
        
        # If we don't get enough results with high threshold, try lower threshold
        if len(results) < limit // 2 and threshold > 0.5:
            logger.info(f"Expanding search with lower threshold for {table}")
            return vector_search(table, embedding, subject, limit, threshold=0.5)
        
        return results
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        # Enhanced fallback with text search
        try:
            response = supabase.table(table).select('*').eq('subject', subject).limit(limit).execute()
            return response.data if response.data else []
        except Exception as fallback_error:
            logger.error(f"Fallback search also failed: {fallback_error}")
            return []

def hybrid_retrieval(query_text: str, subject: str, embedding: List[float]) -> Dict[str, List[Dict]]:
    """Advanced hybrid retrieval combining semantic and keyword search."""
    # Semantic search
    semantic_questions = vector_search('question_chunks', embedding, subject, 10)
    semantic_syllabus = vector_search('syllabus_chunks', embedding, subject, 8)
    
    # Keyword extraction for backup search
    keywords = extract_keywords(query_text)
    
    # If semantic search returns few results, supplement with keyword search
    if len(semantic_questions) < 5:
        keyword_questions = keyword_search('question_chunks', keywords, subject, 5)
        semantic_questions.extend(keyword_questions)
    
    if len(semantic_syllabus) < 3:
        keyword_syllabus = keyword_search('syllabus_chunks', keywords, subject, 3)
        semantic_syllabus.extend(keyword_syllabus)
    
    # Remove duplicates and rank by relevance
    questions = remove_duplicates_and_rank(semantic_questions)
    syllabus = remove_duplicates_and_rank(semantic_syllabus)
    
    return {'questions': questions[:8], 'syllabus': syllabus[:5]}

def extract_keywords(text: str) -> List[str]:
    """Extract mathematical and subject-specific keywords from query."""
    # Common mathematical terms
    math_terms = ['derivative', 'integral', 'limit', 'function', 'equation', 'matrix', 
                  'vector', 'probability', 'statistics', 'geometry', 'algebra', 'calculus',
                  'differentiate', 'integrate', 'solve', 'find', 'calculate', 'prove']
    
    # Extract words that might be important
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter for mathematical terms and proper nouns
    keywords = []
    for word in words:
        if word in math_terms or word.istitle() or len(word) > 6:
            keywords.append(word)
    
    # Add mathematical symbols and expressions
    math_symbols = re.findall(r'[+\-*/=^()∫∑√π∞≤≥≠±∂∇]|\d+', text)
    keywords.extend(math_symbols)
    
    return list(set(keywords))  # Remove duplicates

def keyword_search(table: str, keywords: List[str], subject: str, limit: int) -> List[Dict]:
    """Perform keyword-based search as fallback."""
    try:
        results = []
        content_field = 'content' if table == 'question_chunks' else 'chunk_text'
        
        for keyword in keywords[:5]:  # Limit to top 5 keywords
            response = supabase.table(table).select('*').eq('subject', subject).ilike(content_field, f'%{keyword}%').limit(3).execute()
            if response.data:
                results.extend(response.data)
        
        return results[:limit]
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return []

def remove_duplicates_and_rank(items: List[Dict]) -> List[Dict]:
    """Remove duplicates and rank by similarity score."""
    seen_ids = set()
    unique_items = []
    
    for item in items:
        item_id = item.get('id')
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_items.append(item)
    
    # Sort by similarity score if available
    try:
        unique_items.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    except:
        pass  # If sorting fails, keep original order
    
    return unique_items

def create_enhanced_context(questions: List[Dict], syllabus: List[Dict], query_text: str) -> Tuple[str, str]:
    """Create enhanced context with better formatting and relevance."""
    question_context = ""
    if questions:
        question_context = "\n\n## Similar Past Questions:\n"
        for i, q in enumerate(questions[:4], 1):  # Show top 4
            content = q.get('content', '')
            year = q.get('year', 'Unknown')
            paper = q.get('paper', '')
            similarity = q.get('similarity', 0)
            
            # Truncate long content intelligently
            if len(content) > 250:
                # Try to end at sentence boundary
                truncated = content[:250]
                last_period = truncated.rfind('.')
                if last_period > 150:
                    content = truncated[:last_period + 1]
                else:
                    content = truncated + "..."
            
            question_context += f"{i}. **({year} {paper})** {content}\n\n"
    
    syllabus_context = ""
    if syllabus:
        syllabus_context = "\n\n## Relevant Syllabus Content:\n"
        for i, s in enumerate(syllabus[:3], 1):  # Show top 3
            topic = s.get('topic_title', 'Unknown Topic')
            chunk_text = s.get('chunk_text', '')
            module = s.get('module', '')
            
            # Truncate syllabus content
            if len(chunk_text) > 200:
                chunk_text = chunk_text[:200] + "..."
            
            syllabus_context += f"{i}. **{topic}** ({module})\n   {chunk_text}\n\n"
    
    return question_context, syllabus_context

async def track_query(query_text: str, subject: str, question_ids: List[int], session_id: str = None):
    """Track query for popularity analytics."""
    try:
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        
        supabase.table('question_queries').insert({
            'query_text': query_text,
            'query_hash': query_hash,
            'subject': subject,
            'matched_question_ids': question_ids,
            'user_session_id': session_id or 'anonymous'
        }).execute()
        
        logger.info(f"Tracked query for subject {subject} with {len(question_ids)} matched questions")
    except Exception as e:
        logger.warning(f"Query tracking failed: {e}")

def calculate_probability(topics: List[str], subject: str) -> Dict[str, str]:
    """Calculate probability of topic reappearance based on historical data."""
    try:
        probabilities = {}
        for topic in topics:
            # First try topic_stats materialized view
            response = supabase.table('topic_stats').select('*').eq('subject', subject).eq('topic_title', topic).execute()
            
            if response.data:
                # Use materialized view data if available
                recent_years = [row for row in response.data if row.get('year', 0) >= 2020]
                total_recent_years = len(set(row.get('year') for row in recent_years if row.get('year')))
                appearances = len(recent_years)
                
                if total_recent_years > 0:
                    prob = appearances / max(total_recent_years, 5)
                    if prob >= 0.7:
                        probabilities[topic] = "High"
                    elif prob >= 0.3:
                        probabilities[topic] = "Medium"
                    else:
                        probabilities[topic] = "Low"
                else:
                    probabilities[topic] = "Unknown"
            else:
                # Fallback: Calculate directly from topic mappings if materialized view is empty
                logger.info(f"Topic_stats empty for {topic}, using fallback calculation")
                
                # Get syllabus chunk for this topic
                syllabus_response = supabase.table('syllabus_chunks').select('id').eq('subject', subject).eq('topic_title', topic).execute()
                
                if syllabus_response.data:
                    topic_id = syllabus_response.data[0]['id']
                    
                    # Get mappings for this topic
                    mappings_response = supabase.table('question_topic_mappings').select('question_id').eq('topic_id', topic_id).execute()
                    
                    if mappings_response.data:
                        # Get question years for these mappings
                        question_ids = [m['question_id'] for m in mappings_response.data]
                        
                        # Get years from questions (batch query)
                        years_data = []
                        for q_id in question_ids:
                            q_response = supabase.table('question_chunks').select('year').eq('id', q_id).execute()
                            if q_response.data and q_response.data[0].get('year'):
                                years_data.append(q_response.data[0]['year'])
                        
                        if years_data:
                            recent_years = [y for y in years_data if y >= 2020]
                            unique_years = len(set(recent_years))
                            
                            if unique_years > 0:
                                # Simple probability based on how many recent years it appeared
                                prob = unique_years / 5  # Assume 5 year window
                                if prob >= 0.4:  # Adjusted for smaller dataset
                                    probabilities[topic] = "Medium"  
                                elif prob >= 0.2:
                                    probabilities[topic] = "Low"
                                else:
                                    probabilities[topic] = "Low"
                            else:
                                probabilities[topic] = "Low"
                        else:
                            probabilities[topic] = "Low"
                    else:
                        probabilities[topic] = "Unknown"
                else:
                    probabilities[topic] = "Unknown"
                
        return probabilities
        
    except Exception as e:
        logger.error(f"Probability calculation failed: {e}")
        return {topic: "Unknown" for topic in topics}

def upload_to_storage(file_bytes: bytes, filename: str, user_id: str) -> str:
    """Upload file to Supabase storage and return storage path."""
    try:
        # Create user-specific path
        file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        storage_path = f"{user_id}/{unique_filename}"
        
        # Upload to Supabase storage
        response = supabase.storage.from_("questions").upload(
            storage_path, 
            file_bytes,
            {"content-type": f"image/{file_extension}" if file_extension in ['png', 'jpg', 'jpeg'] else "application/octet-stream"}
        )
        
        # Check if upload was successful (new Supabase client format)
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Storage upload failed: {response.error}")
        
        # For newer versions of supabase-py, check the data attribute
        if hasattr(response, 'data') and response.data is None:
            # If data is None, there might be an error
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Storage upload failed: {response.error}")
        
        logger.info(f"File uploaded successfully to: {storage_path}")
        return storage_path
        
    except Exception as e:
        logger.error(f"Storage upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")

def classify_question(content: str, filename: str) -> dict:
    """Simple classification of question attributes."""
    content_lower = content.lower()
    filename_lower = filename.lower()
    
    # Subject detection
    subject = "Pure Mathematics"  # Default
    if any(term in content_lower for term in ['physics', 'force', 'velocity', 'acceleration']):
        subject = "Physics"
    elif any(term in content_lower for term in ['chemistry', 'molecule', 'reaction', 'element']):
        subject = "Chemistry"
    elif any(term in content_lower for term in ['applied', 'statistics', 'probability']):
        subject = "Applied Mathematics"
    
    # Year detection from filename
    year_match = re.search(r'20\d{2}', filename_lower)
    estimated_year = int(year_match.group()) if year_match else None
    
    # Question type detection
    question_type = "short_answer"  # Default
    if any(term in content_lower for term in ['a)', 'b)', 'c)', 'd)', 'multiple choice']):
        question_type = "multiple_choice"
    elif len(content) > 500:
        question_type = "essay"
    
    # Topic extraction (simple keyword matching)
    topics = []
    topic_keywords = {
        'calculus': ['derivative', 'integral', 'limit', 'differentiat', 'integrat'],
        'algebra': ['equation', 'polynomial', 'quadratic', 'linear'],
        'geometry': ['triangle', 'circle', 'angle', 'area', 'volume'],
        'trigonometry': ['sin', 'cos', 'tan', 'sine', 'cosine', 'tangent'],
        'statistics': ['mean', 'median', 'standard deviation', 'probability']
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            topics.append(topic)
    
    return {
        'subject': subject,
        'estimated_year': estimated_year,
        'question_type': question_type,
        'topics': topics
    }

async def process_question_async(question_id: str, file_bytes: bytes, filename: str):
    """Asynchronously process a question with Mathpix."""
    try:
        # Update status to processing
        supabase.table('questions').update({
            'processing_status': 'processing',
            'updated_at': datetime.now().isoformat()
        }).eq('id', question_id).execute()
        
        # Process with Mathpix
        mathpix_result = process_with_mathpix(file_bytes, filename)
        
        if mathpix_result.error:
            # Try Google Vision as fallback
            try:
                is_math = is_math_heavy(file_bytes)
                fallback_text = ocr_image(file_bytes, is_math)
                
                # Update with fallback results
                supabase.table('questions').update({
                    'ocr_fallback_text': fallback_text,
                    'processing_status': 'completed',
                    'processing_error': mathpix_result.error,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', question_id).execute()
            except Exception as fallback_error:
                # Both MathPix and Google Vision failed - provide helpful message
                error_msg = "OCR services are not configured. Please upload a text description of your question or configure OCR APIs."
                supabase.table('questions').update({
                    'processing_status': 'failed',
                    'processing_error': error_msg,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', question_id).execute()
        else:
            # Classify the question
            classification = classify_question(mathpix_result.markdown, filename)
            
            # Update with successful results
            supabase.table('questions').update({
                'mathpix_markdown': mathpix_result.markdown,
                'mathpix_svg': mathpix_result.svg,
                'mathpix_confidence': mathpix_result.confidence,
                'uses_svg': mathpix_result.uses_svg,
                'processing_status': 'completed',
                'subject': classification['subject'],
                'estimated_year': classification['estimated_year'],
                'question_type': classification['question_type'],
                'topics': classification['topics'],
                'updated_at': datetime.now().isoformat()
            }).eq('id', question_id).execute()
        
    except Exception as e:
        logger.error(f"Async processing failed for question {question_id}: {e}")
        # Update with error status
        supabase.table('questions').update({
            'processing_status': 'failed',
            'processing_error': str(e),
            'updated_at': datetime.now().isoformat()
        }).eq('id', question_id).execute()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "CAPE GPT API is running", "version": "1.0.0"}

@app.post('/upload')
async def upload_image(file: UploadFile = File(...)):
    """Upload and process image to extract text."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await file.read()
        
        # Validate file size (max 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Determine if math-heavy and extract text
        is_math = is_math_heavy(image_bytes)
        text = ocr_image(image_bytes, is_math)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the image")
        
        # Generate hash for caching
        image_hash = hashlib.md5(image_bytes).hexdigest()
        
        return {
            'text': text,
            'is_math_heavy': is_math,
            'image_hash': image_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image")

class QueryRequest(BaseModel):
    text: str
    subject: str

@app.post('/query')
async def query(request: QueryRequest):
    """Enhanced query processing with improved RAG implementation."""
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Query text cannot be empty")
        
        valid_subjects = ['Pure Mathematics', 'Applied Mathematics', 'Physics', 'Chemistry']
        if request.subject not in valid_subjects:
            raise HTTPException(status_code=400, detail=f"Subject must be one of: {valid_subjects}")
        
        # Generate embedding
        embedding = embed_text(request.text)
        
        # Enhanced hybrid retrieval
        retrieval_results = hybrid_retrieval(request.text, request.subject, embedding)
        questions = retrieval_results['questions']
        syllabus = retrieval_results['syllabus']
        
        # Create enhanced context
        question_context, syllabus_context = create_enhanced_context(questions, syllabus, request.text)
        
        # Enhanced GPT prompt with better instructions
        prompt = f"""You are an expert CAPE {request.subject} tutor with deep knowledge of Caribbean exam patterns and mathematical problem-solving techniques.

**Student Question:** {request.text}
{question_context}{syllabus_context}

**Instructions:**
1. Provide a comprehensive, step-by-step solution that a CAPE student can easily follow
2. Use proper mathematical notation with LaTeX formatting ($ for inline, $$ for display)
3. Explain the conceptual reasoning behind each step
4. Highlight key formulas, theorems, or principles being applied
5. If applicable, mention common mistakes students make with this type of problem
6. Connect the solution to the relevant syllabus objectives shown above

**Solution Format:**
Start with a brief overview of the approach, then provide numbered steps with clear explanations. End with a summary of key concepts used."""

        # Get GPT response with improved parameters
        response = openai_client.chat.completions.create(
            model='openai/gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': f'You are an expert CAPE {request.subject} tutor. Always provide clear, step-by-step solutions with proper mathematical notation.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.1,
            max_tokens=2500,  # Increased for more detailed solutions
            presence_penalty=0.1  # Encourage diverse explanations
        )
        
        answer = response.choices[0].message.content
        
        # Enhanced insights extraction
        years = list(set([q.get('year') for q in questions if q.get('year')]))
        years.sort(reverse=True)
        
        topics = list(set([s.get('topic_title') for s in syllabus if s.get('topic_title')]))
        
        # Get question patterns for additional insights
        question_patterns = []
        for q in questions[:5]:
            if q.get('question_id'):
                question_patterns.append(q['question_id'])
        
        # Calculate probabilities
        probabilities = calculate_probability(topics, request.subject)
        
        # Track the query for popularity analytics
        question_ids = [q.get('id') for q in questions if q.get('id')]
        await track_query(request.text, request.subject, question_ids)
        
        # Enhanced response with more metadata
        return {
            'answer': answer,
            'years': years[:12],  # Show more years
            'topics': topics[:6],  # Show more topics
            'probabilities': probabilities,
            'similar_questions_count': len(questions),
            'syllabus_matches_count': len(syllabus),
            'question_patterns': question_patterns[:5],
            'confidence_score': min(len(questions) / 5.0, 1.0),  # Confidence based on matches found
            'search_quality': {
                'semantic_matches': len([q for q in questions if q.get('similarity', 0) > 0.8]),
                'keyword_matches': len(questions) - len([q for q in questions if q.get('similarity', 0) > 0.8]),
                'total_context_length': len(question_context) + len(syllabus_context)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced query processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")

@app.get('/stats/topic')
async def get_topic_stats(subject: str, topic: str = None):
    """Get topic statistics for probability calculations."""
    try:
        query = supabase.table('topic_stats').select('*').eq('subject', subject)
        
        if topic:
            query = query.eq('topic_title', topic)
        
        response = query.execute()
        
        return {
            'stats': response.data if response.data else [],
            'total_count': len(response.data) if response.data else 0
        }
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get('/popular-questions')
async def get_popular_questions(subject: str, limit: int = 10):
    """Get most popular questions by subject."""
    try:
        # Validate subject
        valid_subjects = ['Pure Mathematics', 'Applied Mathematics', 'Physics', 'Chemistry']
        if subject not in valid_subjects:
            raise HTTPException(status_code=400, detail=f"Subject must be one of: {valid_subjects}")
        
        # Validate limit
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
        
        # Get popular questions using RPC function
        response = supabase.rpc('get_popular_questions', {
            'query_subject': subject,
            'result_limit': limit
        }).execute()
        
        popular_questions = response.data if response.data else []
        
        # Enrich with additional metadata
        enriched_questions = []
        for question in popular_questions:
            enriched_question = {
                'id': question.get('question_id'),
                'content': question.get('content', '')[:200] + ('...' if len(question.get('content', '')) > 200 else ''),
                'year': question.get('year'),
                'paper': question.get('paper'),
                'question_id': question.get('question_text'),
                'topic': question.get('topic'),
                'query_count': question.get('query_count', 0),
                'unique_users': question.get('unique_users', 0),
                'popularity_rank': question.get('popularity_rank', 0),
                'last_queried': question.get('last_queried')
            }
            enriched_questions.append(enriched_question)
        
        return {
            'popular_questions': enriched_questions,
            'total_count': len(enriched_questions),
            'subject': subject,
            'period': 'Last 30 days'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Popular questions retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular questions")

@app.get('/query-stats')
async def get_query_stats(subject: str = None, days: int = 30):
    """Get query statistics and trends."""
    try:
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        # Build query
        query = supabase.table('question_queries').select('*')
        
        if subject:
            valid_subjects = ['Pure Mathematics', 'Applied Mathematics', 'Physics', 'Chemistry']
            if subject not in valid_subjects:
                raise HTTPException(status_code=400, detail=f"Subject must be one of: {valid_subjects}")
            query = query.eq('subject', subject)
        
        # Filter by date range
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        query = query.gte('created_at', cutoff_date.isoformat())
        
        response = query.execute()
        queries = response.data if response.data else []
        
        # Calculate statistics
        total_queries = len(queries)
        unique_users = len(set(q.get('user_session_id') for q in queries if q.get('user_session_id')))
        subjects_breakdown = {}
        
        for query_record in queries:
            subj = query_record.get('subject', 'Unknown')
            if subj not in subjects_breakdown:
                subjects_breakdown[subj] = 0
            subjects_breakdown[subj] += 1
        
        return {
            'total_queries': total_queries,
            'unique_users': unique_users,
            'subjects_breakdown': subjects_breakdown,
            'period_days': days,
            'average_queries_per_day': round(total_queries / max(days, 1), 2) if total_queries > 0 else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get query statistics")

@app.get('/subjects')
async def get_subjects():
    """Get available subjects."""
    return {
        'subjects': ['Pure Mathematics', 'Applied Mathematics', 'Physics', 'Chemistry']
    }

# New Question Storage Endpoints

class QuestionUploadResponse(BaseModel):
    id: str
    processing_status: str
    message: str

@app.post('/questions/upload', response_model=QuestionUploadResponse)
async def upload_question(file: UploadFile = File(...)):
    """Upload a question file and process it with Mathpix."""
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith(('image/', 'application/pdf')):
            raise HTTPException(status_code=400, detail="File must be an image or PDF")
        
        if file.size and file.size > 25 * 1024 * 1024:  # 25MB limit
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")
        
        # Read file
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # For now, use a mock user ID (in production, get from auth)
        user_id = "00000000-0000-0000-0000-000000000001"  # Mock UUID format for testing
        
        # Upload to storage
        storage_path = upload_to_storage(file_bytes, file.filename, user_id)
        
        # Generate signed URL (expires in 24 hours)
        signed_url_response = supabase.storage.from_("questions").create_signed_url(
            storage_path, 60 * 60 * 24  # 24 hours
        )
        # Handle new Supabase client format for signed URL
        signed_url = None
        if signed_url_response:
            if hasattr(signed_url_response, 'data') and signed_url_response.data:
                signed_url = signed_url_response.data.get('signedURL') if isinstance(signed_url_response.data, dict) else signed_url_response.data
            elif hasattr(signed_url_response, 'signedURL'):
                signed_url = signed_url_response.signedURL
            elif isinstance(signed_url_response, dict):
                signed_url = signed_url_response.get('signedURL')
        
        # Create question record
        question_data = {
            'user_id': user_id,
            'original_filename': file.filename,
            'file_size': len(file_bytes),
            'file_type': file.content_type,
            'storage_path': storage_path,
            'signed_url': signed_url,
            'processing_status': 'pending'
        }
        
        result = supabase.table('questions').insert(question_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create question record")
        
        question_id = result.data[0]['id']
        
        # Start async processing
        import asyncio
        asyncio.create_task(process_question_async(question_id, file_bytes, file.filename))
        
        return QuestionUploadResponse(
            id=question_id,
            processing_status='pending',
            message='Question uploaded successfully. Processing started.'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload question")

class QuestionResponse(BaseModel):
    id: str
    original_filename: str
    mathpix_markdown: Optional[str]
    mathpix_svg: Optional[str]
    uses_svg: bool
    processing_status: str
    processing_error: Optional[str]
    subject: Optional[str]
    topics: Optional[List[str]]
    created_at: str
    signed_url: Optional[str]

@app.get('/questions/{question_id}', response_model=QuestionResponse)
async def get_question(question_id: str):
    """Get a specific question by ID."""
    try:
        # For now, use mock user ID (in production, get from auth and filter by user)
        user_id = "00000000-0000-0000-0000-000000000001"  # Mock UUID format for testing
        
        result = supabase.table('questions').select('*').eq('id', question_id).eq('user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question = result.data[0]
        
        # Refresh signed URL if needed (if older than 23 hours)
        signed_url = question.get('signed_url')
        if question.get('storage_path'):
            try:
                signed_url_response = supabase.storage.from_("questions").create_signed_url(
                    question['storage_path'], 60 * 60 * 24  # 24 hours
                )
                # Handle new Supabase client format for signed URL
                if signed_url_response:
                    if hasattr(signed_url_response, 'data') and signed_url_response.data:
                        signed_url = signed_url_response.data.get('signedURL') if isinstance(signed_url_response.data, dict) else signed_url_response.data
                    elif hasattr(signed_url_response, 'signedURL'):
                        signed_url = signed_url_response.signedURL
                    elif isinstance(signed_url_response, dict):
                        signed_url = signed_url_response.get('signedURL')
            except Exception as e:
                logger.warning(f"Failed to refresh signed URL: {e}")
        
        return QuestionResponse(
            id=question['id'],
            original_filename=question['original_filename'],
            mathpix_markdown=question.get('mathpix_markdown'),
            mathpix_svg=question.get('mathpix_svg'),
            uses_svg=question.get('uses_svg', False),
            processing_status=question['processing_status'],
            processing_error=question.get('processing_error'),
            subject=question.get('subject'),
            topics=question.get('topics', []),
            created_at=question['created_at'],
            signed_url=signed_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve question")

class QuestionListResponse(BaseModel):
    questions: List[QuestionResponse]
    total_count: int

@app.get('/questions', response_model=QuestionListResponse)
async def list_questions(limit: int = 20, offset: int = 0, subject: Optional[str] = None):
    """List user's questions with pagination."""
    try:
        # For now, use mock user ID (in production, get from auth)
        user_id = "00000000-0000-0000-0000-000000000001"  # Mock UUID format for testing
        
        query = supabase.table('questions').select('*').eq('user_id', user_id)
        
        if subject:
            query = query.eq('subject', subject)
        
        # Get total count
        count_result = query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        # Get paginated results
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        questions = []
        for question in result.data or []:
            # Refresh signed URL
            signed_url = question.get('signed_url')
            if question.get('storage_path'):
                try:
                    signed_url_response = supabase.storage.from_("questions").create_signed_url(
                        question['storage_path'], 60 * 60 * 24  # 24 hours
                    )
                    # Handle new Supabase client format for signed URL
                    if signed_url_response:
                        if hasattr(signed_url_response, 'data') and signed_url_response.data:
                            signed_url = signed_url_response.data.get('signedURL') if isinstance(signed_url_response.data, dict) else signed_url_response.data
                        elif hasattr(signed_url_response, 'signedURL'):
                            signed_url = signed_url_response.signedURL
                        elif isinstance(signed_url_response, dict):
                            signed_url = signed_url_response.get('signedURL')
                except Exception as e:
                    logger.warning(f"Failed to refresh signed URL: {e}")
            
            questions.append(QuestionResponse(
                id=question['id'],
                original_filename=question['original_filename'],
                mathpix_markdown=question.get('mathpix_markdown'),
                mathpix_svg=question.get('mathpix_svg'),
                uses_svg=question.get('uses_svg', False),
                processing_status=question['processing_status'],
                processing_error=question.get('processing_error'),
                subject=question.get('subject'),
                topics=question.get('topics', []),
                created_at=question['created_at'],
                signed_url=signed_url
            ))
        
        return QuestionListResponse(
            questions=questions,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Question listing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list questions")

@app.get('/questions/search')
async def search_questions(q: str, limit: int = 20, subject: Optional[str] = None):
    """Search questions using full-text search."""
    try:
        # For now, use mock user ID (in production, get from auth)
        user_id = "00000000-0000-0000-0000-000000000001"  # Mock UUID format for testing
        
        # Use the search function from the migration
        result = supabase.rpc('search_questions', {
            'search_query': q,
            'user_filter': user_id,
            'subject_filter': subject,
            'limit_count': limit
        }).execute()
        
        questions = []
        for question in result.data or []:
            questions.append({
                'id': question['id'],
                'original_filename': question['original_filename'],
                'mathpix_markdown': question['mathpix_markdown'],
                'uses_svg': question['uses_svg'],
                'subject': question['subject'],
                'topics': question['topics'],
                'created_at': question['created_at'],
                'relevance_score': question['rank']
            })
        
        return {
            'questions': questions,
            'query': q,
            'total_count': len(questions)
        }
        
    except Exception as e:
        logger.error(f"Question search failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to search questions")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
