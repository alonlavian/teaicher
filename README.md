# Math Learning Assistant

An interactive web application that helps students learn mathematics through personalized drills and an AI-powered tutor.

## Features

- Interactive subject selection gallery
- Dynamic math drills for different subjects
- AI-powered chat tutor for personalized help
- Modern, soft UI design
- Real-time feedback and assistance

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Subjects Available

- Algebra
- Geometry
- Arithmetic
- Statistics

## How to Use

1. Select a subject from the gallery
2. View the practice problem
3. Use the chat interface to get help from the AI tutor
4. Click "New Problem" to get a different drill
5. Continue practicing and learning!
