import json
import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)

API_KEY_HASH = os.environ["API_KEY_HASH"].encode()
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_EXPIRATION_MINUTES = int(os.environ["JWT_EXPIRATION_MINUTES"])

Swagger(app, template={
    "info": {
        "title": "Users API",
        "version": "1.0",
    },
    "securityDefinitions": {
        "JWT": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Paste your JWT token (obtained from /login)",
        },
    },
    "security": [{"JWT": []}],
})


@app.route("/login", methods=["POST"])
def login():
    """Exchange an API key for a JWT token
    ---
    security: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          required:
            - api_key
          properties:
            api_key:
              type: string
              example: your-secret-key
    responses:
      200:
        description: JWT token
        schema:
          properties:
            token:
              type: string
      401:
        description: Invalid API key
    """
    data = request.get_json()
    if not data or "api_key" not in data:
        return jsonify({"error": "api_key is required"}), 400

    if not bcrypt.checkpw(data["api_key"].encode(), API_KEY_HASH):
        return jsonify({"error": "Invalid API key"}), 401

    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return jsonify({"token": token})


@app.before_request
def check_auth():
    if request.path.startswith(("/apidocs", "/flasgger", "/apispec", "/login")):
        return
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return jsonify({"error": "Unauthorized"}), 401
    token = auth_header.removeprefix("Bearer ")
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

DATA_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def next_id(users):
    if not users:
        return 1
    return max(u["id"] for u in users) + 1


@app.route("/users", methods=["GET"])
def get_users():
    """Get all users
    ---
    responses:
      200:
        description: A list of users
        schema:
          type: array
          items:
            properties:
              id:
                type: integer
              name:
                type: string
              email:
                type: string
              age:
                type: integer
    """
    return jsonify(load_users())


@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          required:
            - name
            - email
            - age
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: john@example.com
            age:
              type: integer
              example: 25
    responses:
      201:
        description: User created
      400:
        description: Missing required fields
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    missing = [f for f in ("name", "email", "age") if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    users = load_users()
    user = {
        "id": next_id(users),
        "name": data["name"],
        "email": data["email"],
        "age": data["age"],
    }
    users.append(user)
    save_users(users)
    return jsonify(user), 201


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get a user by ID
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: A user object
      404:
        description: User not found
    """
    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """Update a user
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          properties:
            name:
              type: string
              example: Jane Doe
            email:
              type: string
              example: jane@example.com
            age:
              type: integer
              example: 30
    responses:
      200:
        description: User updated
      404:
        description: User not found
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    if "name" in data:
        user["name"] = data["name"]
    if "email" in data:
        user["email"] = data["email"]
    if "age" in data:
        user["age"] = data["age"]

    save_users(users)
    return jsonify(user)


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: User deleted
      404:
        description: User not found
    """
    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    users = [u for u in users if u["id"] != user_id]
    save_users(users)
    return jsonify({"message": f"User {user_id} deleted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5050)
