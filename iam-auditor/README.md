# SecureVPC IAM Security Auditor

## Purpose

The SecureVPC IAM Security Auditor is a read-only Python security auditing tool that evaluates AWS IAM users for several common identity and access-management risks.

The auditor is designed for defensive security testing and portfolio demonstration.

It does not modify AWS resources.

## What the Auditor Checks

The auditor currently performs the following checks.

### 1. Active IAM Access Keys

The auditor identifies IAM users with active access keys.

Finding:

```text
HIGH - ACTIVE_ACCESS_KEY
```

The purpose of this check is to identify long-lived IAM user credentials that may require security review.

### 2. Old Active Access Keys

Active access keys are checked for age.

The current review threshold is:

```text
90 days
```

An active key older than 90 days produces:

```text
HIGH - OLD_ACTIVE_ACCESS_KEY
```

The check is intended to provide visibility into aging IAM credentials.

### 3. Console Password Access

The auditor checks whether an IAM user has an AWS console login profile.

A user with console password access produces:

```text
MEDIUM - CONSOLE_PASSWORD
```

The project favors federated human access through AWS IAM Identity Center where appropriate.

### 4. Missing MFA

For IAM users with console access, the auditor checks whether an MFA device is associated with the user.

A console-enabled user without MFA produces:

```text
HIGH - MISSING_MFA
```

### 5. Direct IAM Policy Attachments

The auditor checks for policies directly attached to IAM users.

A directly attached policy produces:

```text
MEDIUM - DIRECT_POLICY_ATTACHMENT
```

This provides visibility into user-level permission assignments that may require governance review.

## AWS Permissions

The auditor uses a deliberately limited set of IAM read permissions.

The GitHub Actions role uses the customer-managed policy:

```text
SecureVPC-IAMAuditorReadOnly
```

The required permissions are:

```text
iam:ListUsers
iam:ListAccessKeys
iam:GetLoginProfile
iam:ListMFADevices
iam:ListAttachedUserPolicies
```

The auditor does not require IAM write permissions.

## Security Model

The auditor follows a read-only security model:

```text
AWS IAM
    |
    | Read-only API calls
    v
IAM Security Auditor
    |
    v
Security Findings
```

The auditor does not:

- Create IAM users
- Delete IAM users
- Create access keys
- Delete access keys
- Modify IAM policies
- Modify MFA configuration
- Modify IAM roles

## Project Structure

```text
iam-auditor/
├── auditor.py
├── README.md
└── tests/
    └── test_auditor.py
```

## Requirements

The auditor requires:

- Python 3.11+ for local development
- `boto3`
- Valid AWS credentials with the required read-only IAM permissions

For GitHub Actions, AWS authentication is provided through GitHub OIDC and AWS STS temporary credentials.

## Local Usage

The auditor can use the AWS CLI profile configured on the local development system.

Example:

```bash
python auditor.py --profile securevpc-admin
```

If the AWS SDK should use the default credential chain:

```bash
python auditor.py
```

The auditor reads IAM information and prints security findings to standard output.

## Example Output

Example finding output:

```text
SecureVPC IAM Security Audit
================================
[HIGH] ACTIVE_ACCESS_KEY user-example: IAM user has an active long-lived access key.
[HIGH] OLD_ACTIVE_ACCESS_KEY user-example: Active access key is 120 days old. Keys older than 90 days should be reviewed.
[MEDIUM] CONSOLE_PASSWORD user-example: IAM user has console password access. Prefer federated access through IAM Identity Center where possible.
[HIGH] MISSING_MFA user-example: IAM user has console access but no MFA device is associated.
[MEDIUM] DIRECT_POLICY_ATTACHMENT user-example: User has directly attached policy: ExamplePolicy.

Total findings: 5
```

The example above illustrates the finding format; actual findings depend on the IAM configuration being audited.

## Running Tests

The unit tests are located in:

```text
tests/test_auditor.py
```

Run them from the `iam-auditor` directory:

```bash
PYTHONPATH=. pytest -q
```

The test suite uses mocked IAM responses rather than requiring live AWS resources.

This allows the security logic to be validated without making changes to an AWS environment.

## GitHub Actions Integration

The IAM auditor is executed automatically by:

```text
.github/workflows/security.yml
```

The workflow has two relevant stages.

### Unit Tests

The test job runs the mocked IAM auditor tests without AWS credentials.

```text
GitHub Actions
      |
      v
pytest
      |
      v
IAM auditor tests
```

### AWS IAM Audit

The AWS audit job uses GitHub OIDC to authenticate to AWS.

```text
GitHub Actions
      |
      v
GitHub OIDC
      |
      v
AWS IAM OIDC Provider
      |
      v
SecureVPC-GitHub-IAMAuditor
      |
      v
Temporary STS credentials
      |
      v
Python IAM Auditor
```

The AWS role is restricted by its trust policy to the `main` branch of the SecureVPC repository.

## Design Principles

The auditor demonstrates:

- Least privilege
- Read-only security assessment
- IAM credential lifecycle monitoring
- MFA governance
- IAM policy governance
- Federated authentication
- Short-lived AWS credentials
- Automated security validation
- Separation of testing and AWS integration

## Limitations

The auditor currently focuses on IAM users and the specific checks implemented in `auditor.py`.

It does not currently provide comprehensive AWS security posture management.

The following are outside the current auditor scope:

- AWS CloudTrail analysis
- CloudTrail event detection
- IAM role analysis
- IAM policy document analysis
- AWS Config compliance evaluation
- Security Hub integration
- Automated remediation

These capabilities may be added as the project evolves.

## Security

The auditor is intended for authorized AWS environments only.

Do not run security testing against AWS resources without appropriate authorization.

See the repository `SECURITY.md` file for additional security information.
