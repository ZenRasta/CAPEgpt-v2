"""
Unit tests for the questions API endpoints.
"""
import pytest
import tempfile
import os
import re
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import importlib
import sys
import os

# Provide required environment variables for importing main
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "test-key")
# Mock SentenceTransformer to avoid network calls during tests
with patch('sentence_transformers.SentenceTransformer') as MockST:
    MockST.return_value.encode.return_value = [0.0]
    sys.path.append(os.path.dirname(__file__))
    main = importlib.import_module('main')

app = main.app
MathpixResult = main.MathpixResult
should_use_svg = main.should_use_svg
classify_question = main.classify_question

client = TestClient(app)

@pytest.mark.skip("Upload tests require full Supabase setup")
class TestQuestionUpload:
    """Test the question upload endpoint."""
    
    def test_upload_valid_image(self):
        """Test uploading a valid image file."""
        # Create a test image file
        test_image_content = b"fake_image_data"
        
        with patch.object(main, 'supabase') as mock_supabase, \
             patch('asyncio.create_task') as mock_task:

            mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
            mock_supabase.storage.from_.return_value.create_signed_url.return_value = {
                'signedURL': 'https://example.com/signed-url'
            }
            mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
                {'id': 'test-question-id'}
            ]
            
            response = client.post(
                "/questions/upload",
                files={"file": ("test.png", test_image_content, "image/png")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == 'test-question-id'
            assert data['processing_status'] == 'pending'
            assert 'message' in data
            
            # Verify async task was created
            mock_task.assert_called_once()
    
    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type."""
        test_content = b"not_an_image"
        
        response = client.post(
            "/questions/upload",
            files={"file": ("test.txt", test_content, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "File must be an image or PDF" in response.json()['detail']
    
    def test_upload_large_file(self):
        """Test uploading a file that's too large."""
        # Create a large file content
        large_content = b"x" * (26 * 1024 * 1024)  # 26MB
        
        response = client.post(
            "/questions/upload",
            files={"file": ("large.png", large_content, "image/png")}
        )

        assert response.status_code == 400
        assert "File too large" in response.json()['detail']
    
    def test_upload_empty_file(self):
        """Test uploading an empty file."""
        response = client.post(
            "/questions/upload",
            files={"file": ("empty.png", b"", "image/png")}
        )
        
        assert response.status_code == 400
        assert "Empty file" in response.json()['detail']

class TestQuestionRetrieval:
    """Test the question retrieval endpoints."""
    
    def test_get_question_success(self):
        """Test successfully retrieving a question."""
        mock_question_data = {
            'id': 'test-id',
            'original_filename': 'test.png',
            'mathpix_markdown': '# Test Question',
            'mathpix_svg': '<svg>test</svg>',
            'uses_svg': True,
            'processing_status': 'completed',
            'subject': 'Pure Mathematics',
            'topics': ['algebra'],
            'created_at': '2024-01-01T00:00:00Z',
            'storage_path': 'mock-user-id/test.png'
        }
        
        with patch.object(main, 'supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_question_data]
            mock_supabase.storage.from_.return_value.create_signed_url.return_value = {
                'signedURL': 'https://example.com/signed-url'
            }
            
            response = client.get("/questions/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == 'test-id'
            assert data['original_filename'] == 'test.png'
            assert data['uses_svg'] == True
            assert data['processing_status'] == 'completed'
    
    def test_get_question_not_found(self):
        """Test retrieving a non-existent question."""
        with patch.object(main, 'supabase') as mock_supabase:
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            
            response = client.get("/questions/nonexistent-id")
            
            assert response.status_code == 404
            assert "Question not found" in response.json()['detail']
    
    def test_list_questions(self):
        """Test listing questions with pagination."""
        mock_questions = [
            {
                'id': 'test-id-1',
                'original_filename': 'test1.png',
                'mathpix_markdown': '# Test 1',
                'mathpix_svg': None,
                'uses_svg': False,
                'processing_status': 'completed',
                'subject': 'Pure Mathematics',
                'topics': ['algebra'],
                'created_at': '2024-01-01T00:00:00Z',
                'storage_path': 'mock-user-id/test1.png'
            }
        ]
        
        with patch.object(main, 'supabase') as mock_supabase:
            # Mock the chained query calls
            mock_query = MagicMock()
            mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query
            mock_query.execute.return_value.data = mock_questions
            mock_query.order.return_value.range.return_value.execute.return_value.data = mock_questions
            mock_supabase.storage.from_.return_value.create_signed_url.return_value = {
                'signedURL': 'https://example.com/signed-url'
            }
            
            response = client.get("/questions?limit=10&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['questions']) == 1
            assert data['total_count'] == 1
            assert data['questions'][0]['id'] == 'test-id-1'

class TestMathpixProcessing:
    """Test Mathpix processing functions."""
    
    def test_should_use_svg_low_confidence(self):
        """Test SVG decision with low confidence."""
        markdown = "Simple equation: $x = 1$"
        svg = "<svg>test</svg>"
        
        result = should_use_svg(markdown, 0.6, svg)
        assert result == True
    
    def test_should_use_svg_high_confidence(self):
        """Test SVG decision with high confidence."""
        markdown = "Simple equation: $x = 1$"
        svg = "<svg>test</svg>"
        
        result = should_use_svg(markdown, 0.9, svg)
        assert result == False
    
    def test_should_use_svg_with_fallback_indicators(self):
        """Test SVG decision with fallback indicators."""
        markdown = "Complex content with ![image](img1.png) and ![diagram](img2.png) and ![chart](img3.png)"
        svg = "<svg>test</svg>"
        
        result = should_use_svg(markdown, 0.8, svg)
        assert result == True
    
    def test_should_use_svg_diagram_content(self):
        """Test SVG decision with diagram content."""
        markdown = "Please refer to the diagram below showing the relationship..."
        svg = "<svg>test</svg>"
        
        result = should_use_svg(markdown, 0.8, svg)
        assert result == True
    
    def test_should_use_svg_short_content(self):
        """Test SVG decision with very short content."""
        markdown = "$E = mc^2$"
        svg = "<svg>test</svg>"
        
        result = should_use_svg(markdown, 0.8, svg)
        assert result == True
    
    def test_should_use_svg_no_svg_available(self):
        """Test SVG decision when no SVG is available."""
        markdown = "Simple equation: $x = 1$"
        svg = ""

        result = should_use_svg(markdown, 0.6, svg)
        assert result == False

    def test_should_use_svg_latex_heavy(self):
        """Ensure LaTeX-heavy content doesn't cause regex errors."""
        markdown = r"Evaluate the integral \int_0^1 \sqrt{x} dx"
        svg = "<svg>test</svg>"

        result = should_use_svg(markdown, 0.8, svg)
        assert result is True

    def test_should_use_svg_infty(self):
        """Ensure limit notation with \\infty doesn't raise regex errors."""
        markdown = r"Consider \lim_{x \\to \\infty} f(x)"
        svg = "<svg>test</svg>"

        try:
            result = should_use_svg(markdown, 0.8, svg)
        except re.error as e:
            pytest.fail(f"Regex error: {e}")
        assert result is True
class TestQuestionClassification:
    """Test question classification functions."""
    
    def test_classify_math_question(self):
        """Test classifying a math question."""
        content = "Find the derivative of f(x) = x^2 + 3x"
        filename = "Pure_Math_2023_Unit1_Paper2.pdf"
        
        result = classify_question(content, filename)
        
        assert result['subject'] == 'Pure Mathematics'
        assert result['estimated_year'] == 2023
        assert result['question_type'] == 'short_answer'
        assert 'calculus' in result['topics']
    
    def test_classify_physics_question(self):
        """Test classifying a physics question."""
        content = "Calculate the force required to accelerate a mass of 10kg"
        filename = "Physics_2022.pdf"
        
        result = classify_question(content, filename)
        
        assert result['subject'] == 'Physics'
        assert result['estimated_year'] == 2022
        assert result['question_type'] == 'short_answer'
    
    def test_classify_multiple_choice(self):
        """Test classifying a multiple choice question."""
        content = "Which of the following is correct? a) Option A b) Option B c) Option C d) Option D"
        filename = "test.png"
        
        result = classify_question(content, filename)
        
        assert result['question_type'] == 'multiple_choice'
    
    def test_classify_essay_question(self):
        """Test classifying an essay question."""
        long_content = "Discuss the implications of quantum mechanics in modern physics. " * 20
        filename = "essay_question.pdf"

        result = classify_question(long_content, filename)

        assert result['question_type'] == 'essay'

    def test_classify_question_with_latex(self):
        """Ensure classification handles LaTeX without regex errors."""
        content = r"Compute \int_0^1 \sqrt{x} dx"
        filename = "Pure_Math_2023_Unit1_Paper2.pdf"

        result = classify_question(content, filename)

        assert result['subject'] == 'Pure Mathematics'

    def test_classify_question_with_infty(self):
        """Ensure classification handles expressions with \\infty."""
        content = r"Find the limit as x \\to \\infty of \frac{1}{x}"
        filename = "Pure_Math_2023_Unit1_Paper2.pdf"

        try:
            result = classify_question(content, filename)
        except re.error as e:
            pytest.fail(f"Regex error: {e}")

        assert result['subject'] == 'Pure Mathematics'
class TestSearchEndpoint:
    """Test the search functionality."""
    
    def test_search_questions(self):
        """Test searching questions."""
        pytest.skip("Supabase RPC not available in test environment")

# Test fixtures and utilities
@pytest.fixture
def mock_mathpix_success():
    """Mock successful Mathpix response."""
    return {
        'text': 'Find the value of $x$ in the equation $2x + 3 = 7$',
        'confidence': 0.95
    }

@pytest.fixture
def mock_mathpix_failure():
    """Mock failed Mathpix response."""
    return Mock(ok=False, status_code=500)

@pytest.fixture
def sample_image_bytes():
    """Sample image bytes for testing."""
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'

if __name__ == "__main__":
    pytest.main([__file__])