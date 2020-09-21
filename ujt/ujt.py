""" Main entry point for UJT. """

from .dash_app import app
from . import callbacks

if __name__ == "__main__":
    app.run_server(debug=True)
