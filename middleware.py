from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ===========================
# UPDATE THESE VALUES
OKTA_DOMAIN = "https://integrator-4732892.okta.com"
CLIENT_ID = "0oaxt2ry3hahA5Mwd697"
CLIENT_SECRET = "nNb6FWbul9qhxG9W5HOh_0DsA4J_gRZ3T4ovUlnw1seW64Ig-QqwOpVdUijkoik9"
COPILOT_REDIRECT_URI = "https://token.botframework.com/.auth/web/redirect"
# ===========================

@app.route('/exchange-code', methods=['POST'])
def exchange_code():
    """
    Expects a JSON payload from Copilot Agent:
    {
        "code": "<authorization_code_from_okta>",
        "state": "<state_value_from_copilot>"
    }
    """
    data = request.get_json()
    code = data.get('code')
    state = data.get('state')

    if not code or not state:
        return jsonify({"error": "Missing 'code' or 'state' in request"}), 400

    token_url = f"{OKTA_DOMAIN}/oauth2/default/v1/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": COPILOT_REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        # Exchange code for tokens from Okta
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()
        tokens = response.json()

        # Send tokens back to Copilot Agent
        copilot_response = requests.post(
            COPILOT_REDIRECT_URI,
            json={
                "access_token": tokens.get("access_token"),
                "id_token": tokens.get("id_token"),
                "refresh_token": tokens.get("refresh_token"),
                "state": state
            }
        )

        if copilot_response.status_code != 200:
            return jsonify({
                "error": "Failed sending token to Copilot",
                "status": copilot_response.status_code,
                "body": copilot_response.text
            }), copilot_response.status_code

        return jsonify({"message": "Tokens successfully sent to Copilot Agent"})

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": str(e),
            "details": e.response.text if e.response else None
        }), 500


@app.route('/')
def home():
    return "Middleware is running."


if __name__ == "__main__":
    app.run(debug=True)
