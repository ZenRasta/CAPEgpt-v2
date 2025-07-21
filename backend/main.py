from fastapi import FastAPI, UploadFile, File
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

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MATHPIX_APP_ID = os.getenv('MATHPIX_APP_ID')
MATHPIX_APP_KEY = os.getenv('MATHPIX_APP_KEY')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if GOOGLE_CREDENTIALS:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CREDENTIALS

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=OPENROUTER_API_KEY)

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text):
    return embedding_model.encode(text).tolist()

app = FastAPI()

def is_math_heavy(image_bytes):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    text = response.text_annotations[0].description if response.text_annotations else ''
    math_symbols = len(re.findall(r' [\+\-\*\/=\^\(\)] ', text))
    return math_symbols >= 10

def ocr_image(image_bytes, is_math):
    if is_math:
        response = requests.post(
            'https://api.mathpix.com/v3/text',
            files={'file': ('image.jpg', image_bytes, 'image/jpeg')},
            headers={'app_id': MATHPIX_APP_ID, 'app_key': MATHPIX_APP_KEY},
            data={'options_json': json.dumps({'math_inline_delimiters': ['$', '$'], 'rm_spaces': True})}
        )
        return response.json().get('text', '') if response.ok else ''
    else:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)
        return response.text_annotations[0].description if response.text_annotations else ''

@app.post('/upload')
async def upload_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    is_math = is_math_heavy(image_bytes)
    text = ocr_image(image_bytes, is_math)
    return {'text': text}

class QueryRequest(BaseModel):
    text: str
    subject: str

# In /query, use proper vector search
def vector_search(table, embedding, subject, limit=8):
    query_vec = np.array(embedding).tolist()
    response = supabase.table(table).select('*', count='exact').eq('subject', subject).order('embedding <=> %s', params=[query_vec], desc=False).limit(limit).execute()
    return response.data

@app.post('/query')
async def query(request: QueryRequest):
    embedding = embed_text(request.text)
    questions = vector_search('question_chunks', embedding, request.subject, 8)
    syllabus = vector_search('syllabus_chunks', embedding, request.subject, 5)
    # GPT prompt
    prompt = f'Question: {request.text}\nSimilar past questions: {questions}\nSyllabus: {syllabus}\nProvide step-by-step solution.'
    response = openai_client.chat.completions.create(model='openai/gpt-4o-mini', messages=[{'role': 'user', 'content': prompt}])
    answer = response.choices[0].message.content
    # Append insights
    years = [q['year'] for q in questions if q['year']]
    topics = [s['topic_title'] for s in syllabus if s['topic_title']]
    return {'answer': answer, 'years': years, 'topics': topics}

@app.get('/stats/topic')
async def get_topic_stats(subject: str, topic: str):
    # Implement as needed
    return {'stats': {}} 