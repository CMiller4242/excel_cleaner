from dotenv import load_dotenv
import os

load_dotenv()

print("MONGODB_URI:", os.getenv('MONGODB_URI'))
print("SECRET_KEY:", os.getenv('SECRET_KEY'))