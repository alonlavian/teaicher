from flask import Flask, render_template, jsonify, request, session
from ai_services import call_claude, generate_math_problem
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
    """Generate a drill for the given subject using AI."""
    lang = session.get('language', 'he')  # Get current language from session
    try:
        problem = generate_math_problem(subject, lang)
        return {'drill': problem['question'], 'answer': problem['answer']}
    except Exception as e:
        logger.error(f"Error generating drill: {e}")
        # Fallback to a simple problem if generation fails
        return {
            'drill': '1 + 1 = ?',
            'answer': '2'
        }

@app.route('/')
def home():
    lang = session.get('language', 'he')  # Changed default from 'en' to 'he'
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
    try:
        lang = session.get('language', 'he')
        drill_data = generate_math_problem(subject, lang)
        # Start a new drill session
        session['current_drill'] = drill_data
        session['conversation_history'] = []  # Reset conversation history
        session['drill_solved'] = False
        # Only send the question to the frontend
        return jsonify({
            'drill': drill_data['question'],
            'clearChat': True  # Signal frontend to clear chat
        })
    except Exception as e:
        logger.error(f"Error getting drill: {e}")
        error_messages = {
            'he': 'מצטער, לא הצלחתי ליצור תרגיל. אנא נסה שוב.',
            'en': 'Sorry, I could not generate a drill. Please try again.'
        }
        return jsonify({'error': error_messages.get(lang, error_messages['en'])})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    subject = data.get('subject', '')
    lang = session.get('language', 'he')
    current_drill = session.get('current_drill', {})
    conversation_history = session.get('conversation_history', [])
    drill_solved = session.get('drill_solved', False)

    try:
        # Create context with conversation history
        if current_drill:
            history_text = "\n".join([f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}" 
                                    for i, msg in enumerate(conversation_history)])
            
            if lang == 'he':
                context = f"""נושא נוכחי: {subject}
                שאלה נוכחית: {current_drill['question']}
                תשובה נכונה: {current_drill['answer']}
                
                היסטוריית שיחה:
                {history_text}
                
                הנחיות חשובות:
                1. אם התלמיד מבקש עזרה, תן לו רמז קטן שיכוון אותו לכיוון הנכון. אל תיתן את הפתרון המלא.
                2. אם התלמיד נתקע, תן לו רמז נוסף שיקדם אותו.
                3. רק אם התלמיד מנסה לפתור ונותן תשובה, בדוק אם היא נכונה.
                4. אם התשובה נכונה, התחל את תגובתך עם: [CORRECT_ANSWER]
                
                שמור על גישה מעודדת ותומכת."""
            else:
                context = f"""Current subject: {subject}
                Current problem: {current_drill['question']}
                Correct answer: {current_drill['answer']}
                
                Conversation history:
                {history_text}
                
                Important guidelines:
                1. If the student asks for help, give them a small hint that points them in the right direction. Do not provide the full solution.
                2. If the student is stuck, provide an additional hint to help them progress.
                3. Only check if an answer is correct when the student attempts to solve and provides an answer.
                4. If the answer is correct, start your response with: [CORRECT_ANSWER]
                
                Maintain an encouraging and supportive approach."""
        else:
            context = f"Subject: {subject}"
        
        response = call_claude(
            query=message,
            context=context,
            language=lang
        )
        
        # Update conversation history
        conversation_history.extend([message, response])
        session['conversation_history'] = conversation_history

        # Check if the answer was correct
        if '[CORRECT_ANSWER]' in response:
            session['drill_solved'] = True
            if lang == 'he':
                response += "\n\nמצוין! אתה מוכן לתרגיל הבא. לחץ על 'תרגיל חדש' להמשיך."
            else:
                response += "\n\nExcellent! You're ready for the next problem. Click 'New Problem' to continue."

        return jsonify({
            'success': True,
            'response': response,
            'drillSolved': session['drill_solved']
        })
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        error_messages = {
            'he': 'מצטער, אירעה שגיאה. אנא נסה שוב.',
            'en': 'Sorry, an error occurred. Please try again.'
        }
        return jsonify({
            'success': False,
            'response': error_messages.get(lang, error_messages['en'])
        })

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

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
