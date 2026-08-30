from odoo import fields
from odoo.tests import TransactionCase, tagged

from ..services.ai_query import EcoSphereAIQueryPipeline, ValidatorAgent


@tagged("post_install", "-at_install")
class TestEcoSphereAIQueryPipeline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env["esg.department"]
        cls.Employee = cls.env["hr.employee"]
        cls.User = cls.env["res.users"]
        cls.Factor = cls.env["esg.emission.factor"]
        cls.Carbon = cls.env["esg.carbon.transaction"]
        cls.Score = cls.env["esg.department.score"]
        cls.Issue = cls.env["esg.compliance.issue"]
        cls.Audit = cls.env["esg.audit"]
        cls.user_group = cls.env.ref("eco_sphere_esg.group_esg_user")

    def _department(self, suffix):
        return self.Department.create({"name": "AI Department %s" % suffix, "code": "AI%s" % suffix})

    def _employee_user(self, department, suffix):
        user = self.User.with_context(no_reset_password=True).create({
            "name": "AI User %s" % suffix,
            "login": "ai-user-%s@example.com" % suffix.lower(),
            "email": "ai-user-%s@example.com" % suffix.lower(),
            "groups_id": [(6, 0, [self.user_group.id])],
        })
        employee = self.Employee.create({"name": "AI Employee %s" % suffix, "user_id": user.id, "esg_department_id": department.id})
        return employee, user

    def _issue(self, department, owner, suffix, due_date=None):
        audit = self.Audit.sudo().create({
            "name": "AI Audit %s" % suffix,
            "department_id": department.id,
            "auditor_id": owner.id,
            "audit_date": fields.Date.today(),
        })
        issue = self.Issue.sudo().create({
            "name": "AI Issue %s" % suffix,
            "audit_id": audit.id,
            "department_id": department.id,
            "description": "<p>Issue</p>",
            "owner_id": owner.id,
            "due_date": due_date or fields.Date.subtract(fields.Date.today(), days=1),
            "severity": "high",
        })
        issue._refresh_overdue_flag()
        return issue

    def test_example_score_query_returns_cited_agent_trace(self):
        department = self._department("SCORE")
        employee, user = self._employee_user(department, "SCORE")
        self.Score.create({
            "department_id": department.id,
            "score_date": fields.Date.today(),
            "environmental_score": 78,
            "social_score": 71,
            "governance_score": 73,
        })

        result = EcoSphereAIQueryPipeline(self.env(user=user), use_llm=False).run(
            "What's my department's carbon score this quarter?",
            conversation_id="test-score",
            department_id=department.id,
            employee_id=employee.id,
        )

        self.assertTrue(result["verified"])
        self.assertIn("Department Score record", result["answer"])
        self.assertEqual(result["source"]["tool"], "get_department_score")
        self.assertTrue(result["source"]["record_ids"])
        self.assertEqual([row["agent"] for row in result["agent_trace"]], ["router", "executor", "responder", "validator", "responder"])

    def test_vague_question_stops_before_executor(self):
        department = self._department("VAGUE")
        employee, user = self._employee_user(department, "VAGUE")

        result = EcoSphereAIQueryPipeline(self.env(user=user), use_llm=False).run(
            "How are we doing?",
            department_id=department.id,
            employee_id=employee.id,
        )

        self.assertIn("Do you mean", result["answer"])
        self.assertFalse(result["source"])
        self.assertEqual([row["agent"] for row in result["agent_trace"]], ["router", "responder"])

    def test_project_context_question_answers_from_ecosphere_context(self):
        department = self._department("CTX")
        employee, user = self._employee_user(department, "CTX")

        result = EcoSphereAIQueryPipeline(self.env(user=user), use_llm=False).run(
            "What is the meaning of ESG?",
            department_id=department.id,
            employee_id=employee.id,
        )

        self.assertIn("Environmental, Social, and Governance", result["answer"])
        self.assertEqual(result["source"]["type"], "project_context")
        self.assertEqual(result["suggested_actions"][0]["target"], "Overview")

    def test_out_of_scope_question_is_not_answered(self):
        department = self._department("OOS")
        employee, user = self._employee_user(department, "OOS")

        result = EcoSphereAIQueryPipeline(self.env(user=user), use_llm=False).run(
            "Write a romantic poem for me",
            department_id=department.id,
            employee_id=employee.id,
        )

        self.assertIn("I can only answer questions about EcoSphere", result["answer"])
        self.assertEqual(result["source"]["type"], "domain_boundary")
        self.assertFalse(result["suggested_actions"])

    def test_non_admin_department_question_is_scoped_twice(self):
        own_department = self._department("OWN")
        other_department = self._department("OTHER")
        employee, user = self._employee_user(own_department, "RBAC")
        other_employee = self.Employee.create({"name": "Other Owner", "esg_department_id": other_department.id})
        own_issue = self._issue(own_department, employee, "OWN")
        other_issue = self._issue(other_department, other_employee, "OTHER")

        result = EcoSphereAIQueryPipeline(self.env(user=user), use_llm=False).run(
            "What's Department AI Department OTHER's compliance status?",
            department_id=own_department.id,
            employee_id=employee.id,
        )

        self.assertTrue(result["verified"])
        self.assertEqual(result["source"]["arguments"]["department_id"], own_department.id)
        self.assertIn(own_issue.id, result["source"]["record_ids"])
        self.assertNotIn(other_issue.id, result["source"]["record_ids"])
        router_decision = result["agent_trace"][0]["decision"]
        self.assertTrue(router_decision["rbac_scoped"])

    def test_validator_rejects_wrong_numeric_claim(self):
        validator = ValidatorAgent()
        verdict = validator.validate(
            {"tool_calls": [{"tool": "get_department_score", "raw_result": {"records": [{"total": 74.0}], "record_ids": [1]}}]},
            {"answer": "The score is 99/100.", "claims": [{"label": "total", "value": 99.0}]},
        )

        self.assertFalse(verdict["verified"])
        self.assertIn("Unsupported numeric claim", verdict["issues"][0])
