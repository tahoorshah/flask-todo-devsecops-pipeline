import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            from app import db
            db.create_all()
            yield client

def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json['status'] == 'ok'

def test_create_todo(client):
    r = client.post('/todos', json={'title': 'Buy milk'})
    assert r.status_code == 201
    assert r.json['title'] == 'Buy milk'

def test_create_todo_missing_title(client):
    r = client.post('/todos', json={})
    assert r.status_code == 400
