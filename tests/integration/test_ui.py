import pathlib
import textwrap
import threading
import time

import dash  # noqa

import ujt.dash_app
import ujt.config
import ujt.server.server
from flask_caching import Cache
from unittest.mock import patch
import pytest

import dash_bootstrap_components as dbc


@pytest.fixture
def ready_event():
    return threading.Event()

@pytest.fixture
def reporting_server_thread(ready_event):
    """ Sets up and tears down the example reporting server. """
    stop_event = threading.Event()
    stop_completed_event = threading.Event()
    server_thread = threading.Thread(
        target=ujt.server.server.serve,
        args=(
            "50052",
            pathlib.Path(__file__).parent.absolute() / "data",
            ready_event,
            stop_event,
            stop_completed_event,
        ),
        # stop process when only server thread exists (after test completed)
        daemon=True,
    )
    server_thread.start()
    yield server_thread
    stop_event.set()
    stop_completed_event.wait()

@pytest.fixture
def started_dash_duo(dash_duo, reporting_server_thread, ready_event):
    test_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    test_cache = Cache()
    test_cache.init_app(
        test_app.server,
        config={
            "CACHE_TYPE": "filesystem",
            "CACHE_DIR": "cache_dir",
            "CACHE_DEFAULT_TIMEOUT": 0,
            "CACHE_THRESHOLD": 0,
        },
    )

    TEST_REPORTING_SERVER_ADDRESS = "localhost:50052"
    
    with patch("ujt.dash_app.app", test_app), \
        patch("ujt.dash_app.cache", test_cache), \
        patch("ujt.config.REPORTING_SERVER_ADDRESS", TEST_REPORTING_SERVER_ADDRESS), \
        patch("ujt.config.AUTO_REFRESH_SLI", False), \
        patch("ujt.config.CLEAR_CACHE_ON_STARTUP", True):
        # wait for reporting server to start
        ready_event.wait()
        import ujt.rpc_client
        ujt.rpc_client.connect()

        # hack
        import ujt.main as ujt_main
        ujt_main.initialize_ujt()
        ujt.dash_app.app.layout = ujt.components.get_layout()
        
        dash_duo.start_server(ujt.dash_app.app)
        yield dash_duo
    

def test_initial_ui(started_dash_duo, local):
    time.sleep(2)
    if not local:
        replace_canvas_percy_snapshot(started_dash_duo, "initial_ui")



def test_ensure_server_stopped():
    TEST_REPORTING_SERVER_ADDRESS = "localhost:50052"
    
    with patch("ujt.config.REPORTING_SERVER_ADDRESS", TEST_REPORTING_SERVER_ADDRESS), \
        pytest.raises(Exception):
        import ujt.rpc_client
        ujt.rpc_client.connect()
        ujt.rpc_client.get_nodes()
        