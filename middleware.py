from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ===========================
# UPDATE THESE VALUES
OKTA_DOMAIN = "https://integrator-4732892.okta.com"
CLIENT_ID = "0oaxt2ry3hahA5Mwd697"
CLIENT_SECRET = "nNb6FWbul9qhxG9W5HOh_0DsA4J_gRZ3T4ovUlnw1seW64Ig-QqwOpVdUijkoik9"
REDIRECT_URI = "https://token.botframework.com/.auth/web/redirect"
# ===========================

@app.route('/')
def home():
    return "Middleware is running."

@app.route('/exchange-code', methods=['POST'])
def exchange_code():
    """
    Copilot Agent will POST {"code": "..."} here.
    This endpoint exchanges the code for tokens with Okta.
    """
    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({"error": "Missing authorization code"}), 400

    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"

    # Okta expects POST with x-www-form-urlencoded
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()
        # Return access_token, id_token, refresh_token back to Copilot Agent
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Failed exchanging code",
            "details": e.response.text if e.response else str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
