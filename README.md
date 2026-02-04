# Users API

A Flask REST API for managing users with bcrypt-based API key authentication and Swagger documentation.

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install flask flasgger python-dotenv bcrypt requests pytest
```

2. Create a `.env` file with a bcrypt hash of your API key:

```
API_KEY_HASH=<your_bcrypt_hash>
```

To generate a hash for a given password:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
```

## Running the app

```bash
python app.py
```

The server starts on `http://127.0.0.1:5050`.

## Swagger UI

Once the app is running, open [http://127.0.0.1:5050/apidocs](http://127.0.0.1:5050/apidocs).

Use the **Authorize** button in Swagger UI and enter your plaintext API key (e.g. `secret123`) to authenticate requests.

## Running integration tests

Tests start a real Flask server on port 5051 and make HTTP requests against it.

```bash
pytest test_app.py -v
```

By default the tests use `secret123` as the API key. To override, set the `TEST_API_KEY` environment variable:

```bash
TEST_API_KEY=mykey pytest test_app.py -v
```
