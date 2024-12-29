from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from ai_services import generate_drill, get_drill_answer, call_claude
from translations import TRANSLATIONS
from flask_cors import CORS
import json

load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static/react', static_url_path='')
CORS(app)

# Set the secret key from environment variable or use a default in development
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', '0b8862ea287391e63c177e368d1a923163f9e7264915c299fa66fa20624a5f98')
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')

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

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'success': True, 'message': 'Already logged in'})
        
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        try:
            response = supabase.table('users').select('*').eq('username', username).execute()
            if response.data:
                user_data = response.data[0]
                if check_password_hash(user_data['password_hash'], password):
                    user = User(user_data)
                    login_user(user)
                    return jsonify({'success': True, 'message': 'Login successful'})
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        except Exception as e:
            print(f"Error logging in: {e}")
            return jsonify({'success': False, 'error': 'Error logging in'}), 500
    
    return jsonify({'success': False, 'error': 'Method not allowed'}), 405

@app.route('/login', methods=['GET', 'POST'])
def login_page():
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
    return render_template('login.html', translations=translations, google_client_id=app.config['GOOGLE_CLIENT_ID'])

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

@app.route('/index')
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

@app.route('/api/get_drill', methods=['POST'])
@login_required
def get_drill():
    try:
        data = request.get_json()
        subject = data.get('subject', 'algebra')
        
        # Get user's preferred language
        language = current_user.preferred_language or 'he'
        
        # Get a drill based on the subject
        drill = generate_drill(subject, language)
        
        # Store the current drill in the session
        session['current_drill'] = {
            'question': drill['question'],
            'answer': drill['answer'],
            'hint': drill.get('hint', ''),
            'subject': subject
        }
        
        return jsonify({
            'question': drill['question'],
            'hint': drill.get('hint', '')
        })
        
    except Exception as e:
        print(f"Error generating drill: {e}")
        return jsonify({'error': 'Failed to generate drill'}), 500

@app.route('/api/check_answer', methods=['POST'])
@login_required
def check_answer():
    try:
        data = request.get_json()
        user_answer = data.get('answer', '').strip()
        
        if not user_answer:
            return jsonify({
                'correct': False,
                'feedback': 'Please provide an answer'
            })
            
        current_drill = session.get('current_drill')
        if not current_drill:
            return jsonify({
                'correct': False,
                'feedback': 'No active drill found. Please get a new drill.'
            })
            
        # Get feedback on the answer
        result = get_drill_answer(
            question=current_drill['question'],
            correct_answer=current_drill['answer'],
            user_answer=user_answer,
            language=current_user.preferred_language or 'he'
        )
        
        if result['correct']:
            # Update user's score
            try:
                current_score = current_user.total_score or 0
                new_score = current_score + 1
                
                response = supabase.table('users').update({
                    'total_score': new_score
                }).eq('id', current_user.id).execute()
                
                if response.data:
                    current_user.total_score = new_score
            except Exception as e:
                print(f"Error updating score: {e}")
        
        return jsonify({
            'correct': result['correct'],
            'feedback': result['feedback']
        })
        
    except Exception as e:
        print(f"Error checking answer: {e}")
        return jsonify({'error': 'Failed to check answer'}), 500

@app.route('/get_user_stats')
@login_required
def get_user_stats():
    try:
        # Get user's learning sessions
        response = supabase.table('learning_sessions')\
            .select('*')\
            .eq('user_id', str(current_user.id))\
            .execute()
            
        sessions = response.data if response.data else []
        
        # Calculate stats
        total_problems = sum(session['problems_attempted'] for session in sessions)
        total_solved = sum(session['problems_solved'] for session in sessions)
        total_hints = sum(session['hints_used'] for session in sessions)
        total_score = sum(session['score'] for session in sessions)
        
        return jsonify({
            'total_score': total_score,
            'problems_attempted': total_problems,
            'problems_solved': total_solved,
            'hints_used': total_hints,
            'username': current_user.username
        })
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    if not all([username, email, password, confirm_password]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
    if password != confirm_password:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
    
    try:
        # Check if username exists
        response = supabase.table('users').select('*').eq('username', username).execute()
        if response.data:
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
            
        # Check if email exists
        response = supabase.table('users').select('*').eq('email', email).execute()
        if response.data:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
            
        # Create new user
        password_hash = generate_password_hash(password)
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat(),
            'total_score': 0,
            'preferred_language': 'he'
        }
        
        response = supabase.table('users').insert(user_data).execute()
        if response.data:
            user = User(response.data[0])
            login_user(user)
            return jsonify({'success': True, 'message': 'Registration successful'})
            
        return jsonify({'success': False, 'error': 'Error creating user'}), 500
    except Exception as e:
        print(f"Error registering user: {e}")
        return jsonify({'success': False, 'error': 'Error registering user'}), 500

@app.route('/api/logout')
def api_logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/profile')
@login_required
def api_profile():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'total_score': current_user.total_score,
        'created_at': current_user.created_at,
        'preferred_language': current_user.preferred_language
    })

@app.route('/google-signin', methods=['POST'])
def google_signin():
    try:
        # Get the token from the request
        token = request.json.get('credential')
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 400

        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), app.config['GOOGLE_CLIENT_ID'])

        # Get user info from the token
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])  # Use email prefix if name not provided

        # Check if user exists in database
        response = supabase.table('users').select('*').eq('email', email).execute()
        
        if response.data:
            # User exists, log them in
            user = User(response.data[0])
            login_user(user)
            return jsonify({
                'success': True,
                'message': TRANSLATIONS[session.get('language', 'he')]['google_signin_success']
            })
        else:
            # Create new user
            password = generate_password_hash(token[:32])  # Use first 32 chars of token as password
            new_user = {
                'email': email,
                'username': name,
                'password_hash': password,
                'total_score': 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = supabase.table('users').insert(new_user).execute()
            if response.data:
                user = User(response.data[0])
                login_user(user)
                return jsonify({
                    'success': True,
                    'message': TRANSLATIONS[session.get('language', 'he')]['google_signin_success']
                })
            else:
                raise Exception('Failed to create user')

    except ValueError as e:
        # Invalid token
        return jsonify({
            'success': False,
            'error': TRANSLATIONS[session.get('language', 'he')]['google_signin_error']
        }), 401
    except Exception as e:
        print(f"Error in Google sign-in: {str(e)}")
        return jsonify({
            'success': False,
            'error': TRANSLATIONS[session.get('language', 'he')]['google_signin_error']
        }), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get the current drill from session
        current_drill = session.get('current_drill')
        if not current_drill:
            return jsonify({'error': 'No active drill found. Please get a new drill.'}), 400
            
        # Get help from Claude
        language = current_user.preferred_language or 'he'
        context = {
            'question': current_drill['question'],
            'user_question': data['message']
        }
        
        if language == 'he':
            prompt = f"""אתה מורה למתמטיקה מסור. התלמיד מבקש עזרה בשאלה הבאה:

            שאלה: {context['question']}
            שאלת התלמיד: {context['user_question']}

            עזור לתלמיד בצורה מכוונת, בלי לתת את התשובה המלאה. תן רמזים והכוונה שיעזרו לו להגיע לפתרון בעצמו."""
        else:
            prompt = f"""You are a helpful math teacher. The student needs help with the following question:

            Question: {context['question']}
            Student's question: {context['user_question']}

            Help the student in a guided way, without giving the full answer. Provide hints and guidance that will help them reach the solution on their own."""
        
        response = call_claude(prompt, language=language)
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Error in chat: {e}")
        if language == 'he':
            error_msg = 'מצטער, נתקלתי בשגיאה. אנא נסה שוב.'
        else:
            error_msg = 'Sorry, I encountered an error. Please try again.'
        return jsonify({'error': error_msg}), 500

# Serve React App - this should be after all other routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print(f"Serving static files from: {app.static_folder}")
    app.run(debug=True)
