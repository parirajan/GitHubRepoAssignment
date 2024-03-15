import aerospike
from aerospike import exception as ex

# Configuration for connecting to Aerospike
config = {
    'hosts': [('127.0.0.1', 3000)]
}

# Connect to Aerospike
try:
    client = aerospike.client(config).connect()
except ex.ClientError as e:
    print("Error connecting to Aerospike:", e)
    raise

def print_set_contents(namespace, set_name):
    combination_count = 0
    unique_ids = set()  # Use a set to keep track of unique IDs without duplicates

    def print_record(record_tuple):
        nonlocal combination_count  # Reference the outer scope variable
        key, metadata, bins = record_tuple
        # Extract the unique ID from the bins
        unique_id = bins.get('unique_id', 'N/A')
        # The key's third element (assuming default tuple structure) is the record's primary key, which we're using as the combination
        combination = key[2] if key else 'Unknown'
        print(f"Combination: {combination}, Unique ID: {unique_id}")

        combination_count += 1
        unique_ids.add(unique_id)

    scan = client.scan(namespace, set_name)
    scan.foreach(print_record)

    # Print summary after scanning all records
    print(f"\nSummary:")
    print(f"Total Combinations: {combination_count}")
    print(f"Total Unique IDs: {len(unique_ids)}")

namespace = 'test'
set_name = 'unique_combinations'

# Print the set contents and summary
print_set_contents(namespace, set_name)

# Close the connection to Aerospike
client.close()
