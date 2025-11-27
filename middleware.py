from flask import Flask, request, jsonify, redirect
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# ===========================
# UPDATE THESE VALUES
OKTA_DOMAIN = "https://integrator-4732892.okta.com"
CLIENT_ID = "0oaxt2ry3hahA5Mwd697"
CLIENT_SECRET = "nNb6FWbul9qhxG9W5HOh_0DsA4J_gRZ3T4ovUlnw1seW64Ig-QqwOpVdUijkoik9"

# >>> Your middleware callback URL <<<
MIDDLEWARE_REDIRECT_URI = "https://copilot-okta-middleware.onrender.com/auth/callback"

# >>> Copilot fixed redirect <<<
COPILOT_REDIRECT = "https://token.botframework.com/.auth/web/redirect"
# ===========================


# ---------------------------------------------------------------------
# 1️⃣ This is the callback Okta calls: /auth/callback
# ---------------------------------------------------------------------
@app.route("/auth/callback")
def okta_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "Missing 'code' in callback", 400

    app.logger.info(f"Received code from Okta: {code}")

    # ---------- Exchange Code for Token ----------
    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": MIDDLEWARE_REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(token_url, data=payload, headers=headers)

    if token_response.status_code != 200:
        return f"Token exchange failed: {token_response.text}", 500

    tokens = token_response.json()
    app.logger.info("Token exchange successful.")

    # ---------- Forward token to Copilot ----------
    try:
        copilot_response = requests.post(
            COPILOT_REDIRECT,
            json=tokens,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        return f"Failed to post tokens to Copilot: {str(e)}", 500

    app.logger.info("Token forwarded to Copilot.")

    # Copilot expects a redirect back to itself
    return redirect(COPILOT_REDIRECT)


# ---------------------------------------------------------------------
# 2️⃣ Legacy endpoint (still useful for debugging)
# ---------------------------------------------------------------------
@app.route('/exchange-code', methods=['POST'])
def exchange_code_direct():
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({"error": "Missing authorization code"}), 400

    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": MIDDLEWARE_REDIRECT_URI,
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


@app.route("/")
def home():
    return "Middleware is running. /auth/callback is ready."


# Render runs: gunicorn middleware:app
