import os
import textwrap

from selenium.webdriver.chrome.options import Options


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


def replace_canvas_percy_snapshot(started_dash_duo, snapshot_name):
    # The following is a major hack.
    # Percy renders the DOM and doesn't use direct screenshots
    # It doesn't work with the canvas element that renders the cytoscape graph.
    # We replace the canvas that displays nodes with a screenshot so Percy can process it correctly.
    # See:
    # https://github.com/plotly/dash-cytoscape/blob/26df79a0d50fa29d409ccb4a6c7d49c9234fcbe2/tests/test_percy_snapshot.py
    # https://medium.com/nyc-planning-digital/visual-diffing-mapboxgl-edd2a85df4c4
    # https://github.com/OHIF/Viewers/issues/1082

    node_canvas = started_dash_duo.driver.find_element_by_css_selector(
        "[data-id=layer2-node]"
    )
    replace_canvas_with_image_script = textwrap.dedent(
        """
        var dataURL = arguments[0].toDataURL();
        arguments[0].outerHTML = `<img src=${dataURL} style="width: 100%"/>`;
        """
    )
    started_dash_duo.driver.execute_script(
        replace_canvas_with_image_script, node_canvas
    )
    started_dash_duo.percy_snapshot(snapshot_name, wait_for_callbacks=True)
