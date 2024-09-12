import requests
from utils import ConfigLoader, LoggingHandler, sso_login
import json

def getSession(session: requests.Session, config_path: str):
    try:
        config_loader = ConfigLoader(config_path)
        logger = LoggingHandler().get_execution_logger(__name__)

        # Perform SSO login if enabled
        ssoEnabled = config_loader.get_config('ssoLogin', 'enabled', False)
        if ssoEnabled:
            session = sso_login(session, config_loader, logger)
            if not session:
                logger.error("SSO login failed. Exiting.")
                return None

        # Add TLS certificates if TLS validation is enabled
        tlsConfig = config_loader.get_config('validateTls', 'enabled', False)
        if tlsConfig:
            session.verify = config_loader.get_config('validateTls', 'caCert', None)
            session.cert = (
                config_loader.get_config('validateTls', 'clientCert', None),
                config_loader.get_config('validateTls', 'clientKey', None)
            )

        return session

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return None
