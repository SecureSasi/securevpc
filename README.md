# SecureVPC

Secure AWS VPC and IAM security engineering project built with Terraform, Python, AWS IAM, GitHub Actions, and GitHub OIDC federation.

The project demonstrates practical cloud security engineering concepts including infrastructure as code, IAM auditing, least privilege, federated identity, short-lived AWS credentials, and automated security validation.

Project Status

Core IAM security automation and GitHub Actions OIDC pipeline verified.

Currently implemented

AWS VPC infrastructure defined with Terraform

Public and private subnet architecture

Internet Gateway and routing

Locked-down default security group

Python-based IAM security auditor

IAM auditor unit tests using pytest

Dedicated least-privilege IAM role for GitHub Actions

GitHub OIDC federation to AWS

Short-lived AWS credentials through AWS STS

Branch-restricted IAM trust policy

Automated IAM security validation through GitHub Actions

Planned

AWS CloudTrail logging

CloudTrail-based security detections

Additional IAM governance checks

Expanded security monitoring

Additional automated security validation

Architecture

The current security automation flow is:

Developer
    |
    | git push
    v
GitHub Repository
SecureSasi/securevpc
    |
    v
GitHub Actions
    |
    +---------------------------+
    |                           |
    v                           v
IAM Auditor Tests        GitHub OIDC Token
    |                           |
    |                           v
    |                  AWS IAM OIDC Provider
    |                           |
    |                           v
    |                SecureVPC-GitHub-IAMAuditor
    |                           |
    |                           v
    |                  Temporary AWS credentials
    |                           |
    +---------------------------+
                                |
                                v
                     Read-only IAM permissions
                                |
                                v
                       Python IAM Auditor

The AWS IAM role trust policy restricts access to the main branch of the SecureSasi/securevpc repository.

GitHub Actions does not use long-lived AWS access keys for this integration. The workflow obtains temporary AWS credentials through GitHub OIDC and AWS STS.

IAM Auditor

The IAM auditor is located in:

iam-auditor/auditor.py

It performs read-only IAM security checks for:

Active IAM access keys

Old active IAM access keys

IAM users with console password access

IAM users with console access but no MFA

Directly attached IAM user policies

The auditor reports findings and does not modify AWS resources.

Example checks

An active IAM access key produces a HIGH severity finding.

An active access key older than the configured 90-day review threshold produces an additional HIGH severity finding.

An IAM user with console password access produces a MEDIUM severity finding.

An IAM user with console access but no MFA produces a HIGH severity finding.

A directly attached IAM user policy produces a MEDIUM severity finding.

IAM Least Privilege

GitHub Actions assumes the dedicated role:

SecureVPC-GitHub-IAMAuditor

The role uses the customer-managed policy:

SecureVPC-IAMAuditorReadOnly

The policy grants the following IAM read-only actions:

iam:ListUsers
iam:ListAccessKeys
iam:GetLoginProfile
iam:ListMFADevices
iam:ListAttachedUserPolicies

The GitHub Actions role does not have IAM write permissions.

This creates a separation between:

GitHub Actions
      |
      v
Federated IAM role
      |
      v
Read-only IAM policy
      |
      v
IAM security auditor

GitHub Actions

The security workflow is located at:

.github/workflows/security.yml

The workflow performs two primary functions.

1. IAM Auditor Tests

The workflow installs the Python dependencies and executes the IAM auditor test suite with pytest.

GitHub Actions
      |
      v
Python environment
      |
      v
pytest
      |
      v
IAM auditor tests

2. AWS IAM Security Audit

The AWS audit job:

Requests a GitHub OIDC token.

Uses the token to assume the dedicated AWS IAM role.

Receives temporary AWS credentials.

Verifies the AWS identity.

Runs the read-only IAM auditor.

The AWS audit job is restricted to pushes and manual workflow runs on the main branch.

Pull requests do not run the AWS audit job because the IAM trust policy is restricted to the main branch.

Terraform Infrastructure

Terraform defines the current AWS network foundation:

AWS VPC

Public subnets

Private subnets

Internet Gateway

Public route table

Private route tables

Locked-down default security group

Environment and project tagging

The Terraform configuration supports configurable AWS regions and Availability Zones.

The current design does not deploy a NAT Gateway. Private subnets therefore do not currently have outbound internet access through NAT.

This is intentional for the current portfolio implementation and avoids introducing unnecessary AWS infrastructure cost.

Security Principles Demonstrated

Least privilege

Federated identity

Short-lived credentials

Branch-restricted IAM trust

MFA governance

Access-key lifecycle monitoring

IAM policy governance

Infrastructure as Code

Automated security validation

Separation of unit testing and AWS integration

Read-only security auditing

Repository Structure

securevpc/
├── README.md
├── LICENSE
├── SECURITY.md
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── iam-auditor/
│   ├── auditor.py
│   └── tests/
│       └── test_auditor.py
├── detection/
│   └── README.md
├── docs/
│   ├── architecture.md
│   └── security-controls.md
└── .github/
    └── workflows/
        └── security.yml

Roadmap

The next planned security engineering components are:

AWS CloudTrail logging

CloudTrail-based security detections

Additional IAM governance checks

Security monitoring documentation

Expanded automated security validation

These components are intentionally documented as planned work until they are implemented and verified.

Security

See SECURITY.md for security-related information.

Disclaimer

This project is intended for educational, portfolio, and authorized security testing purposes only.
