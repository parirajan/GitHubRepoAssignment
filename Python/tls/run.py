import json
from utils import Utils, Logger
from getSession import get_session

# Load configuration and setup logging
config = Utils.load_config("config.json")
logger = Logger.setup_logger()

# Get session and login payload from getSession
session, loginpayload = get_session(config)

# Build the URL for getInstancesTable with request as a query string
api_url = Utils.get_full_url(config, "api", "getInstancesTable") + '?{"request":"getInstancesTable"}'
request_type = Utils.get_request_type(config, "api", "getInstancesTable")
uid = config["uid"]

logger.info(f"Sending {request_type} request to {api_url} with UID: {uid}")

# Get TLS options (includes both cert and verify options)
tls_options = Utils.get_tls_options(config)

# Make the GET request to fetch the cluster status
if request_type == "GET":
    getClusterStatus = session.get(f"{api_url}&uid={uid}", headers=loginpayload, **tls_options).text

# Log and print the cluster status
getClusterStatusJson = json.loads(getClusterStatus)
cluster_status_pretty = json.dumps(getClusterStatusJson, indent=4, sort_keys=True)
logger.info("Cluster Status: %s", cluster_status_pretty)
print(cluster_status_pretty)
