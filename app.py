import json
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)

API_KEY = os.environ["API_KEY"]

Swagger(app, template={
    "info": {
        "title": "Users API",
        "version": "1.0",
    },
    "securityDefinitions": {
        "ApiKey": {
            "type": "apiKey",
            "name": "ApiKey",
            "in": "header",
            "description": "Enter your API key, e.g.: supersecret123",
        },
    },
    "security": [{"ApiKey": []}],
})


@app.before_request
def check_auth():
    if request.path.startswith(("/apidocs", "/flasgger", "/apispec")):
        return
    token = request.headers.get("ApiKey", "")
    if token != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

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
    app.run(debug=True, port=5050)
