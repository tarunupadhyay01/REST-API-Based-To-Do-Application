from flask import Flask, jsonify, request, send_from_directory
import sqlite3
from pathlib import Path

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todos.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.get("/style.css")
def stylesheet():
    return send_from_directory(BASE_DIR, "style.css")

@app.get("/api/todos")
def get_todos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM todos ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@app.post("/api/todos")
def add_todo():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Task title is required."}), 400
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO todos (title) VALUES (?)", (title,))
        todo = conn.execute("SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(dict(todo)), 201

@app.patch("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        current = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if current is None:
            return jsonify({"error": "Task not found."}), 404
        title = str(data.get("title", current["title"])).strip()
        completed = int(bool(data.get("completed", current["completed"])))
        if not title:
            return jsonify({"error": "Task title cannot be empty."}), 400
        conn.execute(
            "UPDATE todos SET title = ?, completed = ? WHERE id = ?",
            (title, completed, todo_id)
        )
        updated = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return jsonify(dict(updated))

@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"message": "Task deleted."})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
