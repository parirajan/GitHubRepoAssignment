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
        """
        Gets the TLS options based on the config.
        - If tls_enabled is false, returns verify=False (no TLS).
        - If tls_enabled is true:
          - If tls_verify is false: returns verify=False.
          - If tls_verify is true: sends verify=True (or caCert if provided), along with clientCert and clientKey.
        """
        tls_enabled = config.get("tls_enabled", True)
        tls_verify = config.get("tls_verify", True)
        
        # If TLS is disabled, return verify=False (no TLS)
        if not tls_enabled:
            return {"verify": False}

        # If TLS is enabled but verification is disabled, do not verify certificates
        if tls_enabled and not tls_verify:
            return {"verify": False}

        # If TLS verification is enabled
        tls_options = {"verify": True}  # Default to system trust store

        # Use CA cert if provided, otherwise system trust store (verify=True)
        ca_cert = config["tls_options"].get("ca_file")
        if ca_cert:
            tls_options["verify"] = ca_cert  # Use custom CA cert if provided

        # Add client certificate and key if provided
        client_cert = config["tls_options"].get("cert")
        client_key = config["tls_options"].get("key")
        if client_cert and client_key:
            tls_options["cert"] = (client_cert, client_key)

        return tls_options

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
