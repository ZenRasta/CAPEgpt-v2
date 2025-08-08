# CAPE GPT v2

CAPE GPT is an AI-powered web application that helps CAPE students by allowing them to snap photos of past-paper questions and get step-by-step solutions with exam insights.

## Features

- **Image Upload & OCR**: Upload images of CAPE questions and get text extraction using Google Vision API and Mathpix for math-heavy content
- **AI-Powered Solutions**: Get detailed step-by-step solutions using GPT-4 with proper mathematical notation
- **Exam Insights**: See which years similar questions appeared and probability of reappearance
- **Subject Support**: Pure Mathematics, Applied Mathematics, Physics, and Chemistry
- **Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile devices
- **Vector Search**: Find similar past questions using semantic search

## Architecture

```
┌────────────────┐        ┌───────────────────┐        ┌───────────────────┐
│ Frontend (React)│ ─────► │  FastAPI Backend  │ ─────► │  Supabase Vector  │
│  + Vite + Tailwind │     │  (Python 3.11)   │        │  DB (pgvector)    │
└────────────────┘        └───────────────────┘        └───────────────────┘
        ▲                        │  ▲  │                        ▲
        │                        │  │  │                        │
        │                        │  │  └─►External OCR APIs     │
        │                        │  │       • Google Vision     │
        │                        │  │       • Mathpix           │
        │                        │  │                          │
        │                        │  └────► OpenAI API          │
        │                        └──────── Vector Search ──────┘
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- OpenRouter API key (for OpenAI access)
- Google Cloud Vision API credentials (optional)
- Mathpix API credentials (optional)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/ZenRasta/CAPEgpt-v2.git
cd CAPEgpt-v2
```

### 2. Database Setup (Supabase)

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor in your Supabase dashboard
3. Run the SQL script from `supabase_db.sql` to create tables and functions
4. Enable the `pgvector` extension if not already enabled
5. Note your Supabase URL and anon key

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

#### Environment File Locations

The system automatically loads `.env` files in this order:
1. `backend/.env` (primary location)
2. `backups/.env` (fallback location)

Edit your `.env` file with these credentials:

```env
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENROUTER_API_KEY=your_openrouter_api_key

# OCR Services (at least one required for image processing)
MATHPIX_APP_ID=your_mathpix_app_id
MATHPIX_APP_KEY=your_mathpix_app_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
```

#### OCR Service Setup

**Mathpix (Recommended for Math)**
1. Sign up at [mathpix.com](https://mathpix.com/)
2. Get your App ID and App Key from the dashboard
3. Add to `.env` file

**Google Vision (PDF Support + Fallback)**
1. Create a Google Cloud project
2. Enable the Vision API
3. Create service account credentials
4. Download JSON credentials file
5. Set path in `GOOGLE_APPLICATION_CREDENTIALS`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

Edit `.env` if needed:

```env
VITE_API_URL=http://127.0.0.1:8000
```

### 5. Running the Application

#### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

The backend will run on `http://127.0.0.1:8000`

#### Check OCR Services

```bash
# Check OCR health status
curl http://localhost:8000/health/ocr
```

Expected response:
```json
{
  "ok": true,
  "provider_status": {
    "mathpix": {"available": true, "app_id_set": true, "app_key_set": true},
    "google_vision": {"available": true, "credentials_set": true}
  }
}
```

#### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:5173`

## API Endpoints

### Backend API

- `GET /` - Health check
- `GET /health/ocr` - OCR services health status
- `POST /upload` - Upload image and extract text via OCR
- `POST /questions/upload` - Upload question file for processing
- `GET /questions/{id}` - Get processed question by ID
- `POST /query` - Process question and get AI solution
- `GET /stats/topic` - Get topic statistics
- `GET /subjects` - Get available subjects
- `GET /popular-questions` - Get trending questions

### Example Usage

```javascript
// Upload image
const formData = new FormData();
formData.append('file', imageFile);
const response = await fetch('/upload', {
  method: 'POST',
  body: formData
});

// Query for solution
const response = await fetch('/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "Solve: x^2 + 5x + 6 = 0",
    subject: "Pure Mathematics"
  })
});
```

## Environment Variables

### Backend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Your Supabase anon key |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for OpenAI access |
| `MATHPIX_APP_ID` | No | Mathpix app ID for math OCR |
| `MATHPIX_APP_KEY` | No | Mathpix app key for math OCR |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to Google Cloud credentials JSON |

### Frontend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | No | Backend API URL (defaults to localhost:8000) |

## Database Schema

The application uses three main tables:

- **question_chunks**: Stores vectorized past-paper questions
- **syllabus_chunks**: Stores vectorized syllabus objectives  
- **topic_stats**: Materialized view for topic frequency statistics

See `supabase_db.sql` for the complete schema.

## Development

### Adding New Subjects

1. Update the `subjects` list in `frontend/src/App.jsx`
2. Update the `valid_subjects` list in `backend/main.py`
3. Add corresponding data to your database

### OCR Processing Flow

The system uses a **Mathpix-first strategy**:

1. **Mathpix** attempts OCR first (better for mathematical content)
2. **Google Vision** fallback if Mathpix fails or is not configured
3. **PDF Support**: Automatically converts PDF pages to images for Vision API

File support:
- **Images**: PNG, JPG, JPEG (up to 25MB)
- **PDFs**: Converted to images automatically (first 2 pages)

### Handling LaTeX OCR – Why We Escape

When processing mathematical content through OCR, the extracted text often contains LaTeX symbols and commands like `\int`, `\sum`, `\frac{}{}`, etc. These symbols have special meaning in regular expressions and can cause parsing errors if used directly in regex patterns.

**The Problem**: Raw OCR text like `\int_0^\infty x dx` contains backslashes that are invalid regex escape sequences.

**The Solution**: The system includes a `escapeRegex()` utility that safely escapes special regex characters:

```javascript
import { escapeRegex } from '../util/regex';

// Safe regex construction from OCR text
const safePattern = escapeRegex(rawOCRText);
const latexRegex = new RegExp(safePattern, "i");
```

**Error Handling**: If regex construction fails, the system shows user-friendly error messages instead of crashing.

### Styling

The frontend uses Tailwind CSS for styling. Modify `frontend/src/index.css` for custom styles.

## Deployment

### Backend (Fly.io/Railway)

1. Update CORS origins in `backend/main.py`
2. Set environment variables in your deployment platform
3. Deploy using Docker or direct Python deployment

### Frontend (Vercel/Netlify)

1. Update `VITE_API_URL` to your deployed backend URL
2. Build and deploy: `npm run build`

### Database

Supabase handles the database hosting. Ensure your production environment variables point to your Supabase project.

## Troubleshooting

### OCR Issues

1. **Check service status**:
   ```bash
   curl http://localhost:8000/health/ocr
   ```

2. **Common problems**:
   - **Mathpix not working**: Verify `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` are correct
   - **Google Vision errors**: Check `GOOGLE_APPLICATION_CREDENTIALS` path is valid and accessible
   - **PDF processing fails**: Ensure PyMuPDF is installed (`pip install PyMuPDF`)

3. **Environment loading**:
   - Check startup logs for: `"Environment loaded from: /path/to/.env"`
   - System tries `backend/.env` first, then `backups/.env`

### Upload Issues

- **File too large**: Maximum 25MB for uploads
- **Unsupported format**: Only PNG, JPG, PDF are supported  
- **Processing timeout**: Large files may take 1-2 minutes to process
- **No text extracted**: Try a clearer image or check OCR service status

### Frontend Errors

- **CORS errors**: Ensure backend URL is correct in `VITE_API_URL`
- **Network errors**: Check that backend is running on the correct port
- **OCR configuration hints**: The UI shows helpful tips for common OCR setup issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in the `app_context` file for detailed specifications

## Roadmap

- [ ] User authentication and session management
- [ ] Question history and favorites
- [ ] Offline mode support
- [ ] Additional subject support
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
