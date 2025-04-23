import requests
import hashlib
import base64
import secrets

# 1. Сгенерировать code_verifier и code_challenge
code_verifier = secrets.token_urlsafe(64)

code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip("=")

client_id = '53468644'
redirect_uri = 'https://oauth.vk.com/blank.html'

# 2. Сформировать URL для ручного перехода
auth_url = (
    f"https://id.vk.com/authorize?"
    f"client_id={client_id}"
    f"&redirect_uri={redirect_uri}"
    f"&response_type=code"
    f"&code_challenge={code_challenge}"
    f"&code_challenge_method=S256"
)

print("Перейди по ссылке для авторизации:")
print(auth_url)

# 3. После авторизации VK перекинет на redirect_uri?code=XXXX
# Вставь полученный `code` вручную:
code = input("Введи полученный код из URL: ")
device_id = input("Введи полученный device_id URL: ")

# 4. Обменять code на access_token
token_url = "https://id.vk.com/oauth2/auth"

data = {
    'grant_type': 'authorization_code',
    'code': code,
    'client_id': client_id,
    'device_id': device_id,
    'redirect_uri': redirect_uri,
    'code_verifier': code_verifier,
}

response = requests.post(token_url, data=data)

if response.ok:
    tokens = response.json()
    print("Токен получен:")
    print(tokens)
else:
    print("Ошибка:")
    print(response.status_code, response.text)
