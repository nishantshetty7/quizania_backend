from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve secret key from environment variable
SECRET_KEY = os.getenv("SECRET_KEY", default="")

# Algorithm used for signing JWT tokens
ALGORITHM = "HS256"
# Token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", default=15))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", default=60))

MONGO_URL = os.getenv("MONGO_URL", default="")

REDIS_HOST = os.getenv("REDIS_HOST", default="")
REDIS_PORT = os.getenv("REDIS_PORT", default="6379")
REDIS_USERNAME = os.getenv("REDIS_USERNAME", default="")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", default="")

REDIS_CONFIG = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "username": REDIS_USERNAME,
    "password": REDIS_PASSWORD,
    "decode_responses": True
}

# Ensure that the SECRET_KEY variable is set
if not SECRET_KEY:
    raise EnvironmentError("Secret key not found in environment variables.")
