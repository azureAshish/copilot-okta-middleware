from flask import Flask, request, jsonify, redirect
import requests
import urllib.parse

app = Flask(__name__)

# ===========================
# UPDATE THESE VALUES
OKTA_DOMAIN = "https://integrator-4732892.okta.com"
CLIENT_ID = "0oaxt2ry3hahA5Mwd697"
CLIENT_SECRET = "nNb6FWbul9qhxG9W5HOh_0DsA4J_gRZ3T4ovUlnw1seW64Ig-QqwOpVdUijkoik9"
REDIRECT_URI = "https://copilot-okta-middleware.onrender.com/auth/callback"
COPILOT_REDIRECT = "https://token.botframework.com/.auth/web/redirect"
# ===========================

@app.route("/")
def home():
    return "Middleware is running."


# -------------------------------------------------------
# ✨ MAIN ENDPOINT: /auth/callback
# Okta calls this with: ?code=xxx&state=yyy
# -------------------------------------------------------
@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({"error": "Missing 'code' in query params"}), 400

    # -------- STEP 1: Exchange code for tokens ----------
    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        token_response = requests.post(token_url, data=payload, headers=headers)
        token_response.raise_for_status()
        tokens = token_response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Error exchanging authorization code with Okta",
            "message": str(e),
            "okta_response": e.response.text if e.response else None
        }), 500

    # -------- STEP 2: Redirect tokens back to Copilot ------
    # Copilot ONLY accepts GET redirect — NOT POST
    params = {
        "access_token": tokens.get("access_token", ""),
        "id_token": tokens.get("id_token", ""),
        "refresh_token": tokens.get("refresh_token", ""),
        "state": state
    }

    redirect_query = urllib.parse.urlencode(params)
    redirect_url = f"{COPILOT_REDIRECT}?{redirect_query}"

    return redirect(redirect_url, code=302)


# -------------------------------------------------------
# For debugging only (Copilot does not use this)
# -------------------------------------------------------
@app.route("/exchange-code", methods=["POST"])
def exchange_code():
    """Optional helper endpoint for manual testing."""
    data = request.get_json()
    code = data.get("code")

    if not code:
        return jsonify({"error": "Missing authorization code"}), 400

    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": str(e),
            "details": e.response.text if e.response else None
        }), 500


# Render runs: gunicorn middleware:app
