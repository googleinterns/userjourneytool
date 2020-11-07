import importlib
import pathlib
import sys
import threading
import time

import dash  # noqa
import dash_bootstrap_components as dbc
import pytest
from flask_caching import Cache
from selenium.webdriver.common.action_chains import ActionChains

import ujt.config
import ujt.dash_app
import ujt.main
import ujt.rpc_client
import ujt.server.server


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

    # Ideally, we want to use patch the following fields instead of assigning.
    # However, too many different places access the app and cache variables,
    # making patching the paths infeasible.
    ujt.dash_app.app = test_app
    ujt.dash_app.cache = test_cache

    ujt.config.REPORTING_SERVER_ADDRESS = "localhost:50052"
    ujt.config.AUTO_REFRESH_SLI = False
    ujt.config.CLEAR_CACHE_ON_STARTUP = True

    # Since python decorators are run at load/import time, we need to reload the callback modules
    # to register the callback with the test instance of the app.
    # Moreover, we need to reload the modules so they'll point to the correct app and cache object
    imported_modules = list(
        sys.modules.items()
    )  # conver to a list since additional items could be added when reloading?
    for module_name, module in imported_modules:
        if (
            "ujt" in module_name
            and "dash_app" not in module_name
            and "config" not in module_name
        ):
            print(module_name)
            importlib.reload(module)

    ready_event.wait()
    ujt.rpc_client.connect()

    ujt.main.initialize_ujt()
    ujt.dash_app.app.layout = ujt.components.get_layout()

    dash_duo.start_server(ujt.dash_app.app)
    yield dash_duo
    # can perform additional teardown actions here


def test_initial_ui(started_dash_duo, local):
    time.sleep(2)
    if not local:
        replace_canvas_percy_snapshot(started_dash_duo, "initial_ui")


def test_click_node(started_dash_duo, local):
    time.sleep(2)
    node_canvas = started_dash_duo.driver.find_element_by_css_selector(
        "[data-id=layer2-node]"
    )
    canvas_width, canvas_height = node_canvas.size["width"], node_canvas.size["height"]
    ActionChains(started_dash_duo.driver).move_to_element_with_offset(
        node_canvas, canvas_width * 0.55, canvas_height * 0.45
    ).click().perform()
    if not local:
        replace_canvas_percy_snapshot(started_dash_duo, "click_web_server")
