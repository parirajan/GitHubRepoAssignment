import json
import logging

class Utils:
    @staticmethod
    def load_config(config_file="config.json"):
        """Loads configuration from config.json file."""
        with open(config_file, 'r') as f:
            return json.load(f)

    @staticmethod
    def get_full_url(config, category, endpoint_name):
        """Builds the full URL based on the config file and the given endpoint category."""
        protocol = config["connection"]["protocol"]
        host = config["connection"]["host"]
        port = config["connection"]["port"]
        endpoint = config["endpoints"][category].get(endpoint_name, {}).get("url", "")
        return f"{protocol}://{host}:{port}{endpoint}"

    @staticmethod
    def get_request_type(config, category, endpoint_name):
        """Gets the request type (GET/POST) for a given endpoint."""
        return config["endpoints"][category].get(endpoint_name, {}).get("request_type", "GET")

    @staticmethod
    def get_tls_options(config):
        """Gets the TLS verification settings and certificate options."""
        tls_verify = config.get("tls_verify", True)
        
        # If tls_verify is False, no cert is sent, and verify is set to False
        if not tls_verify:
            return {
                "verify": False  # Disable TLS verification
            }
        
        # If tls_verify is True, cert is sent with CA cert for verification
        cert = (config["tls_options"]["cert"], config["tls_options"]["key"])
        ca_file = config["tls_options"].get("ca_file", True)  # Use CA file if specified, otherwise True (default system trust store)

        return {
            "verify": ca_file,  # Path to CA cert or True to use default trust store
            "cert": cert        # Send client cert and key
        }

class Logger:
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
