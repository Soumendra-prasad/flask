import os
import pytest
from unittest import mock
from datetime import timedelta
from src.flask.blueprints import Blueprint
from src.flask.cli import AppGroup
from src.flask.globals import current_app
from src.flask.helpers import send_from_directory
from src.flask.sansio.blueprints import BlueprintSetupState
from src.flask.sansio.scaffold import _sentinel
from src.flask.wrappers import Response

@pytest.fixture
def mock_current_app():
    mock_app = mock.Mock()
    mock_app.config = {
        "SEND_FILE_MAX_AGE_DEFAULT": None
    }
    with mock.patch('src.flask.globals.current_app', mock_app):
        yield mock_app

@pytest.fixture
def mock_send_from_directory():
    with mock.patch('src.flask.helpers.send_from_directory') as mock_send:
        yield mock_send

@pytest.fixture
def mock_AppGroup():
    with mock.patch('src.flask.cli.AppGroup') as mock_cli_group:
        yield mock_cli_group

@pytest.fixture
def mock_BlueprintSetupState():
    with mock.patch('src.flask.sansio.blueprints.BlueprintSetupState') as mock_setup_state:
        yield mock_setup_state

@pytest.fixture
def mock_open():
    mock_open_func = mock.mock_open()
    with mock.patch('builtins.open', mock_open_func):
        yield mock_open_func

@pytest.fixture
def mock_timedelta():
    with mock.patch('src.flask.blueprints.timedelta', timedelta) as mock_td:
        yield mock_td

@pytest.fixture
def blueprint_instance(mock_current_app, mock_send_from_directory, mock_AppGroup):
    return Blueprint(
        name='test_blueprint',
        import_name='test_import',
        static_folder='/static',
        static_url_path='/static',
        template_folder='/templates',
        url_prefix='/prefix',
        subdomain='sub',
        url_defaults={'key': 'value'},
        root_path='/root',
        cli_group=_sentinel
    )

# happy path - __init__ - Test that Blueprint is initialized with all provided parameters correctly
def test_blueprint_initialization(mock_AppGroup):
    blueprint = Blueprint(
        name='test_blueprint',
        import_name='test_import',
        static_folder='/static',
        static_url_path='/static',
        template_folder='/templates',
        url_prefix='/prefix',
        subdomain='sub',
        url_defaults={'key': 'value'},
        root_path='/root',
        cli_group='group'
    )

    assert blueprint.name == 'test_blueprint'
    assert blueprint.import_name == 'test_import'
    assert blueprint.static_folder == '/static'
    assert blueprint.static_url_path == '/static'
    assert blueprint.template_folder == '/templates'
    assert blueprint.url_prefix == '/prefix'
    assert blueprint.subdomain == 'sub'
    assert blueprint.url_defaults == {'key': 'value'}
    assert blueprint.root_path == '/root'
    assert blueprint.cli_group == 'group'


# happy path - get_send_file_max_age - Test that get_send_file_max_age returns None when SEND_FILE_MAX_AGE_DEFAULT is None
def test_get_send_file_max_age_none_default(mock_current_app, blueprint_instance):
    mock_current_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = None
    max_age = blueprint_instance.get_send_file_max_age('test_file.txt')
    assert max_age is None


# happy path - send_static_file - Test that send_static_file raises RuntimeError when static_folder is not set
def test_send_static_file_no_static_folder(blueprint_instance):
    blueprint_instance.static_folder = None
    with pytest.raises(RuntimeError, match="'static_folder' must be set to serve static_files."):
        blueprint_instance.send_static_file('test_file.txt')


# happy path - open_resource - Test that open_resource opens a file in binary mode
def test_open_resource_binary_mode(mock_open, blueprint_instance):
    blueprint_instance.root_path = '/root'
    with blueprint_instance.open_resource('test_file.bin', 'rb') as f:
        mock_open.assert_called_once_with('/root/test_file.bin', 'rb')


# happy path - open_resource - Test that open_resource opens a file in text mode with specified encoding
def test_open_resource_text_mode_with_encoding(mock_open, blueprint_instance):
    blueprint_instance.root_path = '/root'
    with blueprint_instance.open_resource('test_file.txt', 'r', encoding='utf-8') as f:
        mock_open.assert_called_once_with('/root/test_file.txt', 'r', encoding='utf-8')


# edge case - __init__ - Test that Blueprint initialization with None values for optional parameters works correctly
def test_blueprint_initialization_with_none(mock_AppGroup):
    blueprint = Blueprint(
        name='test_blueprint',
        import_name='test_import',
        static_folder=None,
        static_url_path=None,
        template_folder=None,
        url_prefix=None,
        subdomain=None,
        url_defaults=None,
        root_path=None,
        cli_group=None
    )

    assert blueprint.name == 'test_blueprint'
    assert blueprint.import_name == 'test_import'
    assert blueprint.static_folder is None
    assert blueprint.static_url_path is None
    assert blueprint.template_folder is None
    assert blueprint.url_prefix is None
    assert blueprint.subdomain is None
    assert blueprint.url_defaults is None
    assert blueprint.root_path is None
    assert blueprint.cli_group is None


# edge case - get_send_file_max_age - Test that get_send_file_max_age returns correct seconds when SEND_FILE_MAX_AGE_DEFAULT is a timedelta
def test_get_send_file_max_age_timedelta_default(mock_current_app, blueprint_instance, mock_timedelta):
    mock_current_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = mock_timedelta(hours=12)
    max_age = blueprint_instance.get_send_file_max_age('test_file.txt')
    assert max_age == 43200


# edge case - send_static_file - Test that send_static_file works correctly when static_folder is set
def test_send_static_file_with_static_folder(mock_send_from_directory, blueprint_instance):
    blueprint_instance.static_folder = '/static'
    blueprint_instance.send_static_file('test_file.txt')
    mock_send_from_directory.assert_called_once_with('/static', 'test_file.txt', max_age=None)


# edge case - open_resource - Test that open_resource raises ValueError when an invalid mode is provided
def test_open_resource_invalid_mode(blueprint_instance):
    with pytest.raises(ValueError, match='Resources can only be opened for reading.'):
        blueprint_instance.open_resource('test_file.txt', 'w')


# edge case - open_resource - Test that open_resource uses default encoding when not specified in text mode
def test_open_resource_default_encoding(mock_open, blueprint_instance):
    blueprint_instance.root_path = '/root'
    with blueprint_instance.open_resource('test_file.txt', 'r') as f:
        mock_open.assert_called_once_with('/root/test_file.txt', 'r', encoding='utf-8')


