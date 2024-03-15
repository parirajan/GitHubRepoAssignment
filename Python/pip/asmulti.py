import aerospike
from aerospike import exception as ex
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# Configuration for connecting to Aerospike
config = {
    'hosts': [('127.0.0.1', 3000)]
}

# Lock for synchronizing access to the unique ID
lock = threading.Lock()

# Connect to Aerospike
try:
    client = aerospike.client(config).connect()
except ex.ClientError as e:
    print("Error connecting to Aerospike:", e)
    raise

def get_or_create_unique_id(namespace, set_name, combination):
    aerospike_key = (namespace, set_name, combination)
    try:
        _, _, bins = client.get(aerospike_key)
        # If the combination exists, return its existing unique ID
        return bins.get('unique_id', None)
    except ex.RecordNotFound:
        # If the combination is new, return None
        return None

def insert_data_with_send_key_policy(namespace, set_name, account_id, account_type, rtn, venue_id):
    combination = f"{account_id}_{account_type}_{rtn}_{venue_id}"
    unique_id = get_or_create_unique_id(namespace, set_name, combination)
    if unique_id is None:
        with lock:
            # Generate a new unique ID based on the highest existing ID for this set, or start from 0 if no records exist
            scan = client.scan(namespace, set_name)
            scan.select('unique_id')
            max_id = max(int(record[2]['unique_id']) for record in scan.results()) if scan.results() else 0
            unique_id = f"{max_id + 1:010d}"
            aerospike_key = (namespace, set_name, combination)
            bins = {'unique_id': unique_id, 'combination': combination}
            try:
                client.put(aerospike_key, bins, policy={'key': aerospike.POLICY_KEY_SEND})
            except ex.AerospikeError as e:
                print(f"Error inserting record for combination {combination}: {e}")
    else:
        print(f"Combination {combination} already exists with unique ID {unique_id}")

def print_set_contents(namespace, set_name):
    def print_record(record_tuple):
        _, _, bins = record_tuple
        combination = bins.get('combination', 'Unknown')  # Getting combination from bins
        unique_id = bins.get('unique_id', 'N/A')
        print(f"Combination: {combination}, Unique ID: {unique_id}")

    scan = client.scan(namespace, set_name)
    scan.foreach(print_record)

def simulate_requests(namespace, set_name):
    account_ids = [f"A{str(i).zfill(3)}" for i in range(1, 1001)]
    account_types = ["Checking", "Savings"]
    rtns = ["015000015", "015000016"]
    venue_ids = ["V001", "V002"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for i in range(1000):  # Simulate 1000 requests for demonstration
            account_id = random.choice(account_ids)
            account_type = random.choice(account_types)
            rtn = random.choice(rtns)
            venue_id = random.choice(venue_ids)
            # Submit a task to insert data with the send_key policy
            futures.append(executor.submit(insert_data_with_send_key_policy, namespace, set_name, account_id, account_type, rtn, venue_id))

        for future in futures:
            future.result()  # Wait for all insert tasks to complete

if __name__ == "__main__":
    namespace = 'test'
    set_name = 'unique_combinations'

    # Clear existing data if necessary (careful: this operation is destructive)
    # client.truncate(namespace, set_name, 0)

    # Simulate inserting data with the send_key policy enabled
    simulate_requests(namespace, set_name)

    # Print the set contents after insertion
    print_set_contents(namespace, set_name)

    # Close the connection to Aerospike
    client.close()
