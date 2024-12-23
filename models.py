from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferred_language = db.Column(db.String(10), default='he')
    total_score = db.Column(db.Integer, default=0)
    learning_sessions = db.relationship('LearningSession', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LearningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    problems_attempted = db.Column(db.Integer, default=0)
    problems_solved = db.Column(db.Integer, default=0)
    hints_used = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    
    def calculate_score(self):
        """
        Calculate session score based on:
        - Number of problems solved
        - Ratio of problems solved to attempted
        - Number of hints used (fewer hints = higher score)
        """
        if self.problems_attempted == 0:
            return 0
            
        success_ratio = self.problems_solved / self.problems_attempted
        hint_penalty = max(0, 1 - (self.hints_used / (self.problems_attempted * 2)))  # Allow up to 2 hints per problem
        base_score = self.problems_solved * 100
        
        return int(base_score * success_ratio * hint_penalty)
