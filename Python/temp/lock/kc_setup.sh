#!/bin/bash

# Variables
KEYCLOAK_SERVER="http://localhost:9090/auth"
REALM="myrealm"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin"

CLIENT_ID="my-client"
CLIENT_SECRET="my-secret"

ROLE_NAME="my-role"

USERNAME="my-user"
PASSWORD="my-password"

# Login to Keycloak
kcadm.sh config credentials --server $KEYCLOAK_SERVER --realm master --user $ADMIN_USER --password $ADMIN_PASSWORD

# Create Client
kcadm.sh create clients -r $REALM -s clientId=$CLIENT_ID -s secret=$CLIENT_SECRET -s enabled=true

# Create Role
kcadm.sh create roles -r $REALM -s name=$ROLE_NAME

# Create User
kcadm.sh create users -r $REALM -s username=$USERNAME -s enabled=true

# Set User Password
USER_ID=$(kcadm.sh get users -r $REALM -q username=$USERNAME --fields id -o csv | tail -n 1 | tr -d '"')
kcadm.sh set-password -r $REALM --username $USERNAME --new-password $PASSWORD

# Assign Role to User
ROLE_ID=$(kcadm.sh get roles -r $REALM -q name=$ROLE_NAME --fields id -o csv | tail -n 1 | tr -d '"')
kcadm.sh add-roles -r $REALM --uusername $USERNAME --rolename $ROLE_NAME

echo "Client, role, and user creation completed successfully!"
