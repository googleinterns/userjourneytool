import os

import pytest
from selenium.webdriver.chrome.options import Options


def pytest_addoption(parser):
    parser.addoption(
        "--local", action="store_true", default=False, help="run tests locally"
    )


@pytest.fixture
def local(request):
    return request.config.getoption("--local")


def pytest_setup_options():
    options = Options()
    # This is a hack to determine if we're running in a CI environment
    # (i.e. Github Actions).
    # Since this is a pytest plugin hook defined by Dash,
    # we can't provide this function with additional arguments.
    # Ideally, we would read from the "local" fixture defined in the toplevel conftest.
    if "CI" in os.environ and os.environ["CI"] != "":
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    return options
