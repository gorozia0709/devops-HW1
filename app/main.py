from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

tasks = {}
next_id = 1


def reset_store():
    global tasks, next_id
    tasks = {}
    next_id = 1


@app.route("/")
def index():
    return render_template("index.html")



@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    done_filter = request.args.get("done")
    result = list(tasks.values())
    if done_filter is not None:
        want_done = done_filter.lower() == "true"
        result = [t for t in result if t["done"] == want_done]
    return jsonify({"tasks": result, "total": len(result)}), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
    global tasks, next_id
    body = request.get_json()

    if not body or not body.get("title", "").strip():
        return jsonify({"error": "title is required"}), 400

    task = {
        "id":       next_id,
        "title":    body["title"].strip(),
        "priority": body.get("priority", "medium"),
        "done":     False,
    }
    tasks[next_id] = task
    next_id += 1
    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": f"Task {task_id} not found"}), 404

    body = request.get_json() or {}

    if "title" in body:
        if not body["title"].strip():
            return jsonify({"error": "title cannot be empty"}), 400
        task["title"] = body["title"].strip()

    if "done" in body:
        if not isinstance(body["done"], bool):
            return jsonify({"error": "done must be a boolean"}), 400
        task["done"] = body["done"]

    if "priority" in body:
        if body["priority"] not in ("low", "medium", "high"):
            return jsonify({"error": "priority must be low, medium, or high"}), 400
        task["priority"] = body["priority"]

    return jsonify(task), 200


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = tasks.pop(task_id, None)
    if not task:
        return jsonify({"error": f"Task {task_id} not found"}), 404
    return jsonify({"message": f"Task {task_id} deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)