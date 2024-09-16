import json
import logging

class Utils:
    @staticmethod
    def load_config(config_file="config.json"):
        """Loads configuration from config.json."""
        with open(config_file, 'r') as f:
            return json.load(f)

    @staticmethod
    def setup_logger():
        """Sets up a reusable logger."""
        logger = logging.getLogger("app_logger")
        logger.setLevel(logging.DEBUG)

        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler("app.log")

        # Create formatters and add to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    @staticmethod
    def get_tls_options(config):
        """Gets TLS options based on the config."""
        tls_config = config.get("tls_validation", {})
        if tls_config.get("enabled"):
            if tls_config.get("verify", True):
                return {
                    "verify": tls_config.get("caCert", True),  # Use system's trust store if no caCert provided
                    "cert": (tls_config.get("clientCert"), tls_config.get("clientKey"))
                }
            else:
                return {"verify": False}
        return {}

    @staticmethod
    def get_target_url(config, endpoint=""):
        """Builds the target URL based on protocol, ip, and api_port."""
        protocol = config["target"].get("protocol", "https")
        ip = config["target"].get("ip", "localhost")
        port = config["target"].get("api_port", 443)
        return f"{protocol}://{ip}:{port}{endpoint}"
