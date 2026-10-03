# SecureVPC Security Controls

## Purpose

This document describes the security controls currently implemented in the SecureVPC project.

The controls focus on:

- IAM least privilege
- Federated GitHub-to-AWS authentication
- Short-lived AWS credentials
- Branch-restricted trust
- IAM access-key monitoring
- MFA governance
- IAM policy governance
- Read-only security auditing
- Automated security validation

## 1. GitHub OIDC Federation

GitHub Actions authenticates to AWS using OpenID Connect (OIDC).

The workflow does not store a long-lived AWS access key.

The GitHub Actions workflow requests an OIDC token using:

```yaml
permissions:
  contents: read
  id-token: write
```

AWS validates the token through the configured IAM OIDC provider for:

```text
token.actions.githubusercontent.com
```

### Security benefit

OIDC removes the need to store permanent AWS access keys in GitHub repository secrets for this workflow.

AWS STS issues temporary credentials after the identity is successfully authenticated and authorized.

## 2. Branch-Restricted IAM Trust

The dedicated IAM role is:

```text
SecureVPC-GitHub-IAMAuditor
```

Its trust policy restricts role assumption to the `main` branch of the specific repository.

The trusted GitHub subject is:

```text
repo:SecureSasi@180009560/securevpc@1396800758:ref:refs/heads/main
```

The trust policy also requires:

```text
aud = sts.amazonaws.com
```

### Security benefit

The AWS role is not intended to be assumable by arbitrary GitHub repositories or branches.

The AWS-side trust policy establishes the authoritative identity boundary.

## 3. Least-Privilege IAM Policy

The GitHub Actions role uses the customer-managed policy:

```text
SecureVPC-IAMAuditorReadOnly
```

The policy grants only the IAM API actions required by the current auditor:

```text
iam:ListUsers
iam:ListAccessKeys
iam:GetLoginProfile
iam:ListMFADevices
iam:ListAttachedUserPolicies
```

The policy has no IAM write permissions.

### Permission mapping

| Permission | Purpose |
|---|---|
| `iam:ListUsers` | Enumerate IAM users for auditing |
| `iam:ListAccessKeys` | Identify active and aging access keys |
| `iam:GetLoginProfile` | Determine whether an IAM user has console password access |
| `iam:ListMFADevices` | Check MFA association for users with console access |
| `iam:ListAttachedUserPolicies` | Identify directly attached user policies |

### Security benefit

The role is limited to read operations required by the auditor.

The workflow cannot use this role to create, modify, or delete IAM resources.

## 4. Temporary AWS Credentials

After successful OIDC authentication and IAM role assumption, AWS STS provides temporary credentials to the GitHub Actions job.

The workflow verifies the resulting AWS identity with:

```bash
aws sts get-caller-identity
```

The Python auditor then uses the temporary session credentials to perform its IAM read operations.

### Security benefit

The workflow does not depend on a permanent AWS access key.

The credential lifecycle is controlled by AWS STS rather than by a manually managed GitHub secret.

## 5. IAM Access-Key Monitoring

The IAM auditor checks IAM users for active access keys.

An active access key generates a:

```text
HIGH
```

severity finding.

The auditor also calculates the age of active access keys.

The current review threshold is:

```text
90 days
```

An active key older than this threshold generates an additional:

```text
HIGH
```

severity finding.

### Security objective

The control provides visibility into long-lived IAM user credentials and identifies keys that require security review.

## 6. Console Password and MFA Governance

The auditor checks whether an IAM user has an AWS console login profile.

A user with console password access generates a:

```text
MEDIUM
```

finding.

For users with console access, the auditor checks associated MFA devices.

A console-enabled IAM user without an MFA device generates a:

```text
HIGH
```

finding.

### Security objective

The control identifies IAM users that have interactive console access without the expected MFA protection.

The project also promotes federated access through IAM Identity Center for human access rather than relying on long-lived IAM user credentials.

## 7. Direct IAM Policy Attachment Detection

The auditor checks for policies directly attached to IAM users.

A directly attached user policy generates a:

```text
MEDIUM
```

finding.

### Security objective

The check provides visibility into direct user-level permissions that can make access governance more difficult to manage.

The current auditor reports these configurations but does not modify them.

## 8. Read-Only Security Auditing

The Python IAM auditor is intentionally read-only.

It performs IAM API calls to collect security information and produces findings.

It does not:

- Create IAM users
- Delete IAM users
- Create access keys
- Delete access keys
- Modify IAM policies
- Change MFA configuration
- Modify IAM roles

### Security benefit

The auditing workflow is separated from administrative IAM operations.

A security finding does not automatically trigger a destructive or corrective AWS action.

## 9. Pull Request Security Boundary

The GitHub Actions workflow runs unit tests for pull requests.

The AWS IAM audit job is restricted to pushes and manual workflow runs on `main`.

Conceptually:

```text
Pull Request
    |
    +--> Unit tests
    |
    X--> AWS IAM audit credentials


main branch
    |
    +--> Unit tests
    |
    +--> OIDC authentication
    |
    +--> AWS IAM audit
```

### Security benefit

Untrusted pull-request code does not automatically receive the AWS IAM auditor role.

This separates code validation from access to the AWS environment.

## 10. GitHub Actions Job Permissions

The workflow defines repository-level permissions as:

```yaml
permissions:
  contents: read
```

The AWS audit job additionally requests:

```yaml
permissions:
  contents: read
  id-token: write
```

The `id-token` permission is scoped to the job that requires OIDC authentication.

### Security objective

Workflow permissions are explicitly declared rather than relying on broader implicit permissions.

## 11. Terraform Network Security

The Terraform configuration defines:

- A dedicated VPC
- Public subnets
- Private subnets
- Internet Gateway
- Public route table
- Private route tables
- Locked-down default security group

The default security group is configured without ingress or egress rules.

The Terraform configuration uses:

```hcl
ingress = []
egress  = []
```

### Security objective

The default security group does not provide implicit network connectivity.

Workloads can instead use explicitly defined security groups appropriate to their application requirements.

## 12. Private Subnet Design

The current Terraform design separates public and private subnets.

Private subnets do not currently have a NAT Gateway.

Therefore, the current private subnet design does not provide general outbound internet access through NAT.

This is an intentional scope decision for the current portfolio implementation and avoids introducing additional AWS infrastructure and associated cost.

A NAT-based egress architecture can be added later if workloads requiring outbound internet connectivity are introduced.

## 13. Infrastructure as Code

AWS network infrastructure is defined using Terraform.

The Terraform configuration provides controlled, repeatable infrastructure definitions rather than relying solely on manually configured AWS resources.

The configuration includes validation for the deployment environment:

```text
dev
test
prod
```

Availability Zones can also be explicitly supplied or selected automatically from available zones.

## 14. Automated Security Validation

GitHub Actions provides automated validation of the IAM auditor.

The test job runs:

```bash
PYTHONPATH=. pytest -q
```

The AWS audit job separately authenticates to AWS and executes:

```bash
python auditor.py
```

This separates:

```text
Application/unit validation
        |
        v
pytest
```

from:

```text
AWS integration validation
        |
        v
OIDC
        |
        v
IAM role assumption
        |
        v
IAM audit
```

## Security Control Summary

| Control | Implementation |
|---|---|
| Federated authentication | GitHub OIDC |
| AWS credential model | Temporary STS credentials |
| IAM trust restriction | Specific repository and `main` branch |
| IAM authorization | Dedicated customer-managed policy |
| IAM permissions | Read-only and limited to auditor requirements |
| Access-key monitoring | Active and aging key checks |
| MFA monitoring | Console users without MFA identified |
| Policy governance | Direct IAM user policies identified |
| AWS write access | Not granted to auditor role |
| PR AWS access | AWS audit job excluded from pull requests |
| Workflow permissions | Explicit GitHub Actions permissions |
| Network foundation | Terraform-managed VPC and subnet separation |
| Default security group | No ingress or egress rules |
| Security validation | Automated pytest and AWS IAM audit |

## Current Scope

These controls describe functionality currently implemented in the SecureVPC project.

The following security capabilities remain planned rather than implemented:

- AWS CloudTrail deployment
- CloudTrail-based detections
- Security monitoring infrastructure
- Additional IAM governance checks

They should be documented as implemented only after the corresponding infrastructure or automation has been built and verified.
