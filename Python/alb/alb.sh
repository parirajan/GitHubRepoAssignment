#!/bin/sh
set -e

echo "Waiting for LocalStack to become ready..."
until curl -s http://localstack:4566/health | grep '"ready": true' > /dev/null; do
  echo "LocalStack not ready yet. Sleeping 5 seconds..."
  sleep 5
done
echo "LocalStack is ready."

echo "Creating ALB..."
ALB_ARN=$(aws --endpoint-url=http://localstack:4566 elbv2 create-load-balancer \
  --name my-alb \
  --subnets subnet-1234 subnet-5678 \
  --scheme internet-facing \
  --type application \
  --output text \
  --query 'LoadBalancers[0].LoadBalancerArn')
echo "ALB ARN: $ALB_ARN"

echo "Creating target group for Nginx..."
TG_ARN=$(aws --endpoint-url=http://localstack:4566 elbv2 create-target-group \
  --name nginx-tg \
  --protocol HTTP \
  --port 80 \
  --vpc-id vpc-1234 \
  --output text \
  --query 'TargetGroups[0].TargetGroupArn')
echo "Target Group ARN: $TG_ARN"

echo "Creating listener with OIDC authentication and forward action..."
aws --endpoint-url=http://localstack:4566 elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions '[
    {
      "Type": "authenticate-oidc",
      "AuthenticateOidcConfig": {
        "Issuer": "http://keycloak:8080/auth/realms/myrealm",
        "AuthorizationEndpoint": "http://keycloak:8080/auth/realms/myrealm/protocol/openid-connect/auth",
        "TokenEndpoint": "http://keycloak:8080/auth/realms/myrealm/protocol/openid-connect/token",
        "UserInfoEndpoint": "http://keycloak:8080/auth/realms/myrealm/protocol/openid-connect/userinfo",
        "ClientId": "alb-client",
        "ClientSecret": "mysecret",
        "SessionCookieName": "AWSELBAuthSessionCookie",
        "Scope": "openid"
      }
    },
    {
      "Type": "forward",
      "ForwardConfig": {
        "TargetGroups": [
          {
            "TargetGroupArn": "'"$TG_ARN"'"
          }
        ]
      }
    }
  ]'
  
echo "ALB configuration completed."
