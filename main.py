from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

from model import User, UserLogin, GoogleLogin, UserResponse
from database import users_collection

from config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES, ALGORITHM
from auth import authorize
import json

app = FastAPI()

# Configure CORS settings
origins = [
    "http://localhost:3000",  # Replace with your frontend origin
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash password using bcrypt
def hash_password(password: str):
    return pwd_context.hash(password)


# Verify plaintext password against hashed password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


# Generate JWT token
def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_tokens(user: dict):
    email = user.get("email", None)
    image = user["image"] if user.get("image", "") else user.get("profile_pic", "")
    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")
    phone_number = user.get("phone_number", "")
    token_data = dict({"email": email})
    token_data['image'] = image
    token_data['phone_number'] = phone_number
    token_data['name'] = f"{first_name} {last_name}"
    access_token = create_token(data=token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_token(data=token_data, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    return access_token, refresh_token


# Register new user
@app.post("/register", response_model=UserResponse)
async def register_user(user_data: User):
    email = user_data.email
    password = user_data.password
    first_name = user_data.first_name 

    if not email or not password or not first_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email, password and first name are required.")

    user = await users_collection.find_one({"email": user_data.email})
    if user:
        if not user["is_active"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already registered but need to verify your account. Please check your mail or resend verification email")
        
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ID Taken")
    
    hashed_password = hash_password(user_data.password)
    new_user = dict(user_data)
    new_user["password"] = hashed_password
    await users_collection.insert_one(new_user)
    return {"message": "User Registered Successfully"}


# Authenticate user and return JWT token
@app.post("/login")
async def login(form_data: UserLogin):
    user = await users_collection.find_one({"email": form_data.email})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user["auth_type"] == "google":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="""It looks like you've previously registered using social authentication. Please use the same social authentication method (Google) to log in.""")

    access_token, refresh_token = get_tokens(user)

    response = Response(json.dumps({"access_token": access_token}))
    response.set_cookie("jwt", refresh_token, 
                        httponly=True, 
                        secure=True, 
                        samesite=None,
                        max_age=(60 * 60))
    return response


@app.post("/google/login")
async def google_login(request_data: GoogleLogin):
    email = request_data.email
    first_name = request_data.given_name
    last_name = request_data.family_name
    image = request_data.picture
    user_data = {"email": email, "first_name": first_name, 
                 "last_name": last_name, "profile_pic": image}

    if not email:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required."
            )

    user = await users_collection.find_one({"email": email})

    if not user:
        try:
            hashed_password = hash_password(f"{email}_{first_name}")
            new_user = dict(user_data)
            new_user["password"] = hashed_password
            new_user.update({"is_active": True, "auth_type": "google"})
            user = User(**new_user).model_dump()
            await users_collection.insert_one(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    if user["auth_type"] == "regular":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already registered with password authentication. Please contact support for any assistance.")

    access_token, refresh_token = get_tokens(user)

    response = Response(json.dumps({"access_token": access_token}))
    response.set_cookie("jwt", refresh_token, 
                        httponly=True, 
                        secure=True, 
                        samesite=None,
                        max_age=(60 * 60))
    return response

@app.get("/logout")
async def logout(request: Request):
    refresh_token = request.cookies.get('jwt', None)
    # If the refresh token is not present, return a 204 No Content response
    if not refresh_token:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('jwt')
        return response
    except Exception as e:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Test endpoint for protected resources
@app.get("/protected")
async def protected(payload: dict = Depends(authorize)):
    print(payload)
    return "works"
