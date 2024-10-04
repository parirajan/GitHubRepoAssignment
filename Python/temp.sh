#!/bin/bash

# Fetch the JSON configuration from Consul
config=$(curl -s http://localhost:8500/v1/kv/gitlab/package/config?raw)

# Parse the JSON using jq
project_id=$(echo $config | jq -r '.gitlab_package_registry.project_id')
package_name=$(echo $config | jq -r '.gitlab_package_registry.package_name')
package_version=$(echo $config | jq -r '.gitlab_package_registry.package_version')
file_name=$(echo $config | jq -r '.gitlab_package_registry.file_name')
gitlab_url=$(echo $config | jq -r '.gitlab_package_registry.gitlab_url')
access_token=$(echo $config | jq -r '.gitlab_package_registry.access_token')
download_path=$(echo $config | jq -r '.gitlab_package_registry.download_path')
auth_token_header=$(echo $config | jq -r '.gitlab_package_registry.headers.auth_token_header')

# Construct the download URL
download_url="$gitlab_url/api/v4/projects/$project_id/packages/generic/$package_name/$package_version/$file_name"

# Download the file using the access token
echo "Downloading $file_name from $download_url"
curl --header "$auth_token_header: $access_token" --output "$download_path/$file_name" "$download_url"

# Check if the download was successful
if [ $? -eq 0 ]; then
  echo "File downloaded successfully to $download_path/$file_name"
else
  echo "Failed to download file."
fi
