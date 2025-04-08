import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# Получение JWKS (JSON Web Key Set) от Clerk
JWKS_URL = "https://curious-polecat-50.clerk.accounts.dev/.well-known/jwks.json"

# Загружаем JWKS для проверки подписи токенов
def get_jwks():
    response = requests.get(JWKS_URL)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Unable to fetch JWKS")
    return response.json()

# Извлечение публичного ключа для проверки токена
def get_public_key(kid: str):
    jwks = get_jwks()
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return RSAAlgorithm.from_jwk(key)
    raise HTTPException(status_code=400, detail="Public key not found")

# Функция для проверки JWT
def verify_jwt(token: str):
    try:
        # Извлекаем "kid" из заголовка токена
        unverified_header = jwt.get_unverified_header(token)
        if unverified_header is None or "kid" not in unverified_header:
            raise HTTPException(status_code=400, detail="Invalid token header")

        # Получаем публичный ключ
        public_key = get_public_key(unverified_header["kid"])

        # Проверяем подпись токена и его содержимое
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="your-audience", issuer="https://api.clerk.com")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTClaimsError:
        raise HTTPException(status_code=401, detail="Invalid claims, please check the audience and issuer")
    except Exception:
        raise HTTPException(status_code=401, detail="Could not parse token")

# OAuth2PasswordBearer для интеграции с FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Зависимость для верификации токена в каждом эндпоинте
def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_jwt(token)
