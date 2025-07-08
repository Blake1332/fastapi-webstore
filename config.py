import os
from starlette.config import Config
from dotenv import load_dotenv

# check if .env file exists
config = Config(".env")

# Loads from .env file
load_dotenv()

# Database 
DATABASE_URL = os.getenv("DATABASE_URL")

# Application 
SECRET_KEY = os.getenv("SECRET_KEY")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))  

# GitLab OAuth 
GITLAB_CLIENT_ID = os.getenv("GITLAB_CLIENT_ID")
GITLAB_CLIENT_SECRET = os.getenv("GITLAB_CLIENT_SECRET")
GITLAB_DOMAIN = os.getenv("GITLAB_DOMAIN")

# Email 
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT"))
MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
