import os
import base64
import hashlib
import secrets
import requests
import threading
import webbrowser
from flask import Flask, request

# == Конфиг ==
CLIENT_ID = '53468644'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://id.vk.com/authorize'
TOKEN_URL = 'https://id.vk.com/oauth2/token'
SCOPE = 'all'

# == Генерация PKCE ==
def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge

app = Flask(__name__)
code_verifier, code_challenge = generate_pkce_pair()

# == Ловим code ==
@app.route('/callback')
def callback():
    code = request.args.get('code')
    threading.Thread(target=exchange_code_for_token, args=(code,)).start()
    return '✅ Код получен! Можешь закрыть вкладку.'

# == Обмен code на токен ==
def exchange_code_for_token(code):
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': code,
        'code_verifier': code_verifier,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.ok:
        tokens = response.json()
        print("✅ Access Token:", tokens.get("access_token"))
        print("🔁 Refresh Token:", tokens.get("refresh_token"))
        print("⏱ Expires in:", tokens.get("expires_in"))
    else:
        print("❌ Ошибка получения токена:", response.text)
    os._exit(0)

# == Запускаем ==
def run():
    # Открываем браузер с запросом авторизации
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    webbrowser.open(f'{AUTH_URL}?{query}')
    # Запускаем локальный сервер
    app.run(port=5000)

if __name__ == '__main__':
    run()
