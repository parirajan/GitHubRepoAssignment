import os
import json
from collections import defaultdict

PROJECTS_ROOT = "./projects"
CONFIG_PATH = "config/envoy.json"
OUTPUT_FILE = "service_upstream_map.json"

service_map = defaultdict(set)
all_services = set()

for project in os.listdir(PROJECTS_ROOT):
    project_path = os.path.join(PROJECTS_ROOT, project)
    envoy_path = os.path.join(project_path, CONFIG_PATH)

    if os.path.isfile(envoy_path):
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

                # Ensure service is in map even with no upstreams
                service_map.setdefault(service_name, set())

        except json.JSONDecodeError:
            print(f"[WARN] Skipping invalid JSON: {envoy_path}")
    else:
        print(f"[INFO] Skipping {project}: no {CONFIG_PATH}")

# Add upstream-only services
for svc in all_services:
    service_map.setdefault(svc, set())

# Convert sets to sorted lists
final_map = {svc: sorted(list(upstreams)) for svc, upstreams in service_map.items()}

# Write output
with open(OUTPUT_FILE, "w") as f:
    json.dump(final_map, f, indent=2)

print(f"[DONE] Output written to {OUTPUT_FILE}")
