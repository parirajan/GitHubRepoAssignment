aws rds describe-db-instances --query "DBInstances[].{DBInstanceIdentifier:DBInstanceIdentifier, Engine:Engine, Status:DBInstanceStatus}" --output table
