from __future__ import annotations

import unittest

from agentguard.backend.app.models import TaintStatus
from agentguard.backend.app.services.multi_agent import judge_delegation


class MultiAgentDelegationTests(unittest.TestCase):
    def test_child_inherits_parent_taint_without_downgrade(self) -> None:
        result = judge_delegation(
            parent_taint=TaintStatus.TAINTED,
            parent_permissions=["safe_read", "safe_write"],
            child_permissions=["safe_read"],
            delegated_context_status=TaintStatus.UNTRUSTED,
        )
        self.assertTrue(result["delegation_allowed"])
        self.assertEqual(result["child_taint_state"], "tainted")

    def test_extra_child_permission_is_rejected(self) -> None:
        result = judge_delegation(
            parent_taint=TaintStatus.UNTRUSTED,
            parent_permissions=["safe_read"],
            child_permissions=["safe_read", "external_send"],
            delegated_context_status=TaintStatus.UNTRUSTED,
        )
        self.assertFalse(result["delegation_allowed"])
        self.assertTrue(result["blocked_reasons"])

    def test_quarantined_context_cannot_be_delegated(self) -> None:
        result = judge_delegation(
            parent_taint=TaintStatus.TRUSTED,
            parent_permissions=["safe_read"],
            child_permissions=["safe_read"],
            delegated_context_status=TaintStatus.QUARANTINED,
        )
        self.assertFalse(result["delegation_allowed"])
        self.assertEqual(result["child_taint_state"], "quarantined")


if __name__ == "__main__":
    unittest.main()
