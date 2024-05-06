from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client["quizania"]
users_collection = db["users"]

users_collection.create_index([("email", 1)], unique=True)