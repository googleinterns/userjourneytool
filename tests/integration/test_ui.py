import pathlib
import textwrap
import threading
import time

import dash  # noqa

import ujt
import ujt.main
import ujt.server.server


def test_main_ui(dash_duo):
    # Start the reporting server
    server_thread = threading.Thread(
        target=ujt.server.server.serve,
        args=(
            "50052",
            pathlib.Path(__file__).parent.absolute() / "data",
        ),
        daemon=True,  # kill the thread when the test stops
    )
    server_thread.start()

    # initialize the ujt
    ujt.config.REPORTING_SERVER_ADDRESS = "localhost:50052"
    ujt.rpc_client.connect()
    ujt.main.initialize_ujt()
    ujt.dash_app.app.layout = ujt.components.get_layout()

    # API to start server on separate thread
    dash_duo.start_server(ujt.dash_app.app)

    # Sleep to allow cytoscape to render graph layout,
    # this seems like a hack.
    # Maybe we can subscribe to a javascript event?
    time.sleep(2)

    # The following is a major hack
    # Percy renders the DOM and doesn't use direct screenshots
    # It doesn't work with the canvas element that renders the cytoscape graph.
    # We replace the canvas that displays nodes with a screenshot so Percy can process it correctly.
    # See:
    # https://github.com/plotly/dash-cytoscape/blob/26df79a0d50fa29d409ccb4a6c7d49c9234fcbe2/tests/test_percy_snapshot.py
    # https://medium.com/nyc-planning-digital/visual-diffing-mapboxgl-edd2a85df4c4
    # https://github.com/OHIF/Viewers/issues/1082

    node_canvas = dash_duo.driver.find_element_by_css_selector("[data-id=layer2-node]")
    replace_canvas_with_image_script = textwrap.dedent(
        """
        var dataURL = arguments[0].toDataURL();
        arguments[0].outerHTML = `<img src=${dataURL} style="width: 100%"/>`;
        """
    )
    dash_duo.driver.execute_script(replace_canvas_with_image_script, node_canvas)

    dash_duo.percy_snapshot("main_ui", wait_for_callbacks=True)
