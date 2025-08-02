# CAPE-GPT Questions Storage System

A comprehensive question storage and rendering system that preserves layout fidelity while remaining searchable and lightweight.

## Features

### 🔧 Backend Features
- **Enhanced Mathpix Integration**: Processes images with both Markdown and SVG outputs
- **Intelligent Rendering Decision**: Heuristic algorithm decides between SVG (pixel-perfect) vs Markdown/KaTeX (fast-loading)
- **Secure Storage**: Private Supabase storage with user-specific folders and signed URLs
- **Full-Text Search**: PostgreSQL tsvector-based search across content, filename, subject, and topics
- **Row-Level Security**: Users can only access their own questions
- **Async Processing**: Background processing with status tracking
- **Classification System**: Automatic subject, topic, and question-type detection

### 🎨 Frontend Features
- **QuestionViewer Component**: Dedicated viewer with original image reference
- **Dual Rendering Modes**: SVG for complex layouts, KaTeX for mathematical notation
- **Responsive Design**: Works on desktop and mobile
- **Processing Status**: Real-time status updates during Mathpix processing
- **Metadata Display**: Shows subject, topics, confidence scores, and timestamps

## Architecture

### Database Schema
```sql
-- questions table stores processed questions
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    mathpix_markdown TEXT,
    mathpix_svg TEXT,
    uses_svg BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending',
    search_vector TSVECTOR, -- Generated column for full-text search
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### API Endpoints
- `POST /questions/upload` - Upload and process question images/PDFs
- `GET /questions/{id}` - Retrieve a specific question
- `GET /questions` - List user's questions with pagination
- `GET /questions/search` - Full-text search across questions

### React Routes
- `/` - Main chat interface
- `/questions/:id` - Question viewer with original image and processed content

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Supabase account
- Mathpix API credentials (optional, falls back to Google Vision)

### Backend Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create `.env` file:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_service_key
   MATHPIX_APP_ID=your_mathpix_app_id
   MATHPIX_APP_KEY=your_mathpix_app_key
   OPENROUTER_API_KEY=your_openrouter_key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/google/credentials.json
   ```

3. **Run Database Migration**
   ```bash
   python scripts/run_migration.py
   ```

4. **Start Backend Server**
   ```bash
   cd backend
   python main.py
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Configuration**
   Create `.env` file:
   ```env
   VITE_API_URL=http://127.0.0.1:8000
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

## Usage

### Uploading Questions

1. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/questions/upload" \
        -F "file=@math_question.png"
   ```

2. **Via Frontend**: 
   - Use the existing file upload interface
   - Questions are automatically stored and processed

### Viewing Questions

Navigate to `/questions/{question-id}` to view a processed question with:
- Original image reference
- Processed content (SVG or Markdown/KaTeX)
- Question metadata and topics
- Processing confidence scores

### Searching Questions

```bash
curl "http://localhost:8000/questions/search?q=derivative&subject=Pure%20Mathematics"
```

## Processing Pipeline

1. **File Upload**: Image/PDF uploaded to Supabase storage
2. **Mathpix Processing**: Extract both Markdown and SVG
3. **Heuristic Decision**: Determine if SVG or Markdown rendering is better
4. **Classification**: Auto-detect subject, topics, and question type
5. **Storage**: Save all results with full-text search vector
6. **Availability**: Question ready for viewing and searching

## Heuristic Algorithm

The system uses intelligent heuristics to decide rendering mode:

```python
def should_use_svg(markdown: str, confidence: float, svg: str) -> bool:
    # Use SVG if confidence is low (complex layout)
    if confidence < 0.7:
        return True and bool(svg)
    
    # Use SVG if markdown contains fallback images
    fallback_count = count_fallback_indicators(markdown)
    if fallback_count >= 3:
        return True and bool(svg)
    
    # Use SVG for diagrammatic content
    if contains_diagram_indicators(markdown):
        return True and bool(svg)
    
    # Use SVG for very short content (likely single equation)
    if len(markdown.strip()) < 50 and svg:
        return True
    
    # Default to Markdown/KaTeX for performance
    return False
```

## Security

- **Row-Level Security**: Users can only access their own questions
- **Private Storage**: Files stored in user-specific folders
- **Signed URLs**: Temporary access to original files (24-hour expiry)
- **Input Validation**: File type, size, and content validation

## Testing

Run the test suite:

```bash
cd backend
pip install pytest pytest-asyncio
python -m pytest test_questions_api.py -v
```

Test coverage includes:
- File upload validation
- Mathpix processing pipeline
- Question classification
- Search functionality
- Error handling

## Performance Considerations

- **Async Processing**: Mathpix calls don't block the upload response
- **Batch Operations**: Efficient database operations
- **Caching**: Signed URLs cached for 24 hours
- **Lightweight Rendering**: KaTeX preferred over SVG when possible
- **Indexed Search**: Full-text search using PostgreSQL indexes

## Monitoring

Track processing status:
- `pending`: Just uploaded, queued for processing
- `processing`: Currently being processed by Mathpix
- `completed`: Successfully processed and ready
- `failed`: Processing failed, fallback OCR available

## Troubleshooting

### Common Issues

1. **Mathpix API Errors**
   - Check API credentials in `.env`
   - Verify API usage limits
   - System falls back to Google Vision automatically

2. **Storage Upload Failures**
   - Verify Supabase storage bucket exists
   - Check RLS policies are correctly configured
   - Ensure service key has storage permissions

3. **Search Not Working**
   - Run migration to create search functions
   - Check tsvector column is being populated
   - Verify PostgreSQL full-text search extensions

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is part of the CAPE-GPT system and follows the same licensing terms.

## Changelog

### v1.0.0 (Current)
- Initial release with complete question storage system
- Mathpix integration with SVG and Markdown support
- React QuestionViewer component
- Full-text search capabilities
- Row-level security implementation
- Comprehensive test suite