from flask import Flask, request

app = Flask(__name__)

@app.route('/callback')
def callback():
    # Okta redirects back here with authorization code
    authorization_code = request.args.get('code')
    # Handle the code and exchange it for tokens
    return f"Authorization code: {authorization_code}"

if __name__ == '__main__':
    app.run(port=8080)
