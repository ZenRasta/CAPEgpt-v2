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

Edit `.env` with your credentials:

```env
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional (for better OCR)
MATHPIX_APP_ID=your_mathpix_app_id
MATHPIX_APP_KEY=your_mathpix_app_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
```

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

#### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:5173`

## API Endpoints

### Backend API

- `GET /` - Health check
- `POST /upload` - Upload image and extract text via OCR
- `POST /query` - Process question and get AI solution
- `GET /stats/topic` - Get topic statistics
- `GET /subjects` - Get available subjects

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

### Customizing OCR

The system automatically chooses between Google Vision and Mathpix based on mathematical content detection. You can modify the `is_math_heavy()` function in `backend/main.py` to adjust this logic.

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
