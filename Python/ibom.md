# Infrastructure BOM (iBOM) Lifecycle

This document defines a 4-stage architecture to build and manage an **Infrastructure Bill of Materials (iBOM)** by combining Terraform state and AWS live infrastructure, with full reconciliation and relationship mapping — outputting a CycloneDX-compliant BOM.

---

## Objective

Enable iBOM generation across multiple AWS accounts by:

- Parsing Terraform state files
- Scanning AWS live infrastructure
- Mapping resource relationships (e.g., IAM Role -> EC2)
- Reconciling declared vs actual infrastructure
- Emitting a CycloneDX-formatted BOM with drift and dependency awareness

---

## Stage 1: Terraform State Parsing

**Inputs:**
- `.tfstate` files from S3, Terraform Cloud, Git

**Actions:**
- Load and normalize each resource block
- Extract:
  - Type (e.g., `aws_iam_role`)
  - Name and logical ID
  - Attributes and `depends_on`
- Output a simplified BOM-style structure:
```json
{
  "id": "aws_iam_role.app_role",
  "type": "iam_role",
  "depends_on": ["aws_iam_policy.policy1"]
}
```

**Tools:**
- `python-hcl2`, `jq`, or JSON loader for `.tfstate`

---

## Stage 2: AWS Live Infrastructure Scan

**Inputs:**
- AWS account credentials (via AssumeRole)
- Optional: AWS Config data

**Actions:**
- Discover:
  - EC2, IAM, S3, Lambda, SG, RDS, etc.
- Extract relationships such as:
  - EC2 → IAM Role via `IamInstanceProfile`
  - Lambda → Role
  - S3 → Policy

**Output:**
```json
{
  "id": "i-0a123b456",
  "type": "ec2_instance",
  "region": "us-west-2",
  "depends_on": ["iam_role:app_role", "security_group:sg-001"]
}
```

**Tools:**
- `boto3`, AWS Config, AWS CLI

---

## Stage 3: Reconciliation & Graph Merge

**Goal:**
- Merge Terraform and AWS outputs
- Build a dependency-aware graph
- Mark each component with its status

**Statuses:**
- `managed`: exists in both TF and AWS
- `orphaned`: exists in AWS only
- `stale`: exists in TF only
- `dangling`: has unresolved dependency

**Process:**
- Match by logical ID or ARN
- Use graph tool (`networkx`, dict, or adjacency map)
- Validate all `dependsOn` edges

---

## Stage 4: CycloneDX iBOM Generation

**Actions:**
- Convert merged and reconciled resource set into CycloneDX format
- Include:
  - `bom-ref`: unique ID
  - `type`: infrastructure
  - `dependsOn`: logical references
  - `properties`: region, account, tags, origin (live/tf/both)
  - `status`: managed/orphaned/stale

**Example Output:**
```json
{
  "type": "infrastructure",
  "name": "app-server",
  "bom-ref": "ec2:i-0123",
  "status": "managed",
  "dependsOn": ["iam:app-role", "sg:sg-001"],
  "properties": [
    {"name": "region", "value": "us-west-2"},
    {"name": "origin", "value": "live+tf"}
  ]
}
```

**Tools:**
- `cyclonedx-python-lib`, custom JSON emitter

---

## Summary: End-to-End Workflow

```
1. Terraform State → Parse → iBOM (tf_declared)
2. AWS Scan        → Normalize → iBOM (live)
3. Merge + Reconcile → Graph + Compare → iBOM (reconciled)
4. Output → CycloneDX JSON with status and dependency edges
```

This model enables promotion gating, drift detection, infrastructure as inventory, and integration with CMDBs or visualization tools.
