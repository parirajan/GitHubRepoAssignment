#!/bin/bash

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

# Enable AWS auth method
vault auth enable aws

# Configure AWS auth method
vault write auth/aws/config/client \
    access_key=test \
    secret_key=test \
    region=us-east-1

# Get the role ARN
ROLE_ARN=$(aws iam get-role --role-name VaultAuthRole --query 'Role.Arn' --output text --endpoint-url=http://localhost:4566)

# Create a role in Vault
vault write auth/aws/role/my-role \
    auth_type=iam \
    bound_iam_principal_arn="$ROLE_ARN" \
    policies=admin-policy \
    max_ttl=500

# Create an admin policy
cat <<EoF > admin-policy.hcl
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EoF

# Write the admin policy
vault policy write admin-policy admin-policy.hcl
