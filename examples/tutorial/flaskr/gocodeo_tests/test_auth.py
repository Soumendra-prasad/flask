import pytest
from unittest.mock import patch, MagicMock
from flask import g, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from .auth import login_required, load_logged_in_user, register, login, logout
from .db import get_db

@pytest.fixture
def client():
    # Setup for Flask application client
    from flask import Flask
    app = Flask(__name__)
    app.secret_key = 'test_secret'
    app.register_blueprint(auth)
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    db_mock = MagicMock()
    with patch('examples.tutorial.flaskr.auth.get_db', return_value=db_mock) as mock:
        yield db_mock

@pytest.fixture
def mock_session():
    with patch('flask.session', new_callable=MagicMock) as mock:
        yield mock

@pytest.fixture
def mock_g():
    with patch('flask.g', new_callable=MagicMock) as mock:
        yield mock

@pytest.fixture
def mock_flash():
    with patch('flask.flash') as mock:
        yield mock

@pytest.fixture
def mock_redirect():
    with patch('flask.redirect') as mock:
        yield mock

@pytest.fixture
def mock_url_for():
    with patch('flask.url_for') as mock:
        yield mock

@pytest.fixture
def mock_check_password_hash():
    with patch('werkzeug.security.check_password_hash', return_value=True) as mock:
        yield mock

@pytest.fixture
def mock_generate_password_hash():
    with patch('werkzeug.security.generate_password_hash', return_value='hashed_password') as mock:
        yield mock

# happy path - load_logged_in_user - Test that load_logged_in_user sets g.user to None if no user_id in session
@patch('examples.tutorial.flaskr.auth.session', new_callable=MagicMock)
@patch('examples.tutorial.flaskr.auth.g', new_callable=MagicMock)
def test_load_logged_in_user_no_user_id(mock_g, mock_session):
    mock_session.get.return_value = None
    load_logged_in_user()
    assert mock_g.user is None


# happy path - register - Test that register redirects to login page after successful registration
@patch('examples.tutorial.flaskr.auth.get_db')
@patch('examples.tutorial.flaskr.auth.redirect')
@patch('examples.tutorial.flaskr.auth.url_for')
@patch('examples.tutorial.flaskr.auth.request')
def test_register_redirects_after_success(mock_request, mock_url_for, mock_redirect, mock_get_db, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': 'new_user', 'password': 'new_password'}
    mock_url_for.return_value = '/auth/login'
    db_mock = mock_get_db.return_value
    db_mock.execute.return_value = None
    db_mock.commit.return_value = None
    response = client.post('/auth/register', data={'username': 'new_user', 'password': 'new_password'})
    mock_redirect.assert_called_once_with('/auth/login')
    assert response.status_code == 302


# happy path - login - Test that login redirects to index after successful login
@patch('examples.tutorial.flaskr.auth.get_db')
@patch('examples.tutorial.flaskr.auth.redirect')
@patch('examples.tutorial.flaskr.auth.url_for')
@patch('examples.tutorial.flaskr.auth.request')
@patch('examples.tutorial.flaskr.auth.session', new_callable=MagicMock)
@patch('examples.tutorial.flaskr.auth.check_password_hash')
def test_login_redirects_after_success(mock_check_password_hash, mock_session, mock_request, mock_url_for, mock_redirect, mock_get_db, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': 'existing_user', 'password': 'correct_password'}
    mock_url_for.return_value = '/index'
    mock_check_password_hash.return_value = True
    db_mock = mock_get_db.return_value
    db_mock.execute.return_value.fetchone.return_value = {'id': 1, 'username': 'existing_user', 'password': 'hashed_password'}
    response = client.post('/auth/login', data={'username': 'existing_user', 'password': 'correct_password'})
    mock_redirect.assert_called_once_with('/index')
    assert response.status_code == 302


# happy path - logout - Test that logout clears session and redirects to index
@patch('examples.tutorial.flaskr.auth.session', new_callable=MagicMock)
@patch('examples.tutorial.flaskr.auth.redirect')
@patch('examples.tutorial.flaskr.auth.url_for')
def test_logout_clears_session(mock_url_for, mock_redirect, mock_session, client):
    mock_url_for.return_value = '/index'
    response = client.get('/auth/logout')
    mock_session.clear.assert_called_once()
    mock_redirect.assert_called_once_with('/index')
    assert response.status_code == 302


# edge case - register - Test that register shows error if username is missing
@patch('examples.tutorial.flaskr.auth.request')
@patch('examples.tutorial.flaskr.auth.flash')
def test_register_missing_username(mock_flash, mock_request, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': '', 'password': 'password'}
    response = client.post('/auth/register', data={'username': '', 'password': 'password'})
    mock_flash.assert_called_once_with('Username is required.')
    assert response.status_code == 200


# edge case - register - Test that register shows error if password is missing
@patch('examples.tutorial.flaskr.auth.request')
@patch('examples.tutorial.flaskr.auth.flash')
def test_register_missing_password(mock_flash, mock_request, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': 'user', 'password': ''}
    response = client.post('/auth/register', data={'username': 'user', 'password': ''})
    mock_flash.assert_called_once_with('Password is required.')
    assert response.status_code == 200


# edge case - register - Test that register shows error if username already exists
@patch('examples.tutorial.flaskr.auth.get_db')
@patch('examples.tutorial.flaskr.auth.request')
@patch('examples.tutorial.flaskr.auth.flash')
def test_register_username_exists(mock_flash, mock_request, mock_get_db, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': 'existing_user', 'password': 'password'}
    db_mock = mock_get_db.return_value
    db_mock.execute.side_effect = db_mock.IntegrityError
    response = client.post('/auth/register', data={'username': 'existing_user', 'password': 'password'})
    mock_flash.assert_called_once_with('User existing_user is already registered.')
    assert response.status_code == 200


# edge case - login - Test that login shows error if username is incorrect
@patch('examples.tutorial.flaskr.auth.get_db')
@patch('examples.tutorial.flaskr.auth.request')
@patch('examples.tutorial.flaskr.auth.flash')
def test_login_incorrect_username(mock_flash, mock_request, mock_get_db, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': 'wrong_user', 'password': 'password'}
    db_mock = mock_get_db.return_value
    db_mock.execute.return_value.fetchone.return_value = None
    response = client.post('/auth/login', data={'username': 'wrong_user', 'password': 'password'})
    mock_flash.assert_called_once_with('Incorrect username.')
    assert response.status_code == 200


# edge case - login - Test that login shows error if password is incorrect
@patch('examples.tutorial.flaskr.auth.get_db')
@patch('examples.tutorial.flaskr.auth.request')
@patch('examples.tutorial.flaskr.auth.flash')
@patch('examples.tutorial.flaskr.auth.check_password_hash')
def test_login_incorrect_password(mock_check_password_hash, mock_flash, mock_request, mock_get_db, client):
    mock_request.method = 'POST'
    mock_request.form = {'username': 'existing_user', 'password': 'wrong_password'}
    db_mock = mock_get_db.return_value
    db_mock.execute.return_value.fetchone.return_value = {'id': 1, 'username': 'existing_user', 'password': 'hashed_password'}
    mock_check_password_hash.return_value = False
    response = client.post('/auth/login', data={'username': 'existing_user', 'password': 'wrong_password'})
    mock_flash.assert_called_once_with('Incorrect password.')
    assert response.status_code == 200


