import pytest
from unittest import mock
from src.flask.ctx import _AppCtxGlobals, AppContext, RequestContext, after_this_request, copy_current_request_context, has_request_context, has_app_context

@pytest.fixture
def mock_app_context():
    app_context = mock.Mock(spec=AppContext)
    app_context.app = mock.Mock()
    app_context.url_adapter = mock.Mock()
    app_context.g = _AppCtxGlobals()
    app_context._cv_tokens = []
    return app_context

@pytest.fixture
def mock_request_context():
    request_context = mock.Mock(spec=RequestContext)
    request_context.app = mock.Mock()
    request_context.request = mock.Mock()
    request_context.url_adapter = mock.Mock()
    request_context.flashes = []
    request_context.session = mock.Mock()
    request_context._after_request_functions = []
    request_context._cv_tokens = []
    return request_context

@pytest.fixture
def mock_after_this_request():
    mock_func = mock.Mock()
    with mock.patch('src.flask.ctx._cv_request.get', return_value=mock_request_context()):
        yield after_this_request(mock_func)

@pytest.fixture
def mock_copy_current_request_context():
    mock_func = mock.Mock()
    with mock.patch('src.flask.ctx._cv_request.get', return_value=mock_request_context()):
        yield copy_current_request_context(mock_func)

@pytest.fixture
def mock_has_request_context():
    with mock.patch('src.flask.ctx._cv_request.get', return_value=mock_request_context()):
        yield has_request_context()

@pytest.fixture
def mock_has_app_context():
    with mock.patch('src.flask.ctx._cv_app.get', return_value=mock_app_context()):
        yield has_app_context()

@pytest.fixture
def mock_app_ctx_globals():
    app_globals = _AppCtxGlobals()
    app_globals.__setattr__('existing_attr', 'attr_value')
    with mock.patch.object(_AppCtxGlobals, '__getattr__', return_value='attr_value'):
        yield app_globals

@pytest.fixture
def mock_request_context_methods():
    with mock.patch.object(RequestContext, 'push') as mock_push, \
         mock.patch.object(RequestContext, 'pop') as mock_pop:
        yield mock_push, mock_pop

@pytest.fixture
def mock_app_context_methods():
    with mock.patch.object(AppContext, 'push') as mock_push, \
         mock.patch.object(AppContext, 'pop') as mock_pop:
        yield mock_push, mock_pop

# happy path - after_this_request - Test that 'after_this_request' appends a function to the context's after_request_functions list
def test_after_this_request_appends_function(mock_after_this_request, mock_request_context):
    assert mock_request_context._after_request_functions[-1] == mock_after_this_request



# happy path - copy_current_request_context - Test that 'copy_current_request_context' decorates a function and retains the request context
def test_copy_current_request_context_decorates_function(mock_copy_current_request_context):
    assert callable(mock_copy_current_request_context)



# happy path - has_request_context - Test that 'has_request_context' returns True when a request context is active
def test_has_request_context_returns_true(mock_has_request_context):
    assert mock_has_request_context is True



# happy path - has_app_context - Test that 'has_app_context' returns True when an app context is active
def test_has_app_context_returns_true(mock_has_app_context):
    assert mock_has_app_context is True



# happy path - __getattr__ - Test that '__getattr__' retrieves an existing attribute from the _AppCtxGlobals instance
def test_getattr_retrieves_existing_attribute(mock_app_ctx_globals):
    assert mock_app_ctx_globals.existing_attr == 'attr_value'



# edge case - after_this_request - Test that 'after_this_request' raises RuntimeError if no request context is active
def test_after_this_request_raises_runtimeerror_no_context():
    with pytest.raises(RuntimeError):
        after_this_request(lambda x: x)



# edge case - copy_current_request_context - Test that 'copy_current_request_context' raises RuntimeError if no request context is active
def test_copy_current_request_context_raises_runtimeerror_no_context():
    with pytest.raises(RuntimeError):
        copy_current_request_context(lambda x: x)



# edge case - __getattr__ - Test that '__getattr__' raises AttributeError when accessing a non-existent attribute
def test_getattr_raises_attributeerror_nonexistent(mock_app_ctx_globals):
    with pytest.raises(AttributeError):
        _ = mock_app_ctx_globals.nonexistent_attr



# edge case - pop - Test that 'pop' method in RequestContext raises AssertionError when popping wrong context
def test_request_context_pop_raises_assertionerror_wrong_context(mock_request_context_methods, mock_request_context):
    mock_request_context_methods[1].side_effect = AssertionError
    with pytest.raises(AssertionError):
        mock_request_context.pop()



# edge case - pop - Test that 'pop' method in AppContext raises AssertionError when popping wrong context
def test_app_context_pop_raises_assertionerror_wrong_context(mock_app_context_methods, mock_app_context):
    mock_app_context_methods[1].side_effect = AssertionError
    with pytest.raises(AssertionError):
        mock_app_context.pop()



