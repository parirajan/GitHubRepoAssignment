curl -X POST "https://your-okta-domain.com/oauth2/v1/token" \
  -u "client_id:client_secret" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&scope=okta.apps.read okta.groups.read okta.users.read"


curl -X GET "https://your-okta-domain.com/api/v1/apps" \
  -H "Authorization: Bearer your-token" \
  -H "Accept: application/json"
