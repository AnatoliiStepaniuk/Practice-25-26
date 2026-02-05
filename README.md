# Users API

A Flask REST API for managing users with JWT authentication and Swagger documentation.

## Running with Docker

1. Build the image:

```bash
docker build -t users-api .
```

2. Run the container:

```bash
docker run -p 5050:5050 \
  -e API_KEY_HASH='$2b$12$54NpbieqBRI2AYIw8C10rOWP2yWZ5DEDluzRttrUjdJqPdLAStsxC' \
  -e JWT_SECRET='your-secret-key' \
  -e JWT_EXPIRATION_MINUTES=60 \
  users-api
```

The API key for the hash above is `secret123`. Generate a new hash for production:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
```

The server starts on `http://localhost:5050`.

## Running locally (without Docker)

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file:

```
API_KEY_HASH=$2b$12$54NpbieqBRI2AYIw8C10rOWP2yWZ5DEDluzRttrUjdJqPdLAStsxC
JWT_SECRET=your-secret-key
JWT_EXPIRATION_MINUTES=60
```

3. Run the app:

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
