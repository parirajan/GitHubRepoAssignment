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

        # Only include cert if tls_verify is true
        cert = (config["tls_options"]["cert"], config["tls_options"]["key"]) if tls_verify else None
        ca_file = config["tls_options"].get("ca_file") if tls_verify else None

        return {
            "verify": ca_file if tls_verify else False,
            "cert": cert if tls_verify else None  # Cert is only included if tls_verify is True
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
