import base64

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEcoSpherePhasesSixToTen(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env["esg.department"]
        cls.Employee = cls.env["hr.employee"]
        cls.Factor = cls.env["esg.emission.factor"]
        cls.Carbon = cls.env["esg.carbon.transaction"]
        cls.Activity = cls.env["esg.csr.activity"]
        cls.Participation = cls.env["esg.csr.participation"]
        cls.Diversity = cls.env["esg.diversity.metric"]
        cls.Training = cls.env["esg.training.completion"]
        cls.Policy = cls.env["esg.policy"]
        cls.Acknowledgement = cls.env["esg.policy.acknowledgement"]
        cls.Audit = cls.env["esg.audit"]
        cls.Issue = cls.env["esg.compliance.issue"]

    def _department(self, suffix):
        return self.Department.create({"name": "Department %s" % suffix, "code": "D%s" % suffix})

    def _employee(self, department, suffix):
        return self.Employee.create({"name": "Employee %s" % suffix, "esg_department_id": department.id})

    def test_phase_6_department_carbon_tracking_rollup(self):
        department = self._department("ENV")
        factor = self.Factor.create({"name": "Phase 6 factor", "source_type": "manual", "unit": "kWh", "co2e_factor": 0.5, "effective_from": fields.Date.today()})
        self.Carbon.create({"department_id": department.id, "emission_factor_id": factor.id, "quantity": 20, "transaction_date": fields.Date.today()})
        self.env.flush_all()
        self.env["esg.department.carbon.report"].invalidate_model()
        report = self.env["esg.department.carbon.report"].search([("department_id", "=", department.id)])
        self.assertEqual(len(report), 1)
        self.assertAlmostEqual(report.co2e_kg, 10.0)
        self.assertTrue(self.env.ref("eco_sphere_esg.action_esg_environmental_dashboard").exists())

    def test_phase_7_csr_evidence_required_for_approval(self):
        department = self._department("SOC")
        employee = self._employee(department, "SOC")
        self.env["ir.config_parameter"].sudo().set_param("eco_sphere_esg.require_csr_evidence", "True")
        activity = self.Activity.create({"name": "Tree planting", "department_id": department.id, "activity_date": fields.Date.today(), "points": 25})
        participation = self.Participation.create({"employee_id": employee.id, "activity_id": activity.id})
        with self.assertRaises(ValidationError):
            participation.action_approve()
        participation.write({"proof": base64.b64encode(b"proof"), "proof_filename": "proof.pdf"})
        participation.action_approve()
        self.assertEqual(participation.state, "approved")
        self.assertEqual(participation.points_earned, 25)

    def test_phase_8_diversity_and_training_are_department_filterable(self):
        department = self._department("MET")
        employee = self._employee(department, "MET")
        metric = self.Diversity.create({"department_id": department.id, "metric_type": "gender_representation", "value": 48.5, "period": fields.Date.today()})
        training = self.Training.create({"name": "Code of Conduct", "employee_id": employee.id})
        self.assertEqual(metric.department_id, department)
        self.assertEqual(training.department_id, department)

    def test_phase_9_policy_acknowledgement(self):
        department = self._department("POL")
        employee = self._employee(department, "POL")
        policy = self.Policy.create({"name": "Supplier Policy", "reference": "POL-%s" % department.id, "content": "<p>Policy content</p>", "effective_date": fields.Date.today()})
        policy.action_make_effective()
        acknowledgement = self.Acknowledgement.create({"policy_id": policy.id, "employee_id": employee.id})
        acknowledgement.action_acknowledge()
        self.assertEqual(acknowledgement.state, "acknowledged")
        self.assertTrue(acknowledgement.acknowledged_on)

    def test_phase_10_compliance_owner_due_date_and_overdue_cron(self):
        department = self._department("GOV")
        employee = self._employee(department, "GOV")
        audit = self.Audit.create({"name": "Safety Audit", "department_id": department.id, "auditor_id": employee.id, "audit_date": fields.Date.today()})
        with self.assertRaises(ValidationError):
            self.Issue.create({"name": "Missing owner", "audit_id": audit.id, "department_id": department.id, "description": "<p>Issue</p>", "due_date": fields.Date.today()})
        issue = self.Issue.create({"name": "Past-due issue", "audit_id": audit.id, "department_id": department.id, "description": "<p>Issue</p>", "owner_id": employee.id, "due_date": fields.Date.subtract(fields.Date.today(), days=1)})
        self.Issue._cron_update_overdue()
        self.assertTrue(issue.is_overdue)
        issue.action_resolve()
        self.assertFalse(issue.is_overdue)
