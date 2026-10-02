from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from auditor import IAMAuditor


def configure_clean_user(iam):
    iam.get_paginator.return_value.paginate.return_value = [
        {
            "Users": [
                {
                    "UserName": "test-user",
                }
            ]
        }
    ]

    iam.get_login_profile.return_value = {}

    iam.list_mfa_devices.return_value = {
        "MFADevices": []
    }

    iam.list_attached_user_policies.return_value = {
        "AttachedPolicies": []
    }


def test_active_access_key_is_detected():
    iam = Mock()
    configure_clean_user(iam)

    iam.list_access_keys.return_value = {
        "AccessKeyMetadata": [
            {
                "AccessKeyId": "AKIATEST",
                "Status": "Active",
                "CreateDate": datetime.now(timezone.utc),
            }
        ]
    }

    auditor = IAMAuditor(iam)

    findings = auditor.audit_users()

    assert any(
        finding.check == "ACTIVE_ACCESS_KEY"
        for finding in findings
    )


def test_old_active_access_key_is_detected():
    iam = Mock()
    configure_clean_user(iam)

    old_date = datetime.now(timezone.utc) - timedelta(days=120)

    iam.list_access_keys.return_value = {
        "AccessKeyMetadata": [
            {
                "AccessKeyId": "AKIAOLD",
                "Status": "Active",
                "CreateDate": old_date,
            }
        ]
    }

    auditor = IAMAuditor(iam)

    findings = auditor.audit_users()

    assert any(
        finding.check == "OLD_ACTIVE_ACCESS_KEY"
        for finding in findings
    )


def test_direct_policy_attachment_is_detected():
    iam = Mock()
    configure_clean_user(iam)

    iam.list_access_keys.return_value = {
        "AccessKeyMetadata": []
    }

    iam.list_attached_user_policies.return_value = {
        "AttachedPolicies": [
            {
                "PolicyName": "ReadOnlyAccess",
                "PolicyArn": (
                    "arn:aws:iam::aws:policy/ReadOnlyAccess"
                ),
            }
        ]
    }

    auditor = IAMAuditor(iam)

    findings = auditor.audit_users()

    assert any(
        finding.check == "DIRECT_POLICY_ATTACHMENT"
        for finding in findings
    )


def test_no_findings_for_clean_user():
    iam = Mock()
    configure_clean_user(iam)

    iam.list_access_keys.return_value = {
        "AccessKeyMetadata": []
    }

    auditor = IAMAuditor(iam)

    findings = auditor.audit_users()

    assert findings == []

def test_missing_mfa_is_detected():
    iam = Mock()
    configure_clean_user(iam)

    iam.list_access_keys.return_value = {
        "AccessKeyMetadata": []
    }

    iam.get_login_profile.return_value = {
        "LoginProfile": {
            "UserName": "test-user"
        }
    }

    iam.list_mfa_devices.return_value = {
        "MFADevices": []
    }

    auditor = IAMAuditor(iam)

    findings = auditor.audit_users()

    assert any(
        finding.check == "MISSING_MFA"
        for finding in findings
    )
