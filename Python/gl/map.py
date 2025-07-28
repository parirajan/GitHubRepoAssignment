import os
import json
from collections import defaultdict

# Define root folder and output file path
ROOT_DIR = "./projects"
OUTPUT_FILE = "service_upstream_map.json"

service_map = defaultdict(set)
all_services = set()

# Recursively search for config/envoy.json files
for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    if "envoy.json" in filenames and dirpath.endswith("config"):
        envoy_path = os.path.join(dirpath, "envoy.json")
        try:
            with open(envoy_path, "r") as f:
                data = json.load(f)

                service_name = data.get("service", {}).get("name")
                if not service_name:
                    continue
                all_services.add(service_name)

                upstream_list = data.get("Upstream", [])
                for entry in upstream_list:
                    upstream_name = entry.get("svc-name")
                    if upstream_name:
                        service_map[service_name].add(upstream_name)
                        all_services.add(upstream_name)

                service_map.setdefault(service_name, set())

        except json.JSONDecodeError:
            print(f"Warning: Skipping invalid JSON: {envoy_path}")
        except Exception as e:
            print(f"Error processing {envoy_path}: {e}")

# Ensure all services are included in the map
for svc in all_services:
    service_map.setdefault(svc, set())

# Convert sets to sorted lists
final_map = {svc: sorted(list(upstreams)) for svc, upstreams in service_map.items()}

# Write the result to a JSON file
with open(OUTPUT_FILE, "w") as f:
    json.dump(final_map, f, indent=2)

print(f"Service-to-upstream map written to: {OUTPUT_FILE}")
