# EduNova — AI Personalized Learning System
> Learn Smarter. Grow Faster. Only with EduNova.
> Built for AMD Slingshot Hackathon | Team CodeNovaX

## Stack (No Database!)
- Frontend : HTML + CSS + Vanilla JS
- Backend  : Python Flask + OpenAI GPT-4o
- Storage  : In-memory (Flask session)

## Setup in 3 Steps

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI key in .env
```
OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Run
```bash
cd backend
python app.py
```
Then open `frontend/index.html` in your browser.

## Pages
| Page | File | What it does |
|------|------|-------------|
| Landing + Auth | index.html | Login / Signup |
| Quiz | quiz.html | 10-question diagnostic |
| AI Tutor | tutor.html | GPT-4o chat tutor |
| Dashboard | dashboard.html | Charts + progress |

## API Endpoints
```
POST /api/auth/register   → Sign up
POST /api/auth/login      → Sign in
POST /api/auth/logout     → Sign out
GET  /api/auth/me         → Current user

GET  /api/quiz/questions  → Get 10 questions
POST /api/quiz/submit     → Submit + get AI analysis

POST /api/tutor/chat      → Chat with GPT-4o tutor
POST /api/tutor/clear     → Clear chat history

GET  /api/dashboard/data  → All dashboard data
GET  /api/health          → Health check
```
