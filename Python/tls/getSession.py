import requests
import json
from utils import ConfigLoader, LoggingHandler

def getSession(session: requests.Session, config_path: str):
    try:
        config_loader = ConfigLoader(config_path)
        logger = LoggingHandler().get_execution_logger(__name__)

        ssoLogin = config_loader.get_config('ssoLogin', 'enabled', False)
        tlsConfig = config_loader.get_config('validateTls', 'enabled', False)
        ssoEnabled = ssoLogin.get('enabled', False)
        ssoHeaders = ssoLogin.get('reqHeaders', {})

        if ssoEnabled:
            ssoHeaders = {
                key: (json.dumps(value) if isinstance(value, dict) else str(value))
                for key, value in ssoHeaders.items()
            }
            session.headers.update(ssoHeaders)

        if tlsConfig:
            session.verify = config_loader.get_config('validateTls', 'caCert', None)
            session.cert = (
                config_loader.get_config('validateTls', 'clientCert', None),
                config_loader.get_config('validateTls', 'clientKey', None)
            )

        return session

    except Exception as e:
        logger.error("No session provided", str(e))
        return None
