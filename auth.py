from fastapi import HTTPException, Depends
import jwt
from config import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer

# OAuth2 password bearer flow for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def authorize(token: str = Depends(oauth2_scheme)):
    try:
        # token = token.split(" ")[1]  # Extract the token from the "Bearer" format
        # print("TOKEN", token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.InvalidTokenError, jwt.DecodeError, IndexError):
        raise HTTPException(status_code=400, detail="Token invalid")