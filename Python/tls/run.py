import json
from utils import Utils, Logger
from get_session import get_session

# Load configuration and setup logging
config = Utils.load_config("config.json")
logger = Logger.setup_logger()

# Get session and login payload from getSession
session_headers = get_session(config)

# Check if session is successfully created
if session_headers:
    logger.info("Session established successfully!")
    print("Session established successfully!")
    print(f"Session Headers: {session_headers}")
else:
    logger.error("Failed to establish session.")
    print("Failed to establish session.")
