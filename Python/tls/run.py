import json
from utils import Utils
from session_manager import get_session  # Import from session_manager

# Load configuration and setup logging
config = Utils.load_config("config.json")
logger = Utils.setup_logger()

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
