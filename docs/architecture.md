SecureVPC Architecture

Overview

SecureVPC uses GitHub Actions with AWS IAM OIDC federation to perform automated, read-only IAM security auditing without storing long-lived AWS access keys in GitHub.

The architecture separates:

Source code and workflow execution in GitHub

Federated authentication through GitHub OIDC

Authorization through an AWS IAM role

Temporary AWS credentials issued by AWS STS

Read-only IAM security auditing performed by Python

Architecture Flow

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
    +-----------------------------+
    |                             |
    | Test job                    | AWS audit job
    v                             v
pytest                    GitHub OIDC Token
                                  |
                                  v
                     AWS IAM OIDC Identity Provider
                                  |
                                  v
                 IAM Trust Policy Evaluation
                                  |
                                  v
                 SecureVPC-GitHub-IAMAuditor
                                  |
                                  v
                       AWS STS Temporary
                         Credentials
                                  |
                                  v
                  SecureVPC-IAMAuditorReadOnly
                                  |
                                  v
                         Python IAM Auditor
                                  |
                                  v
                         IAM API Read Calls

GitHub Actions

The security workflow is located at:

.github/workflows/security.yml

The workflow contains two security-related jobs.

IAM Auditor Tests

The test job:

Runs on GitHub-hosted infrastructure

Uses Python 3.12

Installs boto3 and pytest

Runs the IAM auditor unit tests

Does not require AWS credentials

The test command is:

PYTHONPATH=. pytest -q

Keeping the unit-test job separate from AWS authentication means the tests do not need access to the AWS account.

AWS IAM Audit

The AWS audit job performs the live IAM security audit.

It requests an OIDC token from GitHub and uses the token with AWS STS to assume the dedicated IAM role.

The workflow requests:

permissions:
  contents: read
  id-token: write

The id-token: write permission allows GitHub Actions to request an OIDC token.

The workflow does not configure long-lived AWS access keys.

GitHub OIDC Federation

GitHub Actions acts as the external identity provider for the AWS role.

AWS contains an IAM OIDC provider for:

token.actions.githubusercontent.com

The workflow requests an identity token from GitHub.

AWS then evaluates that token against the trust policy of:

SecureVPC-GitHub-IAMAuditor

The role trust policy restricts the allowed audience to:

sts.amazonaws.com

It also restricts the subject to the specific SecureVPC repository and main branch.

Conceptually, the trust relationship is:

GitHub repository
      |
      | OIDC identity
      v
SecureSasi/securevpc
      |
      | main branch only
      v
AWS IAM OIDC Provider
      |
      v
SecureVPC-GitHub-IAMAuditor

This prevents an arbitrary GitHub repository from using the role.

Branch Restriction

The IAM trust policy is restricted to the repository's main branch.

The trusted subject is:

repo:SecureSasi@180009560/securevpc@1396800758:ref:refs/heads/main

The trust policy therefore establishes a security boundary between:

Allowed
SecureSasi/securevpc
main branch

and other GitHub repositories or branches.

The GitHub Actions AWS audit job is also configured so that it does not run for pull requests.

This provides two layers of protection:

The workflow prevents the AWS audit job from executing for pull requests.

The AWS IAM trust policy independently restricts role assumption to the main branch.

The IAM trust policy is the authoritative AWS-side security boundary.

AWS STS Temporary Credentials

After the OIDC token is accepted by AWS, GitHub Actions assumes:

SecureVPC-GitHub-IAMAuditor

AWS STS provides temporary credentials for the workflow session.

The workflow then verifies the assumed identity using:

aws sts get-caller-identity

The Python auditor uses these temporary credentials to make read-only IAM API calls.

The architecture therefore avoids storing a permanent AWS access key in GitHub.

IAM Authorization

Authentication and authorization are separated.

Authentication

GitHub proves its identity using the OIDC token.

GitHub OIDC
     |
     v
AWS IAM trust policy

Authorization

After the role is assumed, its attached policy determines what the workflow can do.

The role has the customer-managed policy:

SecureVPC-IAMAuditorReadOnly

The policy grants:

iam:ListUsers
iam:ListAccessKeys
iam:GetLoginProfile
iam:ListMFADevices
iam:ListAttachedUserPolicies

These permissions support the current IAM audit checks.

The role does not have IAM write permissions.

IAM Auditor

The Python auditor is located at:

iam-auditor/auditor.py

The auditor performs read-only checks for:

Active IAM access keys

Active access keys older than 90 days

IAM users with console password access

IAM users with console access but no MFA

Directly attached IAM user policies

The auditor reports findings but does not modify AWS resources.

The current design therefore follows a read-only security-audit model:

AWS IAM
   |
   | read-only API calls
   v
Python IAM Auditor
   |
   v
Security Findings

Security Boundary

The primary security boundary is the AWS IAM role trust policy.

The role can only be assumed when the GitHub OIDC identity satisfies the configured trust conditions.

The authorization boundary is then provided by the role's attached read-only policy.

                 GitHub
                    |
                    | OIDC
                    v
          +-------------------+
          | IAM Trust Policy  |
          +-------------------+
                    |
             trusted identity
                    |
                    v
       +------------------------+
       | GitHub IAM Auditor     |
       | Role                   |
       +------------------------+
                    |
             read-only policy
                    |
                    v
       +------------------------+
       | IAM Read Operations    |
       +------------------------+

This creates a layered security model:

Identity boundary: GitHub OIDC

Trust boundary: AWS IAM role trust policy

Authorization boundary: least-privilege IAM policy

Credential boundary: temporary AWS STS credentials

Application boundary: read-only Python auditor

Pull Request Security

The workflow runs unit tests for pull requests, but the AWS IAM audit job is restricted to pushes and manual workflow runs on main.

This means pull requests can receive automated code validation without automatically receiving AWS credentials.

The distinction is intentional:

Pull Request
    |
    +--> Unit tests
    |
    X--> AWS IAM credentials

main branch
    |
    +--> Unit tests
    |
    +--> OIDC authentication
    |
    +--> AWS IAM audit

Current Scope

The architecture described in this document represents the components currently implemented and verified in the project.

The following are not yet part of the implemented architecture:

AWS CloudTrail deployment

CloudTrail-based detections

Security monitoring infrastructure

NAT Gateway deployment

These are planned extensions of the project rather than current production components.

Security Design Principles

The architecture demonstrates the following security principles:

Least privilege

Federated authentication

Short-lived credentials

Branch-restricted trust

Separation of authentication and authorization

Read-only security auditing

Reduced credential exposure

Automated security validation

Separation of pull-request testing from AWS access
