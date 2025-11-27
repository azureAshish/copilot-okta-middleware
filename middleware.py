from flask import Flask, request, jsonify, redirect
import urllib.parse

app = Flask(__name__)

# ============ CONFIG ============
REDIRECT_URI = "https://copilot-okta-middleware.onrender.com/auth/callback"
COPILOT_REDIRECT = "https://token.botframework.com/.auth/web/redirect"
# =================================

@app.route("/")
def home():
    return "Middleware is running."

@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({"error": "Missing code"}), 400

    # Copilot expects ONLY ?code=xxx&state=yyy
    params = {
        "code": code,
        "state": state
    }
    redirect_query = urllib.parse.urlencode(params)
    url = f"{COPILOT_REDIRECT}?{redirect_query}"

    return redirect(url, code=302)
