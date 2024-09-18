import requests
from utils import config, logger

def getSession(session: requests.Session):
    try:
        ssologin = config.ssologin
        tlsConfig = config.tlsConfig
        ssoEnabled = ssologin.get("enabled", False)
        ssoHeaders = ssologin.get("regHeaders", False)
        if ssoEnabled:
            ssoHeaders = {
                key: (json.dumps(value) if isinstance(value, dict) else str(value))
                for key, value in ssoHeaders.items()
            }
        session.headers.update(ssoHeaders)

        if tlsConfig.get("enabled", False):
            session.verify = tlsConfig.get("caCert", None)
            session.cert = (
                tlsConfig.get("clientCert", None),
                tlsConfig.get("clientKey", None)
            )
        
        return session

    except Exception as e:
        logger.LoggingHandler.getExecutionLogger(__name__).error(
            "No session provided!", str(e)
        )
        return None
