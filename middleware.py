from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ===========================
# 🔧 UPDATE THESE VALUES
OKTA_DOMAIN = "https://integrator-4732892.okta.com"
CLIENT_ID = "0oaxt2ry3hahA5Mwd697"
CLIENT_SECRET = "nNb6FWbul9qhxG9W5HOh_0DsA4J_gRZ3T4ovUlnw1seW64Ig-QqwOpVdUijkoik9"
MIDDLEWARE_CALLBACK = "https://copilot-okta-middleware.onrender.com/auth/callback"
COPILOT_REDIRECT = "https://token.botframework.com/.auth/web/redirect"
# ===========================


@app.route("/")
def home():
    return "Middleware is running."


# -------------------------------------------------------
# STEP 1 — Okta redirects user HERE with ?code=xxxx
# -------------------------------------------------------
@app.route("/auth/callback", methods=["GET"])
def okta_callback():

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "Missing code parameter in Okta redirect", 400

    # Exchange code for tokens via Okta API
    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": MIDDLEWARE_CALLBACK,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    okta_response = requests.post(token_url, data=payload, headers=headers)

    if okta_response.status_code != 200:
        return f"""
        <h2>❌ Token exchange failed</h2>
        <pre>Status: {okta_response.status_code}</pre>
        <pre>{okta_response.text}</pre>
        """, 500

    token_payload = okta_response.json()

    # -------------------------------------------------------
    # STEP 2 — Send tokens to Copilot
    # -------------------------------------------------------
    copilot_response = requests.post(
        COPILOT_REDIRECT,
        json=token_payload,
        headers={"Content-Type": "application/json"}
    )

    if copilot_response.status_code != 200:
        return f"""
        <h2>❌ Failed sending token to Copilot</h2>
        <pre>Status: {copilot_response.status_code}</pre>
        <pre>{copilot_response.text}</pre>
        """, 500

    # -------------------------------------------------------
    # STEP 3 — Success page
    # -------------------------------------------------------
    return """
    <html>
    <body>
        <h1>✅ Login Successful</h1>
        <p>You can close this window and return to your Copilot Agent.</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(port=5000)
