import aerospike
from aerospike import exception as ex
import sys

# Aerospike configuration
config = {
    'hosts': [('127.0.0.1', 3000)]
}

# Initialize the Aerospike client and connect to the cluster
try:
    client = aerospike.client(config).connect()
except ex.ClientError as e:
    print("Error connecting to Aerospike cluster:", e)
    sys.exit(1)

# Function to truncate a set
def truncate_set(client, namespace, set_name):
    try:
        # Attempt to truncate the set without specifying nanoseconds
        client.truncate(namespace, set_name, 0)
        print(f"Set '{set_name}' in namespace '{namespace}' has been successfully truncated.")
    except ex.AerospikeError as e:
        print(f"Failed to truncate set '{set_name}' in namespace '{namespace}':", e)

namespace = 'test'
set_name = 'unique_combinations'

# Truncate the set
truncate_set(client, namespace, set_name)

# Close the connection to Aerospike
client.close()
