import os
import subprocess
import json
import PyPDF2
import pdfplumber
import io
from openai import OpenAI
from supabase import create_client
import re
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import psycopg2

load_dotenv()

# Load environment variables or keys
SUPABASE_URL = 'https://ocdjqofrcrobgrjyjqox.supabase.co'  # Correct to HTTPS
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9jZGpxb2ZyY3JvYmdyanlqcW94Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjQzOTU3OSwiZXhwIjoyMDY4MDE1NTc5fQ.CsP6jzBuJtPUFkHdWPyle2dgFOaY6096zTddYfORnPM'  # From apikeys.txt
OPENAI_API_KEY = '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'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url='https://openrouter.ai/api/v1')

# Google Drive folder ID from the link
FOLDER_ID = '14mkeUmjvsWOWtpns_F3u6yiO6x537OvM'

# Function to get Google Drive service
def get_drive_service():
    # You need to set up credentials.json or use OAuth flow
    # For simplicity, assume credentials are set up
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.readonly'])
    return build('drive', 'v3', credentials=creds)

# Download PDFs from folder
def download_pdfs():
    folder_url = 'https://drive.google.com/drive/folders/14mkeUmjvsWOWtpns_F3u6yiO6x537OvM'
    subprocess.run(['gdown', '--folder', folder_url, '-O', 'pdfs'])

# Chunk PDF (simple example, improve for questions/syllabus)
def chunk_pdf(file_path):
    chunks = []
    with pdfplumber.open(file_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            full_text += page.extract_text() + '\n'
        # Split by question numbers (e.g., 1., 2., (a), etc.)
        question_chunks = re.split(r'(?m)^\d+\.|\(\w+\)', full_text)
        chunks = [chunk.strip() for chunk in question_chunks if chunk.strip()]
    return chunks

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text):
    return embedding_model.encode(text).tolist()

# Upload to Supabase
def upload_to_supabase(chunks, subject, year=None, paper=None, is_syllabus=False):
    table = 'syllabus_chunks' if is_syllabus else 'question_chunks'
    for chunk in chunks:
        embedding = embed_text(chunk)
        data = {
            'subject': subject,
            'chunk_text': chunk,
            'embedding': embedding
        }
        if not is_syllabus:
            data.update({'year': year, 'paper': paper})
        # Add question_id, topic_title as needed
        supabase.table(table).insert(data).execute()

# Main function
def main():
    # Connect to Supabase with psycopg2
    conn = psycopg2.connect(
        host='aws-0-eu-central-1.pooler.supabase.com',
        port=6543,
        dbname='postgres',
        user='postgres.ocdjqofrcrobgrjyjqox',
        password=SUPABASE_KEY
    )
    cur = conn.cursor()
    sql_statements = [
        'CREATE EXTENSION IF NOT EXISTS vector;',
        'CREATE TABLE IF NOT EXISTS question_chunks (id SERIAL PRIMARY KEY, subject TEXT NOT NULL, year INTEGER, paper TEXT, question_id TEXT, chunk_text TEXT NOT NULL, embedding VECTOR(384));',
        'CREATE TABLE IF NOT EXISTS syllabus_chunks (id SERIAL PRIMARY KEY, subject TEXT NOT NULL, topic_title TEXT, chunk_text TEXT NOT NULL, embedding VECTOR(384));',
        'CREATE MATERIALIZED VIEW IF NOT EXISTS topic_stats AS SELECT subject, topic_title, year, COUNT(*) AS occurrence_ct FROM syllabus_chunks GROUP BY subject, topic_title, year;',
        'CREATE INDEX IF NOT EXISTS question_chunks_embedding_idx ON question_chunks USING hnsw (embedding vector_cosine_ops);',
        'CREATE INDEX IF NOT EXISTS syllabus_chunks_embedding_idx ON syllabus_chunks USING hnsw (embedding vector_cosine_ops);',
        'CREATE INDEX IF NOT EXISTS question_chunks_subject_year_idx ON question_chunks (subject, year);'
    ]
    for sql in sql_statements:
        try:
            cur.execute(sql)
            conn.commit()
        except Exception as e:
            print(f'Error executing SQL: {sql} - {e}')
            conn.rollback()
    cur.close()
    conn.close()
    download_pdfs()
    pdf_dir = 'pdfs'
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            file_path = os.path.join(pdf_dir, filename)
            is_syllabus = 'syllabus' in filename.lower()
            subject = 'Pure Mathematics'  # Parse from filename or assume
            year = None
            paper = None
            if not is_syllabus:
                # Parse year and paper from filename, e.g., 'Pure Maths 2023 U1 P2.pdf'
                match = re.match(r'.*(\d{4})\s+U(\d)\s+P(\d)', filename)
                if match:
                    year = int(match.group(1))
                    unit = match.group(2)
                    paper_num = match.group(3)
                    paper = f'U{unit} P{paper_num}'
            chunks = chunk_pdf(file_path)
            upload_to_supabase(chunks, subject, year, paper, is_syllabus)

if __name__ == '__main__':
    main()
