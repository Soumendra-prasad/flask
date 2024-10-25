import pytest
from unittest import mock
from src.flask.app import Flask
from src.flask.cli import AppGroup
from src.flask.ctx import AppContext, RequestContext
from src.flask.globals import _cv_app, _cv_request, current_app, g, request, request_ctx, session
from src.flask.helpers import get_debug_flag, get_flashed_messages, get_load_dotenv, send_from_directory
from src.flask.sansio.app import App
from src.flask.sansio.scaffold import _sentinel
from src.flask.sessions import SecureCookieSessionInterface, SessionInterface
from src.flask.signals import appcontext_tearing_down, got_request_exception, request_finished, request_started, request_tearing_down
from src.flask.templating import Environment
from src.flask.wrappers import Request, Response

@pytest.fixture
def mock_flask_app():
    with mock.patch('src.flask.app.cli.AppGroup', return_value=mock.Mock(spec=AppGroup)) as mock_cli, \
         mock.patch('src.flask.app.AppContext', return_value=mock.Mock(spec=AppContext)) as mock_app_context, \
         mock.patch('src.flask.app.RequestContext', return_value=mock.Mock(spec=RequestContext)) as mock_request_context, \
         mock.patch('src.flask.app._cv_app', new_callable=mock.PropertyMock) as mock_cv_app, \
         mock.patch('src.flask.app._cv_request', new_callable=mock.PropertyMock) as mock_cv_request, \
         mock.patch('src.flask.app.current_app', new_callable=mock.PropertyMock) as mock_current_app, \
         mock.patch('src.flask.app.g', new_callable=mock.PropertyMock) as mock_g, \
         mock.patch('src.flask.app.request', new_callable=mock.PropertyMock) as mock_request, \
         mock.patch('src.flask.app.request_ctx', new_callable=mock.PropertyMock) as mock_request_ctx, \
         mock.patch('src.flask.app.session', new_callable=mock.PropertyMock) as mock_session, \
         mock.patch('src.flask.app.get_debug_flag', return_value=True) as mock_get_debug_flag, \
         mock.patch('src.flask.app.get_flashed_messages', return_value=[]) as mock_get_flashed_messages, \
         mock.patch('src.flask.app.get_load_dotenv', return_value=True) as mock_get_load_dotenv, \
         mock.patch('src.flask.app.send_from_directory', return_value=mock.Mock(spec=Response)) as mock_send_from_directory, \
         mock.patch('src.flask.app.SecureCookieSessionInterface', return_value=mock.Mock(spec=SecureCookieSessionInterface)) as mock_secure_cookie_session_interface, \
         mock.patch('src.flask.app.SessionInterface', return_value=mock.Mock(spec=SessionInterface)), \
         mock.patch('src.flask.app.appcontext_tearing_down', return_value=mock.Mock()) as mock_appcontext_tearing_down, \
         mock.patch('src.flask.app.got_request_exception', return_value=mock.Mock()) as mock_got_request_exception, \
         mock.patch('src.flask.app.request_finished', return_value=mock.Mock()) as mock_request_finished, \
         mock.patch('src.flask.app.request_started', return_value=mock.Mock()) as mock_request_started, \
         mock.patch('src.flask.app.request_tearing_down', return_value=mock.Mock()) as mock_request_tearing_down, \
         mock.patch('src.flask.app.Environment', return_value=mock.Mock(spec=Environment)) as mock_environment, \
         mock.patch('src.flask.app.Request', return_value=mock.Mock(spec=Request)) as mock_request_class, \
         mock.patch('src.flask.app.Response', return_value=mock.Mock(spec=Response)) as mock_response_class:
        
        app = Flask(import_name='test_app')
        yield app

# happy path - _make_timedelta - Test that _make_timedelta correctly returns a timedelta object when given an integer.
def test_make_timedelta_with_integer():
    result = _make_timedelta(3600)
    assert result == timedelta(seconds=3600)


# happy path - __init__ - Test that __init__ initializes Flask app with default static and template folders.
def test_flask_init_defaults(mock_flask_app):
    assert mock_flask_app.static_folder == 'static'
    assert mock_flask_app.template_folder == 'templates'


# happy path - get_send_file_max_age - Test that get_send_file_max_age returns None by default.
def test_get_send_file_max_age_default(mock_flask_app):
    mock_flask_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = None
    max_age = mock_flask_app.get_send_file_max_age('test_file.txt')
    assert max_age is None


# happy path - send_static_file - Test that send_static_file raises RuntimeError when static_folder is not set.
def test_send_static_file_no_static_folder(mock_flask_app):
    mock_flask_app.has_static_folder = False
    with pytest.raises(RuntimeError):
        mock_flask_app.send_static_file('test_file.txt')


# happy path - open_resource - Test that open_resource opens a file in read-binary mode by default.
def test_open_resource_default_mode(mock_flask_app):
    with mock.patch('builtins.open', mock.mock_open(read_data='data')) as mock_file:
        with mock_flask_app.open_resource('test_file.txt') as f:
            mock_file.assert_called_once_with(mock.ANY, 'rb')


# edge case - _make_timedelta - Test that _make_timedelta returns None when given None as input.
def test_make_timedelta_with_none():
    result = _make_timedelta(None)
    assert result is None


# edge case - __init__ - Test that __init__ raises AssertionError with invalid static_host/host_matching combination.
def test_flask_init_invalid_static_host():
    with pytest.raises(AssertionError):
        Flask(import_name='test_app', static_host='example.com', host_matching=False)


# edge case - get_send_file_max_age - Test that get_send_file_max_age handles timedelta configuration correctly.
def test_get_send_file_max_age_timedelta(mock_flask_app):
    mock_flask_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(hours=12)
    max_age = mock_flask_app.get_send_file_max_age('test_file.txt')
    assert max_age == 43200


# edge case - send_static_file - Test that send_static_file correctly uses max_age from get_send_file_max_age.
def test_send_static_file_with_max_age(mock_flask_app):
    mock_flask_app.has_static_folder = True
    with mock.patch('src.flask.app.send_from_directory') as mock_send_from_directory:
        mock_send_from_directory.return_value = mock.Mock(spec=Response)
        mock_flask_app.get_send_file_max_age = mock.Mock(return_value=3600)
        response = mock_flask_app.send_static_file('test_file.txt')
        mock_send_from_directory.assert_called_once_with(mock.ANY, 'test_file.txt', max_age=3600)
        assert response is not None


# edge case - open_resource - Test that open_resource raises ValueError for invalid mode.
def test_open_resource_invalid_mode(mock_flask_app):
    with pytest.raises(ValueError):
        mock_flask_app.open_resource('test_file.txt', mode='w')


# happy path - _make_timedelta - Test that _make_timedelta correctly handles zero as input and returns timedelta of zero seconds.
def test_make_timedelta_with_zero():
    result = _make_timedelta(0)
    assert result == timedelta(seconds=0)


# happy path - __init__ - Test that __init__ sets server name from configuration if provided.
def test_flask_init_with_server_name():
    app = Flask(import_name='test_app', server_name='example.com')
    assert app.config['SERVER_NAME'] == 'example.com'


# happy path - get_send_file_max_age - Test that get_send_file_max_age returns configured max age when set as integer.
def test_get_send_file_max_age_integer(mock_flask_app):
    mock_flask_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 7200
    max_age = mock_flask_app.get_send_file_max_age('test_file.txt')
    assert max_age == 7200


# happy path - send_static_file - Test that send_static_file correctly serves a file when static_folder is set.
def test_send_static_file_with_static_folder(mock_flask_app):
    mock_flask_app.has_static_folder = True
    with mock.patch('src.flask.app.send_from_directory') as mock_send_from_directory:
        mock_send_from_directory.return_value = mock.Mock(spec=Response)
        response = mock_flask_app.send_static_file('test_file.txt')
        mock_send_from_directory.assert_called_once()
        assert response is not None


# happy path - open_resource - Test that open_resource opens a file with specified encoding in text mode.
def test_open_resource_with_encoding(mock_flask_app):
    with mock.patch('builtins.open', mock.mock_open(read_data='data')) as mock_file:
        with mock_flask_app.open_resource('test_file.txt', mode='r', encoding='utf-8') as f:
            mock_file.assert_called_once_with(mock.ANY, 'r', encoding='utf-8')


