#!/bin/bash

export AWS_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

# Create trust policy
cat <<EoF > trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EoF

# Create the IAM role
aws iam create-role --role-name VaultAuthRole --assume-role-policy-document file://trust-policy.json --endpoint-url=$AWS_URL

# Create role policy
cat <<EoF > role-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
EoF

# Attach the policy to the role
aws iam put-role-policy --role-name VaultAuthRole --policy-name VaultPolicy --policy-document file://role-policy.json --endpoint-url=$AWS_URL
