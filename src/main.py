from quart import Quart, request, jsonify, Response
import asyncio

from client.orchestrator import orchestrator

# initiate quart app
app = Quart(__name__)

# expose the model to open webUI
@app.route("/chat/models", methods=["GET"])
async def list_models():
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "Daryl's Personal Assistant",
                "object": "model",
                "owned_by": "me",
            }
        ]
    })

# create endpoint to chat with the agent
@app.route("/chat", methods=["POST"])
async def chat():
    data = await request.get_json()
    user_id = data.get("user", "anon")
    question = data.get("question", "")

    async def generate():
        async for chunk in orchestrator(user_id, question):
            yield chunk

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)