from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from ai_services import generate_drill, get_drill_answer, call_claude
from translations import TRANSLATIONS

load_dotenv()

app = Flask(__name__)

# Set the secret key from environment variable or use a default in development
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', '0b8862ea287391e63c177e368d1a923163f9e7264915c299fa66fa20624a5f98')

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login route
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = 'strong'  # Provide strong session protection

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.total_score = user_data.get('total_score', 0)
        self.created_at = user_data.get('created_at')
        self.preferred_language = user_data.get('preferred_language', 'he')

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            return User(response.data[0])
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting to register user: {username}, {email}")
        
        try:
            # Check if username exists
            username_check = supabase.table('users').select('*').eq('username', username).execute()
            print(f"Username check response: {username_check.data}")
            if username_check.data:
                flash('Username already exists')
                return redirect(url_for('register'))

            # Check if email exists
            email_check = supabase.table('users').select('*').eq('email', email).execute()
            print(f"Email check response: {email_check.data}")
            if email_check.data:
                flash('Email already registered')
                return redirect(url_for('register'))
            
            # Create new user
            user_data = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'total_score': 0,
                'preferred_language': 'he',
                'created_at': datetime.utcnow().isoformat()
            }
            print(f"Attempting to create user with data: {user_data}")
            
            response = supabase.table('users').insert(user_data).execute()
            print(f"Insert response: {response.data}")
            
            if response.data:
                user = User(response.data[0])
                login_user(user)
                flash('Registration successful!')
                return redirect(url_for('home'))
            else:
                print("No data in response after insert")
                flash('Error creating user: No data returned')
                return redirect(url_for('register'))
                
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            flash(f'Error creating user: {str(e)}')
            return redirect(url_for('register'))
            
    translations = TRANSLATIONS.get(session.get('language', 'he'), TRANSLATIONS['he'])
    return render_template('register.html', translations=translations)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            response = supabase.table('users').select('*').eq('username', username).execute()
            if response.data:
                user_data = response.data[0]
                if check_password_hash(user_data['password_hash'], password):
                    user = User(user_data)
                    login_user(user)
                    return redirect(url_for('home'))
            flash('Invalid username or password')
        except Exception as e:
            flash('Error logging in')
            print(f"Error logging in: {e}")
    
    translations = TRANSLATIONS.get(session.get('language', 'he'), TRANSLATIONS['he'])
    return render_template('login.html', translations=translations)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    translations = TRANSLATIONS.get(session.get('language', 'he'), TRANSLATIONS['he'])
    
    # Get user's learning sessions
    try:
        sessions = supabase.table('learning_sessions')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        
        learning_history = sessions.data if sessions.data else []
    except Exception as e:
        print(f"Error fetching learning sessions: {e}")
        learning_history = []
    
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'total_score': current_user.total_score,
        'member_since': current_user.created_at.split('T')[0] if current_user.created_at else 'N/A',
        'learning_history': learning_history
    }
    
    return render_template('profile.html', user=user_data, translations=translations)

@app.route('/set_language', methods=['POST'])
def set_language():
    data = request.get_json()
    language = data.get('language')
    if language in TRANSLATIONS:
        session['language'] = language
        if current_user.is_authenticated:
            try:
                supabase.table('users').update({'preferred_language': language}).eq('id', current_user.id).execute()
            except Exception as e:
                print(f"Error updating language preference: {e}")
    return jsonify({'success': True})

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/home')
@login_required
def home():
    translations = TRANSLATIONS.get(session.get('language', 'he'), TRANSLATIONS['he'])
    subjects = [
        {
            'id': 'algebra',
            'name': translations['algebra']['name'],
            'description': translations['algebra']['description'],
            'icon': 'fas fa-square-root-alt'
        },
        {
            'id': 'geometry',
            'name': translations['geometry']['name'],
            'description': translations['geometry']['description'],
            'icon': 'fas fa-shapes'
        },
        {
            'id': 'arithmetic',
            'name': translations['arithmetic']['name'],
            'description': translations['arithmetic']['description'],
            'icon': 'fas fa-calculator'
        },
        {
            'id': 'statistics',
            'name': translations['statistics']['name'],
            'description': translations['statistics']['description'],
            'icon': 'fas fa-chart-bar'
        }
    ]
    return render_template('index.html', subjects=subjects, translations=translations)

@app.route('/get_drill', methods=['POST'])
@login_required
def get_drill():
    try:
        data = request.get_json()
        print(f"Received request for drill in subject: {data}")
        
        if not data or 'subject' not in data:
            return jsonify({'error': 'No subject specified'}), 400
            
        subject = data['subject']
        language = session.get('language', 'he')
        
        # Generate drill using AI service
        drill_data = generate_drill(subject, language)
        print(f"Generated drill: {drill_data}")
        
        # Store drill in session for answer checking
        session['current_drill'] = drill_data
        
        # Store learning session with minimal required fields
        try:
            current_time = datetime.utcnow().isoformat()
            session_data = {
                'user_id': str(current_user.id),
                'subject': subject,
                'problems_attempted': 0,
                'problems_solved': 0,
                'hints_used': 0,
                'score': 0,
                'created_at': current_time,
                'started_at': current_time
            }
            print(f"Creating learning session with data: {session_data}")
            
            try:
                response = supabase.table('learning_sessions').insert(session_data).execute()
                session['learning_session_id'] = response.data[0]['id'] if response.data else None
                print(f"Created learning session: {response.data}")
            except Exception as e:
                error_response = getattr(e, 'response', None)
                if error_response:
                    try:
                        error_json = error_response.json()
                        print(f"Supabase error details: {error_json}")
                    except:
                        print(f"Raw error response: {error_response.text}")
                print(f"Error creating learning session: {str(e)}")
        except Exception as e:
            print(f"Outer error creating learning session: {str(e)}")
            # Continue even if session creation fails
            pass
        
        # Return the drill even if session creation failed
        return jsonify({
            'question': drill_data['question'],
            'success': True
        })
        
    except Exception as e:
        print(f"Error generating drill: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    try:
        data = request.get_json()
        if not data or 'answer' not in data:
            return jsonify({'error': 'No answer provided'}), 400
            
        # Get the current drill from session
        current_drill = session.get('current_drill')
        if not current_drill:
            return jsonify({'error': 'No active drill found'}), 400
            
        # Get the answer feedback from Claude
        language = session.get('language', 'he')
        result = get_drill_answer(current_drill['question'], data['answer'], language)
        
        # Update learning session if one exists
        session_id = session.get('learning_session_id')
        if session_id:
            try:
                # Get current session data
                response = supabase.table('learning_sessions').select('*').eq('id', session_id).execute()
                if response.data:
                    session_data = response.data[0]
                    # Update stats
                    updates = {
                        'problems_attempted': session_data['problems_attempted'] + 1,
                        'problems_solved': session_data['problems_solved'] + (1 if result['correct'] else 0),
                        'score': session_data['score'] + (10 if result['correct'] else 0)
                    }
                    supabase.table('learning_sessions').update(updates).eq('id', session_id).execute()
            except Exception as e:
                print(f"Error updating learning session: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error checking answer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get the current drill from session
        current_drill = session.get('current_drill')
        if not current_drill:
            return jsonify({'error': 'No active drill found'}), 400
            
        # Get the answer feedback from Claude
        language = session.get('language', 'he')
        question = data['message'].strip()
        
        # Update hint count if session exists
        session_id = session.get('learning_session_id')
        if session_id:
            try:
                response = supabase.table('learning_sessions').select('*').eq('id', session_id).execute()
                if response.data:
                    session_data = response.data[0]
                    supabase.table('learning_sessions').update({
                        'hints_used': session_data['hints_used'] + 1
                    }).eq('id', session_id).execute()
            except Exception as e:
                print(f"Error updating hint count: {e}")
        
        # Get help from Claude
        context = {
            'question': current_drill['question'],
            'user_question': question,
            'language': language
        }
        response = call_claude(
            f"Help the student with their question about this math problem. Problem: {context['question']}, Student's question: {context['user_question']}",
            language=language
        )
        
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
