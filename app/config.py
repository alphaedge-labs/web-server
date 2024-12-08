# module imports
import os
from dotenv import load_dotenv

load_dotenv()

# server variables
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

# cache database
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# mongo connection string
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')