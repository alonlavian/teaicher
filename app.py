from flask import Flask, render_template, jsonify, request, session
from ai_services import call_claude
import os
from dotenv import load_dotenv
from translations import TRANSLATIONS
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))  # Set a secret key for session
claude = None  # Removed the direct Anthropic client usage

# Math subjects and their corresponding drills
SUBJECTS = {
    'algebra': {
        'name': 'Algebra',
        'icon': '📐',
        'description': 'Learn equations, functions, and mathematical patterns'
    },
    'geometry': {
        'name': 'Geometry',
        'icon': '📏',
        'description': 'Explore shapes, angles, and spatial relationships'
    },
    'arithmetic': {
        'name': 'Arithmetic',
        'icon': '🔢',
        'description': 'Master basic mathematical operations'
    },
    'statistics': {
        'name': 'Statistics',
        'icon': '📊',
        'description': 'Understand data analysis and probability'
    }
}

def get_translated_subjects(lang):
    translated = {}
    for key, subject in SUBJECTS.items():
        translated[key] = {
            'name': TRANSLATIONS[lang][key]['name'],
            'icon': subject['icon'],
            'description': TRANSLATIONS[lang][key]['description']
        }
    return translated

def generate_drill(subject):
    drills = {
        'algebra': [
            {'question': 'Solve for x: 2x + 5 = 13', 'answer': '4'},
            {'question': 'Find x: 3(x - 4) = 15', 'answer': '9'},
            {'question': 'Solve the equation: 5x + 2 = 3x - 6', 'answer': '-4'},
            {'question': 'If 2(x + 3) = 16, what is x?', 'answer': '5'}
        ],
        'geometry': [
            {'question': 'Calculate the area of a triangle with base 6 and height 8', 'answer': '24'},
            {'question': 'Find the perimeter of a rectangle with length 10 and width 4', 'answer': '28'},
            {'question': 'What is the area of a circle with radius 5?', 'answer': '78.54'},
            {'question': 'Calculate the volume of a cube with side length 3', 'answer': '27'}
        ],
        'arithmetic': [
            {'question': 'What is 15% of 80?', 'answer': '12'},
            {'question': 'Calculate: 123 × 12', 'answer': '1476'},
            {'question': 'Divide 156 by 12', 'answer': '13'},
            {'question': 'What is the sum of 1/4 and 2/3?', 'answer': '0.917'}
        ],
        'statistics': [
            {'question': 'Calculate the mean of the numbers: 4, 8, 15, 16, 23', 'answer': '13.2'},
            {'question': 'Find the median of: 7, 12, 3, 9, 15, 18', 'answer': '10.5'},
            {'question': 'What is the mode of: 2, 4, 4, 6, 8, 4, 10?', 'answer': '4'},
            {'question': 'Calculate the range of: 15, 25, 35, 45, 55', 'answer': '40'}
        ]
    }
    import random
    drill_list = drills.get(subject, [{'question': 'Invalid subject', 'answer': ''}])
    drill = random.choice(drill_list)
    return {'drill': drill['question'], 'answer': drill['answer']}

@app.route('/')
def home():
    lang = session.get('language', 'en')
    return render_template('index.html',
                         subjects=get_translated_subjects(lang),
                         translations=TRANSLATIONS[lang])

@app.route('/set_language', methods=['POST'])
def set_language():
    data = request.json
    lang = data.get('language', 'en')
    if lang in TRANSLATIONS:
        session['language'] = lang
        return jsonify({
            'success': True,
            'translations': TRANSLATIONS[lang],
            'subjects': get_translated_subjects(lang)
        })
    return jsonify({'error': 'Invalid language'}), 400

@app.route('/get_drill/<subject>')
def get_drill(subject):
    drill_data = generate_drill(subject)
    # Store the answer in the session for validation
    session['current_answer'] = drill_data['answer']
    return jsonify({'drill': drill_data['drill']})

@app.route('/validate_answer', methods=['POST'])
def validate_answer():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        answer = data.get('answer')
        drill = data.get('drill')
        subject = data.get('subject')

        if not all([answer, drill, subject]):
            return jsonify({'error': 'Missing required fields'}), 400

        lang = session.get('language', 'en')
        language_context = {
            'en': 'Respond in English.',
            'fr': 'Répondez en français.',
            'he': 'השב בעברית.'
        }

        context = f"""You are a math tutor helping students learn {subject}. 
        {language_context[lang]}
        Evaluate if this answer is correct for the given problem.
        If correct, provide encouragement.
        If incorrect, provide a helpful hint without giving away the answer."""

        prompt = f"Problem: {drill}\nStudent's answer: {answer}\nIs this correct? Provide feedback:"
        
        logging.info(f"Calling Claude with context: {context}")
        feedback = call_claude(prompt, context=context)
        
        # Basic correct/incorrect detection based on feedback
        correct = any(word in feedback.lower() for word in ['correct', 'right', 'exactement', 'bravo', 'נכון', 'מצוין'])
        
        return jsonify({
            'correct': correct,
            'feedback': feedback
        })
    except Exception as e:
        logging.error(f"Error validating answer: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        message = data.get('message')
        subject = data.get('subject')
        drill = data.get('drill', '')

        if not message or not subject:
            return jsonify({'error': 'Missing required fields'}), 400

        lang = session.get('language', 'en')
        language_context = {
            'en': 'Respond in English.',
            'fr': 'Répondez en français.',
            'he': 'השב בעברית.'
        }

        context = f"""You are a friendly and encouraging math tutor specializing in {subject}.
        {language_context[lang]}
        Current problem being discussed: {drill}
        Provide clear, step-by-step explanations when helping with problems.
        Keep responses concise but informative."""

        response = call_claude(message, context=context)
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
