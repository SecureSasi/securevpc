#!/usr/bin/env python3

"""
SecureVPC IAM Security Auditor

Read-only IAM security checks for portfolio and defensive security testing.

The auditor intentionally does not modify AWS resources.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import boto3


ACCESS_KEY_MAX_AGE_DAYS = 90


@dataclass
class Finding:
    severity: str
    check: str
    principal: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "check": self.check,
            "principal": self.principal,
            "message": self.message,
        }


class IAMAuditor:
    def __init__(self, iam_client: Any) -> None:
        self.iam = iam_client

    def audit_users(self) -> list[Finding]:
        findings: list[Finding] = []

        paginator = self.iam.get_paginator("list_users")

        for page in paginator.paginate():
            for user in page.get("Users", []):
                username = user["UserName"]

                # Check access keys.
                key_response = self.iam.list_access_keys(
                    UserName=username
                )

                for key in key_response.get("AccessKeyMetadata", []):
                    if key["Status"] == "Active":
                        findings.append(
                            Finding(
                                severity="HIGH",
                                check="ACTIVE_ACCESS_KEY",
                                principal=username,
                                message=(
                                    "IAM user has an active long-lived "
                                    "access key."
                                ),
                            )
                        )

                        create_date = key.get("CreateDate")

                        if create_date:
                            age_days = (
                                datetime.now(timezone.utc) - create_date
                            ).days

                            if age_days > ACCESS_KEY_MAX_AGE_DAYS:
                                findings.append(
                                    Finding(
                                        severity="HIGH",
                                        check="OLD_ACTIVE_ACCESS_KEY",
                                        principal=username,
                                        message=(
                                            f"Active access key is "
                                            f"{age_days} days old. "
                                            f"Keys older than "
                                            f"{ACCESS_KEY_MAX_AGE_DAYS} "
                                            f"days should be reviewed."
                                        ),
                                    )
                                )

                # Check console password.
                login_profile = self.get_login_profile(username)

                if login_profile:
                    findings.append(
                        Finding(
                            severity="MEDIUM",
                            check="CONSOLE_PASSWORD",
                            principal=username,
                            message=(
                                "IAM user has console password access. "
                                "Prefer federated access through IAM "
                                "Identity Center where possible."
                            ),
                        )
                    )

                    # Check MFA for users with console access.
                    mfa_response = self.iam.list_mfa_devices(
                        UserName=username
                    )

                    if not mfa_response.get("MFADevices"):
                        findings.append(
                            Finding(
                                severity="HIGH",
                                check="MISSING_MFA",
                                principal=username,
                                message=(
                                    "IAM user has console access but no "
                                    "MFA device is associated."
                                ),
                            )
                        )

                # Check directly attached policies.
                attached = self.iam.list_attached_user_policies(
                    UserName=username
                )

                for policy in attached.get("AttachedPolicies", []):
                    findings.append(
                        Finding(
                            severity="MEDIUM",
                            check="DIRECT_POLICY_ATTACHMENT",
                            principal=username,
                            message=(
                                f"User has directly attached policy: "
                                f"{policy['PolicyName']}."
                            ),
                        )
                    )

        return findings

    def get_login_profile(self, username: str) -> bool:
        try:
            response = self.iam.get_login_profile(
                UserName=username
            )
            return bool(response.get("LoginProfile"))

        except self.iam.exceptions.NoSuchEntityException:
            return False


def build_auditor(profile: str | None) -> IAMAuditor:
    session_kwargs: dict[str, str] = {}

    if profile:
        session_kwargs["profile_name"] = profile

    session = boto3.Session(**session_kwargs)

    return IAMAuditor(session.client("iam"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the SecureVPC IAM security auditor."
    )

    parser.add_argument(
        "--profile",
        help="AWS CLI profile to use.",
    )

    args = parser.parse_args()

    auditor = build_auditor(args.profile)
    findings = auditor.audit_users()

    if not findings:
        print("No IAM findings detected.")
        return 0

    print("SecureVPC IAM Security Audit")
    print("=" * 32)

    for finding in findings:
        print(
            f"[{finding.severity}] "
            f"{finding.check} "
            f"{finding.principal}: "
            f"{finding.message}"
        )

    print()
    print(f"Total findings: {len(findings)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
