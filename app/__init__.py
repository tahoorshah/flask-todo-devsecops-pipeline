import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///todos.db'
    )
    
    db.init_app(app)
    
    from .routes import bp
    app.register_blueprint(bp)
    
    with app.app_context():
        db.create_all()
        
    return app
