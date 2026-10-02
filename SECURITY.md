# Security Policy

## Purpose

SecureVPC is a security engineering portfolio project demonstrating AWS infrastructure security, IAM auditing, identity federation, logging, monitoring, and automated security validation.

## Reporting a Security Issue

Please do not publicly disclose credentials, access tokens, private keys, or other sensitive information.

For issues involving this repository, please use the repository's GitHub security reporting mechanisms where available.

## Credentials

No AWS credentials, private keys, access tokens, or other secrets should be committed to this repository.

The project is designed to use short-lived AWS credentials through GitHub Actions OIDC federation rather than long-lived AWS access keys.

## Authorized Use

All testing and deployment activities must be performed against AWS resources for which the operator has explicit authorization.
