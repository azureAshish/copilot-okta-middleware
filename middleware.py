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


@app.route("/auth/callback")
def okta_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "Missing 'code' in callback", 400

    # Exchange code for tokens
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

    # POST tokens to Copilot
    copilot_response = requests.post(
        COPILOT_REDIRECT,
        json=tokens,
        headers={"Content-Type": "application/json"}
    )

    if copilot_response.status_code != 200:
        return f"Failed to forward tokens to Copilot: {copilot_response.text}", 500

    # DO NOT REDIRECT
    return """
        <h2>Login successful!</h2>
        <p>You may now close this window and return to Copilot.</p>
    """
