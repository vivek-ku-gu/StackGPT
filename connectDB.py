from dotenv import load_dotenv
from pymongo import MongoClient
import os
load_dotenv()
MONGO_URI = os.environ["MONGO_URI"]
client = MongoClient(MONGO_URI)
INDEX_NAME = "vector_index"
# Access database
db = client["StackGPT"]

# Access or create collection
collection = db.get_collection("POC")