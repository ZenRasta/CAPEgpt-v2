#!/usr/bin/env python3
"""
Intelligent Document Chunking Script for CAPE GPT
=================================================

This script creates optimal chunks for storage in Supabase vector database:
1. Uses Google Vision OCR for poor quality scans
2. Integrates Mathpix API for math notation conversion
3. Creates semantic chunks optimized for mathematical content
4. Implements RAG-ready embeddings for question retrieval
"""

import os
import re
import json
import logging
import hashlib
import base64
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# PDF and image processing
import fitz  # PyMuPDF for better PDF handling
import pdfplumber
from PIL import Image
import io

# OCR and Vision APIs
from google.cloud import vision
import requests
import pytesseract

# Vector embeddings
from sentence_transformers import SentenceTransformer
import numpy as np

# Database
from supabase import create_client
from dotenv import load_dotenv

# LLM for enhanced linking
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

class ChunkType(Enum):
    QUESTION = "question"
    SYLLABUS = "syllabus"
    MIXED = "mixed"

@dataclass
class DocumentChunk:
    content: str
    chunk_type: ChunkType
    subject: str
    year: Optional[int] = None
    paper: Optional[str] = None
    question_id: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    images: List[Dict] = None
    equations: List[Dict] = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.equations is None:
            self.equations = []

class IntelligentChunker:
    def __init__(self):
        # Environment variables
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.mathpix_app_id = os.getenv('MATHPIX_APP_ID')
        self.mathpix_app_key = os.getenv('MATHPIX_APP_KEY')
        self.google_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
        # Validate required environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        if self.google_credentials:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.google_credentials
        
        # Initialize clients
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize OpenAI client for LLM-based linking
        self.llm_client = None
        if self.openrouter_api_key:
            self.llm_client = OpenAI(
                base_url='https://openrouter.ai/api/v1',
                api_key=self.openrouter_api_key
            )
            logger.info("LLM client initialized for enhanced linking")
        
        # Initialize Vision API client if credentials available
        self.vision_client = None
        if self.google_credentials:
            try:
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Vision API: {e}")
        
        # Chunk size parameters (optimized for mathematical content)
        self.max_chunk_tokens = 500  # Conservative for complex math
        self.overlap_tokens = 50     # Small overlap to preserve context
        self.min_chunk_tokens = 100  # Ensure chunks have sufficient content
        
        # Mathematical content patterns
        self.math_patterns = [
            r'[+\-*/=^()∫∑√π∞≤≥≠±∂∇]',
            r'\$[^$]*\$',  # LaTeX inline
            r'\$\$[^$]*\$\$',  # LaTeX display
            r'\\[a-zA-Z]+\{[^}]*\}',  # LaTeX commands
            r'\d+/\d+',  # Fractions
            r'[a-zA-Z]\s*=\s*[^a-zA-Z\s]',  # Equations
            r'sin|cos|tan|log|ln|exp|lim|∀|∃',  # Math functions/symbols
        ]
        
        # Question identification patterns
        self.question_patterns = [
            r'^\s*\d+\.?\s*',  # 1. or 1
            r'^\s*\([a-z]+\)\s*',  # (a) (b) (c)
            r'^\s*[a-z]+\)\s*',  # a) b) c)
            r'^\s*[ivx]+\)\s*',  # i) ii) iii)
            r'Question\s+\d+',  # Question 1
            r'Problem\s+\d+',  # Problem 1
        ]
    
    def is_math_heavy(self, text: str) -> bool:
        """Determine if text contains significant mathematical content."""
        math_count = 0
        total_chars = len(text)
        
        if total_chars == 0:
            return False
        
        for pattern in self.math_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            math_count += len(matches)
        
        # Consider math-heavy if >5% of content is mathematical
        math_ratio = math_count / max(total_chars, 1)
        return math_ratio > 0.05 or math_count >= 10
    
    def extract_equations(self, text: str) -> List[Dict[str, str]]:
        """Extract mathematical equations from text."""
        equations = []
        
        # LaTeX equations
        latex_patterns = [
            r'\$\$([^$]*)\$\$',  # Display math
            r'\$([^$]*)\$',      # Inline math
        ]
        
        for pattern in latex_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                equations.append({
                    'latex': match.group(1).strip(),
                    'text': match.group(0),
                    'type': 'display' if pattern.startswith(r'\$\$') else 'inline'
                })
        
        return equations
    
    def ocr_with_vision(self, image_bytes: bytes) -> str:
        """Extract text using Google Vision API for poor quality scans."""
        if not self.vision_client:
            logger.warning("Google Vision API not available")
            return ""
        
        try:
            image = vision.Image(content=image_bytes)
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            if response.full_text_annotation:
                return response.full_text_annotation.text
            else:
                logger.warning("No text detected by Vision API")
                return ""
                
        except Exception as e:
            logger.error(f"Google Vision OCR failed: {e}")
            return ""
    
    def ocr_with_mathpix(self, image_bytes: bytes) -> str:
        """Extract text with math notation using Mathpix API."""
        if not (self.mathpix_app_id and self.mathpix_app_key):
            logger.warning("Mathpix credentials not available")
            return ""
        
        try:
            response = requests.post(
                'https://api.mathpix.com/v3/text',
                files={'file': ('image.jpg', image_bytes, 'image/jpeg')},
                headers={
                    'app_id': self.mathpix_app_id,
                    'app_key': self.mathpix_app_key
                },
                data={
                    'options_json': json.dumps({
                        'math_inline_delimiters': ['$', '$'],
                        'math_display_delimiters': ['$$', '$$'],
                        'rm_spaces': True,
                        'rm_fonts': True,
                        'format': 'latex',
                    })
                },
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                return result.get('text', '')
            else:
                logger.error(f"Mathpix API error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Mathpix OCR failed: {e}")
            return ""
    
    def ocr_with_tesseract(self, image_bytes: bytes) -> str:
        """Extract text using Tesseract OCR as fallback."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use Tesseract to extract text
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            if text.strip():
                logger.info("Using Tesseract OCR for text extraction")
                return text.strip()
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""
    
    def smart_ocr(self, image_bytes: bytes) -> Tuple[str, bool]:
        """
        Intelligently choose OCR method based on content analysis.
        Returns (text, is_math_heavy)
        """
        # Try Google Vision first for initial analysis
        vision_text = self.ocr_with_vision(image_bytes)
        is_math = self.is_math_heavy(vision_text)
        
        # If Google Vision worked, continue with logic
        if vision_text.strip():
            if is_math and self.mathpix_app_id and self.mathpix_app_key:
                # Use Mathpix for math-heavy content
                mathpix_text = self.ocr_with_mathpix(image_bytes)
                if mathpix_text.strip():
                    logger.info("Using Mathpix OCR for math-heavy content")
                    return mathpix_text, True
                else:
                    logger.warning("Mathpix failed, using Google Vision result")
                    return vision_text, is_math
            else:
                return vision_text, is_math
        else:
            # Google Vision failed (billing disabled), try Tesseract as fallback
            logger.info("Google Vision unavailable, trying Tesseract OCR")
            tesseract_text = self.ocr_with_tesseract(image_bytes)
            
            if tesseract_text.strip():
                is_math = self.is_math_heavy(tesseract_text)
                return tesseract_text, is_math
            else:
                logger.warning("All OCR methods failed")
                return "", False
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract images from PDF pages for OCR processing with parallel processing."""
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            # Collect all image data first
            image_tasks = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        image_tasks.append({
                            'page': page_num + 1,
                            'index': img_index,
                            'data': img_data
                        })
                    
                    pix = None  # Clean up
            
            doc.close()
            
            # Process OCR in parallel if we have images
            if image_tasks:
                images = self._process_images_parallel(image_tasks)
            
        except Exception as e:
            logger.error(f"Failed to extract images from PDF: {e}")
        
        return images

    def _process_images_parallel(self, image_tasks: List[Dict], max_workers: int = 3) -> List[Dict]:
        """Process OCR for multiple images in parallel."""
        logger.info(f"Processing OCR for {len(image_tasks)} images using {max_workers} workers...")
        
        def process_single_image(task):
            try:
                ocr_text, is_math = self.smart_ocr(task['data'])
                if ocr_text.strip():
                    return {
                        'page': task['page'],
                        'index': task['index'],
                        'base64_data': base64.b64encode(task['data']).decode(),
                        'ocr_text': ocr_text,
                        'is_math_heavy': is_math,
                        'extension': 'png'
                    }
            except Exception as e:
                logger.warning(f"OCR failed for image on page {task['page']}: {e}")
            return None
        
        processed_images = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single_image, task) for task in image_tasks]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        processed_images.append(result)
                except Exception as e:
                    logger.warning(f"Image processing failed: {e}")
        
        logger.info(f"Successfully processed {len(processed_images)} images")
        return processed_images

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber with parallel page processing."""
        logger.info("Extracting text from PDF pages...")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # For small PDFs, process sequentially
                if len(pdf.pages) <= 5:
                    full_text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        full_text += page_text + "\n"
                    return full_text
                
                # For larger PDFs, use parallel processing
                def extract_page_text(page):
                    try:
                        return page.extract_text() or ""
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page: {e}")
                        return ""
                
                with ThreadPoolExecutor(max_workers=4) as executor:
                    page_texts = list(executor.map(extract_page_text, pdf.pages))
                
                return "\n".join(page_texts)
                
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""
    
    def identify_questions(self, text: str) -> List[Tuple[int, str]]:
        """Identify question boundaries in text."""
        questions = []
        lines = text.split('\n')
        current_question = []
        current_id = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new question
            for pattern in self.question_patterns:
                match = re.match(pattern, line)
                if match:
                    # Save previous question if exists
                    if current_question and current_id:
                        questions.append((current_id, '\n'.join(current_question)))
                    
                    # Start new question
                    current_id = line[:20]  # Use first 20 chars as ID
                    current_question = [line]
                    break
            else:
                # Continue current question
                if current_question:
                    current_question.append(line)
        
        # Add final question
        if current_question and current_id:
            questions.append((current_id, '\n'.join(current_question)))
        
        return questions
    
    def semantic_chunk_text(self, text: str, chunk_type: ChunkType) -> List[str]:
        """Create semantic chunks optimized for mathematical content."""
        # For questions, try to keep each question as a single chunk
        if chunk_type == ChunkType.QUESTION:
            questions = self.identify_questions(text)
            if questions:
                return [q[1] for q in questions]
        
        # For syllabus or when questions can't be identified, use sentence-based chunking
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            sentence_tokens = len(sentence) // 4
            
            if current_length + sentence_tokens > self.max_chunk_tokens and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Filter out chunks that are too small
        chunks = [chunk for chunk in chunks if len(chunk) // 4 >= self.min_chunk_tokens]
        
        return chunks
    
    def extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename."""
        metadata = {
            'subject': 'Unknown',
            'year': None,
            'paper': None,
            'is_syllabus': False
        }
        
        filename_lower = filename.lower()
        
        # Check if syllabus
        syllabus_patterns = [
            'syllabus', 'curriculum', 'cape pure mathematics (1)', 
            'cape applied mathematics (1)', 'cape physics (1)', 'cape chemistry (1)',
            'specification', 'outline', 'course description'
        ]
        
        for pattern in syllabus_patterns:
            if pattern in filename_lower:
                metadata['is_syllabus'] = True
                break
        
        # Extract subject
        subject_patterns = {
            r'pure\s*math|pure\s*mathematics': 'Pure Mathematics',
            r'applied\s*math|applied\s*mathematics': 'Applied Mathematics',
            r'physics': 'Physics',
            r'chemistry': 'Chemistry',
        }
        
        for pattern, subject in subject_patterns.items():
            if re.search(pattern, filename_lower):
                metadata['subject'] = subject
                break
        
        # Extract year
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            metadata['year'] = int(year_match.group(1))
        
        # Extract paper info
        paper_match = re.search(r'(u\d+\s*p\d+|unit\s*\d+\s*paper\s*\d+|paper\s*\d+)', filename_lower)
        if paper_match:
            metadata['paper'] = paper_match.group(1).upper()
        
        # Enhanced validation and error checking
        self._validate_metadata(metadata, filename)
        
        return metadata

    def _validate_metadata(self, metadata: Dict[str, Any], filename: str) -> None:
        """Validate extracted metadata and log warnings for potential issues."""
        
        # Check for required fields based on classification
        if metadata['is_syllabus']:
            if metadata['subject'] == 'Unknown':
                logger.error(f"VALIDATION ERROR: Syllabus document missing subject: {filename}")
            if metadata['year'] is not None:
                logger.warning(f"VALIDATION WARNING: Syllabus document has year (unusual): {filename}")
        else:
            # Question document validations
            if metadata['subject'] == 'Unknown':
                logger.error(f"VALIDATION ERROR: Question document missing subject: {filename}")
            if metadata['year'] is None and not any(word in filename.lower() for word in ['specimen', 'sample']):
                logger.warning(f"VALIDATION WARNING: Question document missing year: {filename}")
            if metadata['paper'] is None:
                logger.warning(f"VALIDATION WARNING: Question document missing paper info: {filename}")
        
        # Log classification decision
        doc_type = "SYLLABUS" if metadata['is_syllabus'] else "QUESTION"
        logger.info(f"Classified as {doc_type}: {filename}")
        logger.info(f"Final metadata: subject={metadata['subject']}, year={metadata['year']}, paper={metadata['paper']}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            return []
    
    def process_pdf(self, pdf_path: str) -> List[DocumentChunk]:
        """Process a PDF file and create optimal chunks."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract metadata from filename
        filename = Path(pdf_path).name
        metadata = self.extract_metadata_from_filename(filename)
        
        chunks = []
        
        try:
            # Extract text and images in parallel
            logger.info("Starting parallel text and image extraction...")
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit text extraction task
                text_future = executor.submit(self._extract_text_from_pdf, pdf_path)
                # Submit image extraction task  
                images_future = executor.submit(self.extract_images_from_pdf, pdf_path)
                
                # Get results
                full_text = text_future.result()
                images = images_future.result()
            
            # Add OCR text to main content
            ocr_text = ""
            for img in images:
                if img.get('ocr_text'):
                    ocr_text += f"\n[Image OCR]: {img['ocr_text']}\n"
            
            combined_text = full_text + ocr_text
            
            if not combined_text.strip():
                logger.warning(f"No text extracted from {pdf_path}")
                return chunks
            
            # Determine chunk type
            chunk_type = ChunkType.SYLLABUS if metadata['is_syllabus'] else ChunkType.QUESTION
            
            # Create semantic chunks
            text_chunks = self.semantic_chunk_text(combined_text, chunk_type)
            
            # Create DocumentChunk objects
            for i, chunk_text in enumerate(text_chunks):
                # Extract equations from chunk
                equations = self.extract_equations(chunk_text)
                
                # Create chunk object
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_type=chunk_type,
                    subject=metadata['subject'],
                    year=metadata['year'],
                    paper=metadata['paper'],
                    images=images if i == 0 else [],  # Attach images to first chunk
                    equations=equations,
                    confidence_score=0.9  # High confidence for PDF extraction
                )
                
                # Try to identify question ID for question chunks
                if chunk_type == ChunkType.QUESTION:
                    for pattern in self.question_patterns:
                        match = re.search(pattern, chunk_text)
                        if match:
                            chunk.question_id = match.group(0).strip()
                            break
                
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from {pdf_path}")
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
        
        return chunks
    
    def get_syllabus_chunks(self, subject: str) -> List[Dict]:
        """Retrieve all syllabus chunks for a subject from database."""
        try:
            response = self.supabase.table('syllabus_chunks').select('*').eq('subject', subject).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to retrieve syllabus chunks: {e}")
            return []
    
    def analyze_question_with_llm(self, question_content: str, subject: str) -> Dict[str, Any]:
        """Use LLM to analyze question and extract educational metadata."""
        if not self.llm_client:
            logger.warning("LLM client not available for question analysis")
            return {}
        
        try:
            prompt = f"""Analyze this CAPE {subject} question and extract educational metadata:

QUESTION: {question_content[:1000]}...

Please provide a JSON response with the following fields:
1. "topics": List of main mathematical/scientific topics covered (e.g., ["Differentiation", "Polynomial Functions"])
2. "difficulty_level": One of ["Basic", "Intermediate", "Advanced"] 
3. "key_concepts": List of specific concepts tested (e.g., ["Power Rule", "Chain Rule"])
4. "question_type": Type of question (e.g., "Problem Solving", "Proof", "Calculation")
5. "syllabus_keywords": Keywords that would help match to syllabus objectives

Respond with valid JSON only."""

            response = self.llm_client.chat.completions.create(
                model='openai/gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': f'You are an expert CAPE {subject} curriculum analyst. Analyze questions and provide structured educational metadata.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse JSON response with robust error handling
            import json
            response_content = response.choices[0].message.content.strip()
            logger.debug(f"Raw LLM response: {response_content[:200]}...")
            
            try:
                # Try to parse as JSON
                analysis = json.loads(response_content)
                logger.debug(f"LLM analysis: {analysis}")
                return analysis
            except json.JSONDecodeError as json_error:
                logger.warning(f"Failed to parse LLM JSON response: {json_error}")
                logger.warning(f"Response content: {response_content[:500]}...")
                
                # Try to extract JSON from markdown or mixed content
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group())
                        logger.info("Successfully extracted JSON from mixed content")
                        return analysis
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse extracted JSON")
                
                # Return empty dict if all parsing fails
                return {}
            
        except Exception as e:
            logger.error(f"LLM question analysis failed: {e}")
            return {}
    
    def find_matching_syllabus_with_llm(self, question_analysis: Dict, syllabus_chunks: List[Dict], subject: str) -> List[Dict]:
        """Use LLM to match questions to syllabus objectives with confidence scores."""
        if not self.llm_client or not question_analysis or not syllabus_chunks:
            return []
        
        try:
            # Create a simplified syllabus context for LLM
            syllabus_context = ""
            for i, syllabus in enumerate(syllabus_chunks[:20]):  # Limit to top 20 for context size
                syllabus_context += f"ID:{syllabus['id']} | {syllabus['topic_title']} | {syllabus['chunk_text'][:200]}...\n"
            
            prompt = f"""Match this CAPE {subject} question to relevant syllabus objectives:

QUESTION ANALYSIS:
- Topics: {question_analysis.get('topics', [])}
- Key Concepts: {question_analysis.get('key_concepts', [])}  
- Keywords: {question_analysis.get('syllabus_keywords', [])}
- Difficulty: {question_analysis.get('difficulty_level', 'Unknown')}

AVAILABLE SYLLABUS OBJECTIVES:
{syllabus_context}

Provide a JSON array of matches with confidence scores:
[
  {{"syllabus_id": 123, "confidence": 0.95, "reasoning": "Direct match for differentiation concepts"}},
  {{"syllabus_id": 456, "confidence": 0.75, "reasoning": "Related to polynomial functions"}}
]

Only include matches with confidence >= 0.6. Respond with valid JSON only."""

            response = self.llm_client.chat.completions.create(
                model='openai/gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': f'You are an expert CAPE {subject} curriculum specialist. Match questions to syllabus objectives with high accuracy.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            # Parse JSON response
            import json
            matches = json.loads(response.choices[0].message.content.strip())
            logger.debug(f"LLM syllabus matches: {matches}")
            return matches
            
        except Exception as e:
            logger.error(f"LLM syllabus matching failed: {e}")
            return []
    
    def create_enhanced_topic_mappings(self, question_chunk_id: int, question_content: str, subject: str) -> List[Dict]:
        """Create enhanced topic mappings using LLM analysis."""
        if not self.llm_client:
            logger.warning("LLM not available, using basic keyword matching")
            return self.create_basic_topic_mappings(question_chunk_id, question_content, subject)
        
        try:
            # Step 1: Get syllabus chunks for the subject
            syllabus_chunks = self.get_syllabus_chunks(subject)
            if not syllabus_chunks:
                logger.warning(f"No syllabus chunks found for {subject}")
                return []
            
            # Step 2: Analyze question with LLM
            question_analysis = self.analyze_question_with_llm(question_content, subject)
            if not question_analysis:
                logger.warning("LLM analysis failed, falling back to basic matching")
                return self.create_basic_topic_mappings(question_chunk_id, question_content, subject)
            
            # Step 3: Find matching syllabus objectives with LLM
            llm_matches = self.find_matching_syllabus_with_llm(question_analysis, syllabus_chunks, subject)
            
            # Step 4: Create mapping objects
            mappings = []
            for match in llm_matches:
                if match.get('confidence', 0) >= 0.6:  # Only high-confidence matches
                    mapping = {
                        'question_id': question_chunk_id,
                        'topic_id': match['syllabus_id'],
                        'confidence_score': match['confidence'],
                        'mapping_type': 'llm_enhanced',
                        'reasoning': match.get('reasoning', ''),
                        'question_analysis': question_analysis
                    }
                    mappings.append(mapping)
            
            logger.info(f"Created {len(mappings)} LLM-enhanced topic mappings")
            return mappings
            
        except Exception as e:
            logger.error(f"Enhanced topic mapping failed: {e}")
            return self.create_basic_topic_mappings(question_chunk_id, question_content, subject)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract mathematical and subject-specific keywords from text."""
        # Common mathematical and scientific terms
        important_terms = [
            'derivative', 'integral', 'limit', 'function', 'equation', 'matrix', 
            'vector', 'probability', 'statistics', 'geometry', 'algebra', 'calculus',
            'differentiate', 'integrate', 'solve', 'find', 'calculate', 'prove',
            'force', 'velocity', 'acceleration', 'energy', 'momentum', 'frequency',
            'reaction', 'compound', 'element', 'molecule', 'atom', 'bond',
            'polynomial', 'quadratic', 'logarithmic', 'exponential', 'trigonometric',
            'factorization', 'roots', 'coefficients', 'continuity'
        ]
        
        # Mathematical term synonyms/related words
        term_groups = {
            'differentiation': ['derivative', 'differentiate', 'differentiation'],
            'integration': ['integral', 'integrate', 'integration'],
            'quadratic': ['quadratic', 'parabola', 'square'],
            'polynomial': ['polynomial', 'monomial', 'binomial'],
            'function': ['function', 'functions'],
            'equation': ['equation', 'equations'],
            'chemical': ['chemical', 'chemistry', 'reaction', 'reactions']
        }
        
        # Extract words that might be important
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter for important terms and normalize related terms
        keywords = []
        for word in words:
            if word in important_terms:
                # Check if this word belongs to a term group
                normalized_word = word
                for group_key, group_terms in term_groups.items():
                    if word in group_terms:
                        normalized_word = group_key
                        break
                keywords.append(normalized_word)
            elif len(word) > 6:
                keywords.append(word)
        
        # Add mathematical symbols and expressions
        math_symbols = re.findall(r'[+\-*/=^()∫∑√π∞≤≥≠±∂∇]|\d+', text)
        keywords.extend(math_symbols)
        
        return list(set(keywords))  # Remove duplicates

    def create_basic_topic_mappings(self, question_chunk_id: int, question_content: str, subject: str) -> List[Dict]:
        """Fallback: Create basic topic mappings using keyword/semantic matching."""
        try:
            # Get syllabus chunks
            syllabus_chunks = self.get_syllabus_chunks(subject)
            if not syllabus_chunks:
                return []
            
            # Simple keyword-based matching
            question_keywords = set(self.extract_keywords(question_content))
            mappings = []
            
            for syllabus in syllabus_chunks:
                syllabus_text = f"{syllabus['topic_title']} {syllabus['chunk_text']}"
                syllabus_keywords = set(self.extract_keywords(syllabus_text))
                
                # Calculate keyword overlap
                common_keywords = question_keywords.intersection(syllabus_keywords)
                if len(common_keywords) > 0:
                    confidence = min(len(common_keywords) / max(len(question_keywords), 1), 0.9)
                    
                    if confidence >= 0.05:  # Very low threshold for basic matching
                        mapping = {
                            'question_id': question_chunk_id,
                            'topic_id': syllabus['id'],
                            'confidence_score': confidence,
                            'mapping_type': 'keyword_based',
                            'common_keywords': list(common_keywords)
                        }
                        mappings.append(mapping)
            
            # Sort by confidence and limit results
            mappings.sort(key=lambda x: x['confidence_score'], reverse=True)
            return mappings[:5]  # Top 5 matches
            
        except Exception as e:
            logger.error(f"Basic topic mapping failed: {e}")
            return []
    
    def validate_mapping_quality(self, mappings: List[Dict]) -> List[Dict]:
        """Validate and enhance mapping quality with additional confidence scoring."""
        validated_mappings = []
        
        for mapping in mappings:
            try:
                # Base confidence from initial analysis
                base_confidence = mapping.get('confidence_score', 0.5)
                
                # Additional validation factors
                confidence_adjustments = 0.0
                
                # Boost confidence for LLM-enhanced mappings
                if mapping.get('mapping_type') == 'llm_enhanced':
                    confidence_adjustments += 0.1
                
                # Boost confidence if reasoning is provided
                if mapping.get('reasoning') and len(mapping['reasoning']) > 20:
                    confidence_adjustments += 0.05
                
                # Reduce confidence for keyword-only mappings with few matches (but less harsh)
                if (mapping.get('mapping_type') == 'keyword_based' and 
                    len(mapping.get('common_keywords', [])) < 2):
                    confidence_adjustments -= 0.05  # Less harsh penalty
                
                # Calculate final confidence (cap at 0.95 max)
                final_confidence = min(base_confidence + confidence_adjustments, 0.95)
                final_confidence = max(final_confidence, 0.1)  # Minimum 0.1
                
                # Only include mappings above minimum threshold (lowered)
                if final_confidence >= 0.1:
                    mapping['confidence_score'] = final_confidence
                    mapping['validation_notes'] = f"Adjusted confidence by {confidence_adjustments:+.2f}"
                    validated_mappings.append(mapping)
                else:
                    logger.debug(f"Filtered out low-confidence mapping (score: {final_confidence:.2f})")
                    
            except Exception as e:
                logger.warning(f"Error validating mapping: {e}")
                # Include original mapping if validation fails
                if mapping.get('confidence_score', 0) >= 0.4:
                    validated_mappings.append(mapping)
        
        # Sort by confidence and return top mappings
        validated_mappings.sort(key=lambda x: x['confidence_score'], reverse=True)
        return validated_mappings[:10]  # Top 10 highest confidence mappings

    def store_topic_mappings(self, mappings: List[Dict]) -> bool:
        """Store validated topic mappings in the database."""
        if not mappings:
            return True
        
        try:
            # Validate mapping quality first
            validated_mappings = self.validate_mapping_quality(mappings)
            
            if not validated_mappings:
                logger.warning("No mappings passed validation")
                return False
            
            # Prepare data for insertion (remove analysis data for storage)
            db_mappings = []
            for mapping in validated_mappings:
                db_mapping = {
                    'question_id': mapping['question_id'],
                    'topic_id': mapping['topic_id'],
                    'confidence_score': mapping['confidence_score'],
                    'mapping_type': mapping['mapping_type']
                }
                db_mappings.append(db_mapping)
            
            # Insert into database
            result = self.supabase.table('question_topic_mappings').insert(db_mappings).execute()
            
            if result.data:
                logger.info(f"Successfully stored {len(db_mappings)} validated topic mappings")
                return True
            else:
                logger.warning("No data returned from topic mappings insertion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to store topic mappings: {e}")
            return False
    
    def upload_chunks_to_supabase(self, chunks: List[DocumentChunk]) -> bool:
        """Upload chunks to Supabase database with automatic topic mapping using batch processing."""
        try:
            if not chunks:
                return True
            
            logger.info(f"Starting batch upload of {len(chunks)} chunks...")
            
            # Separate chunks by type
            question_chunks = [c for c in chunks if c.chunk_type == ChunkType.QUESTION]
            syllabus_chunks = [c for c in chunks if c.chunk_type == ChunkType.SYLLABUS]
            
            total_uploaded = 0
            
            # Process question chunks in batches
            if question_chunks:
                total_uploaded += self._upload_question_chunks_batch(question_chunks)
            
            # Process syllabus chunks in batches  
            if syllabus_chunks:
                total_uploaded += self._upload_syllabus_chunks_batch(syllabus_chunks)
            
            logger.info(f"Successfully uploaded {total_uploaded} chunks to Supabase")
            return total_uploaded > 0
            
        except Exception as e:
            logger.error(f"Failed to upload chunks to Supabase: {e}")
            return False

    def _generate_embeddings_parallel(self, contents: List[str], max_workers: int = 4) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple chunks in parallel."""
        logger.info(f"Generating embeddings for {len(contents)} chunks using {max_workers} workers...")
        
        embeddings = [None] * len(contents)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.create_embedding, content): i 
                for i, content in enumerate(contents)
            }
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    embedding = future.result()
                    embeddings[index] = embedding
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {index}: {e}")
                    embeddings[index] = None
        
        successful = sum(1 for e in embeddings if e is not None)
        logger.info(f"Successfully generated {successful}/{len(contents)} embeddings")
        return embeddings

    def _upload_question_chunks_batch(self, chunks: List[DocumentChunk], batch_size: int = 10) -> int:
        """Upload question chunks in batches."""
        logger.info(f"Uploading {len(chunks)} question chunks in batches of {batch_size}")
        
        # Generate all embeddings in parallel first
        contents = [chunk.content for chunk in chunks]
        embeddings = self._generate_embeddings_parallel(contents)
        
        total_uploaded = 0
        
        # Process in batches to avoid database timeouts
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            
            # Prepare batch data
            batch_data = []
            valid_chunks = []
            
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                if embedding is None:
                    logger.warning(f"Skipping chunk due to embedding failure")
                    continue
                    
                data = {
                    'content': chunk.content,
                    'embedding': embedding,
                    'subject': chunk.subject,
                    'year': chunk.year,
                    'paper': chunk.paper,
                    'question_id': chunk.question_id,
                    'topic': chunk.topic,
                    'sub_topic': chunk.sub_topic,
                    'images': chunk.images,
                    'equations': chunk.equations,
                    'is_math_heavy': self.is_math_heavy(chunk.content),
                    'confidence_score': chunk.confidence_score
                }
                batch_data.append(data)
                valid_chunks.append(chunk)
            
            if not batch_data:
                continue
                
            try:
                # Batch insert
                logger.info(f"Inserting batch {i//batch_size + 1} with {len(batch_data)} chunks...")
                result = self.supabase.table('question_chunks').insert(batch_data).execute()
                
                if result.data and len(result.data) > 0:
                    batch_uploaded = len(result.data)
                    total_uploaded += batch_uploaded
                    logger.info(f"Successfully uploaded batch: {batch_uploaded} chunks")
                    
                    # Create topic mappings for uploaded chunks (can be done in background)
                    self._create_topic_mappings_async(result.data, valid_chunks)
                    
                else:
                    logger.warning(f"No data returned from batch insertion")
                    
            except Exception as e:
                logger.error(f"Failed to upload batch {i//batch_size + 1}: {e}")
                # Continue with next batch
                continue
                
            # Small delay between batches to avoid overwhelming database
            time.sleep(0.5)
        
        return total_uploaded

    def _upload_syllabus_chunks_batch(self, chunks: List[DocumentChunk], batch_size: int = 10) -> int:
        """Upload syllabus chunks in batches."""
        logger.info(f"Uploading {len(chunks)} syllabus chunks in batches of {batch_size}")
        
        # Generate all embeddings in parallel first
        contents = [chunk.content for chunk in chunks]
        embeddings = self._generate_embeddings_parallel(contents)
        
        total_uploaded = 0
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            
            # Prepare batch data
            batch_data = []
            
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                if embedding is None:
                    logger.warning(f"Skipping chunk due to embedding failure")
                    continue
                    
                data = {
                    'subject': chunk.subject,
                    'topic_title': chunk.topic or 'General',
                    'chunk_text': chunk.content,
                    'embedding': embedding,
                    'module': chunk.paper or 'Unknown'
                }
                batch_data.append(data)
            
            if not batch_data:
                continue
                
            try:
                # Batch insert
                logger.info(f"Inserting syllabus batch {i//batch_size + 1} with {len(batch_data)} chunks...")
                result = self.supabase.table('syllabus_chunks').insert(batch_data).execute()
                
                if result.data and len(result.data) > 0:
                    batch_uploaded = len(result.data)
                    total_uploaded += batch_uploaded
                    logger.info(f"Successfully uploaded syllabus batch: {batch_uploaded} chunks")
                else:
                    logger.warning(f"No data returned from syllabus batch insertion")
                    
            except Exception as e:
                logger.error(f"Failed to upload syllabus batch {i//batch_size + 1}: {e}")
                continue
                
            time.sleep(0.5)
        
        return total_uploaded

    def _create_topic_mappings_async(self, uploaded_chunks: List[Dict], original_chunks: List[DocumentChunk]):
        """Create topic mappings asynchronously after chunks are uploaded."""
        try:
            logger.info(f"Creating topic mappings for {len(uploaded_chunks)} chunks...")
            
            def create_mapping_for_chunk(chunk_data, original_chunk):
                try:
                    chunk_id = chunk_data['id']
                    mappings = self.create_enhanced_topic_mappings(
                        chunk_id, original_chunk.content, original_chunk.subject
                    )
                    if mappings:
                        success = self.store_topic_mappings(mappings)
                        return len(mappings) if success else 0
                    return 0
                except Exception as e:
                    logger.warning(f"Topic mapping failed for chunk {chunk_data.get('id')}: {e}")
                    return 0
            
            # Create mappings in parallel (with limited workers to avoid API limits)
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(create_mapping_for_chunk, chunk_data, original_chunk)
                    for chunk_data, original_chunk in zip(uploaded_chunks, original_chunks)
                ]
                
                total_mappings = 0
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        total_mappings += result
                    except Exception as e:
                        logger.warning(f"Mapping creation failed: {e}")
                
                logger.info(f"Created {total_mappings} topic mappings")
                
        except Exception as e:
            logger.error(f"Async topic mapping failed: {e}")

    def verify_upload_integrity(self, original_chunks: List[DocumentChunk], uploaded_count: int) -> bool:
        """Verify that chunks were uploaded correctly to the database."""
        logger.info(f"Verifying upload integrity: {len(original_chunks)} original vs {uploaded_count} uploaded")
        
        try:
            # Check total counts in database
            question_count = self.supabase.table('question_chunks').select('*', count='exact').execute().count
            syllabus_count = self.supabase.table('syllabus_chunks').select('*', count='exact').execute().count
            
            logger.info(f"Database totals: {question_count} questions, {syllabus_count} syllabus")
            
            # Separate original chunks by type
            original_questions = [c for c in original_chunks if c.chunk_type == ChunkType.QUESTION]
            original_syllabus = [c for c in original_chunks if c.chunk_type == ChunkType.SYLLABUS]
            
            logger.info(f"Original totals: {len(original_questions)} questions, {len(original_syllabus)} syllabus")
            
            # Verify counts match expectations
            success = True
            if len(original_questions) > 0:
                # Check if recent question chunks match
                recent_questions = self.supabase.table('question_chunks').select('*').order('id', desc=True).limit(len(original_questions)).execute()
                if len(recent_questions.data) < len(original_questions):
                    logger.error(f"INTEGRITY ERROR: Expected {len(original_questions)} question chunks, found {len(recent_questions.data)}")
                    success = False
            
            if len(original_syllabus) > 0:
                # Check if recent syllabus chunks match
                recent_syllabus = self.supabase.table('syllabus_chunks').select('*').order('id', desc=True).limit(len(original_syllabus)).execute()
                if len(recent_syllabus.data) < len(original_syllabus):
                    logger.error(f"INTEGRITY ERROR: Expected {len(original_syllabus)} syllabus chunks, found {len(recent_syllabus.data)}")
                    success = False
            
            if success:
                logger.info("✅ Upload integrity verification passed")
            else:
                logger.error("❌ Upload integrity verification failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False

    def generate_processing_report(self, pdf_path: str, chunks: List[DocumentChunk], uploaded_count: int) -> Dict[str, Any]:
        """Generate a comprehensive processing report."""
        filename = Path(pdf_path).name
        
        # Count chunks by type
        question_chunks = [c for c in chunks if c.chunk_type == ChunkType.QUESTION]
        syllabus_chunks = [c for c in chunks if c.chunk_type == ChunkType.SYLLABUS]
        
        # Calculate statistics
        total_content_length = sum(len(c.content) for c in chunks)
        avg_chunk_length = total_content_length / len(chunks) if chunks else 0
        
        report = {
            'filename': filename,
            'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_chunks_created': len(chunks),
            'question_chunks': len(question_chunks),
            'syllabus_chunks': len(syllabus_chunks),
            'chunks_uploaded': uploaded_count,
            'upload_success_rate': (uploaded_count / len(chunks)) * 100 if chunks else 0,
            'avg_chunk_length': int(avg_chunk_length),
            'total_content_chars': total_content_length,
            'has_images': any(len(c.images) > 0 for c in chunks),
            'has_equations': any(len(c.equations) > 0 for c in chunks),
            'subjects': list(set(c.subject for c in chunks)),
            'years': list(set(c.year for c in chunks if c.year)),
            'papers': list(set(c.paper for c in chunks if c.paper)),
        }
        
        # Log report
        logger.info("=" * 60)
        logger.info(f"PROCESSING REPORT: {filename}")
        logger.info("=" * 60)
        for key, value in report.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 60)
        
        return report
    
    def process_directory(self, directory_path: str) -> int:
        """Process all PDF files in a directory."""
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory not found: {directory_path}")
            return 0
        
        pdf_files = list(directory.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory_path}")
            return 0
        
        total_chunks = 0
        
        for pdf_file in pdf_files:
            try:
                chunks = self.process_pdf(str(pdf_file))
                if chunks:
                    success = self.upload_chunks_to_supabase(chunks)
                    if success:
                        total_chunks += len(chunks)
                        logger.info(f"Processed {pdf_file.name}: {len(chunks)} chunks")
                    else:
                        logger.error(f"Failed to upload chunks from {pdf_file.name}")
                else:
                    logger.warning(f"No chunks created from {pdf_file.name}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
        
        logger.info(f"Total chunks processed: {total_chunks}")
        return total_chunks

def main():
    """Main function to run the chunking script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Intelligent Document Chunker for CAPE GPT')
    parser.add_argument('input_path', help='Path to PDF file or directory containing PDFs')
    parser.add_argument('--subject', help='Override subject detection', 
                       choices=['Pure Mathematics', 'Applied Mathematics', 'Physics', 'Chemistry'])
    parser.add_argument('--year', type=int, help='Override year detection')
    parser.add_argument('--paper', help='Override paper detection')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize chunker
    try:
        chunker = IntelligentChunker()
    except Exception as e:
        logger.error(f"Failed to initialize chunker: {e}")
        return 1
    
    # Process input
    input_path = Path(args.input_path)
    
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        # Process single PDF
        chunks = chunker.process_pdf(str(input_path))
        if chunks:
            # Apply command line overrides
            for chunk in chunks:
                if args.subject:
                    chunk.subject = args.subject
                if args.year:
                    chunk.year = args.year
                if args.paper:
                    chunk.paper = args.paper
            
            success = chunker.upload_chunks_to_supabase(chunks)
            uploaded_count = len(chunks) if success else 0
            
            # Generate processing report with error checking
            report = chunker.generate_processing_report(str(input_path), chunks, uploaded_count)
            
            # Verify upload integrity with comprehensive checks
            if success:
                integrity_ok = chunker.verify_upload_integrity(chunks, uploaded_count)
                if integrity_ok:
                    print(f"✅ Successfully processed {len(chunks)} chunks from {input_path.name}")
                    print(f"📊 Upload success rate: {report['upload_success_rate']:.1f}%")
                else:
                    print(f"⚠️  Upload completed but integrity check failed for {input_path.name}")
                    return 1
            else:
                print(f"❌ Failed to upload chunks from {input_path.name}")
                return 1
        else:
            print(f"No chunks created from {input_path.name}")
            return 1
    
    elif input_path.is_dir():
        # Process directory
        total_chunks = chunker.process_directory(str(input_path))
        print(f"Processed {total_chunks} total chunks from directory")
    
    else:
        logger.error(f"Invalid input path: {input_path}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())