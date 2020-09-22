# User Journey Tool
![CI Badge](https://github.com/googleinterns/userjourneytool/workflows/Python%20package/badge.svg)

User Journey Tool simplifies debugging by providing an overview of an application's status and dependency topology from a user journey-based perspective.

## Development Setup

1. Create a venv.

        python3 -m venv /venv/path

2. Activate the venv.

        source /venv/path/bin/activate

3. Install dependencies.

        pip install -r requirements.txt

4. Compile protobufs.

        ./generate_protos

5. Install generated protobufs as a package.

        pip install --editable generated/

6. Run the tool.

        python3 -m ujt.app

7. Run tests.

        mypy --cov=ujt

8. Before committing, lint and type check the code.

        ./lint

## License
[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)
