# AI Career Advisor

A web application that analyzes user skills and fetches live job postings to provide career advice.

## Project Structure

```
AI-career-advisor/
├── backend/
│   └── app.py
├── frontend/
│   ├── static/
│   └── templates/
│       └── index.html
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   RAPIDAPI_KEY=your_rapidapi_key
   ```

4. Run the Flask application:
   ```bash
   cd backend
   python app.py
   ```

5. Open your browser and navigate to `http://localhost:5000`

## Features

- Skill analysis using OpenAI's GPT model
- Live job posting fetching from RapidAPI
- Modern and responsive UI
- Real-time career advice based on user input

## Dependencies

- Flask 3.0.2
- Requests 2.31.0
- Python-dotenv 1.0.1