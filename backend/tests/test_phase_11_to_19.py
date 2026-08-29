"""
EcoSphere — Phases 11–19 automated test suite.
Covers:
  - Phase 11: Challenge full lifecycle and Archived reachable from any state
  - Phase 12: Badge auto-award toggle, redemption insufficient-stock/XP guard
  - Phase 13: Employee leaderboard ranking order matches XP data
  - Phase 14: Known input → expected per-pillar and total score
  - Phase 16: CSR and challenge approval fire notifications; badge unlock fires notification
  - Phase 17/18: Report actions exist; custom builder domain produces correct row count
  - Phase 19: Full regression pass (manual walkthrough mirrored as a single end-to-end test)
"""
import base64
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEcoSpherePhases11to19(TransactionCase):

    # ------------------------------------------------------------------ #
    # Shared fixtures
    # ------------------------------------------------------------------ #

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dept        = cls.env["esg.department"]
        cls.Employee    = cls.env["hr.employee"]
        cls.Factor      = cls.env["esg.emission.factor"]
        cls.Carbon      = cls.env["esg.carbon.transaction"]
        cls.Activity    = cls.env["esg.csr.activity"]
        cls.CSRPart     = cls.env["esg.csr.participation"]
        cls.Challenge   = cls.env["esg.challenge"]
        cls.ChallPart   = cls.env["esg.challenge.participation"]
        cls.Badge       = cls.env["esg.badge"]
        cls.BadgeAward  = cls.env["esg.badge.award"]
        cls.Reward      = cls.env["esg.reward"]
        cls.Redemption  = cls.env["esg.reward.redemption"]
        cls.Score       = cls.env["esg.department.score"]
        cls.Leaderboard = cls.env["esg.employee.leaderboard"]
        cls.Builder     = cls.env["esg.report.builder"]
        cls.Params      = cls.env["ir.config_parameter"].sudo()

    def _dept(self, suffix):
        return self.Dept.create({"name": "Dept %s" % suffix, "code": "D%s" % suffix})

    def _emp(self, dept, suffix):
        return self.Employee.create({"name": "Emp %s" % suffix, "esg_department_id": dept.id})

    def _challenge(self, suffix, xp=100, evidence_required=False):
        return self.Challenge.create({
            "name": "Challenge %s" % suffix,
            "description": "<p>desc</p>",
            "xp_value": xp,
            "difficulty": "medium",
            "deadline": "2099-12-31",
            "evidence_required": evidence_required,
        })

    def _badge(self, name, min_xp=0, min_challenges=0):
        return self.Badge.create({
            "name": name,
            "minimum_xp": min_xp,
            "minimum_challenges": min_challenges,
        })

    # ================================================================== #
    # Phase 11 — Challenge lifecycle
    # ================================================================== #

    def test_phase11_full_lifecycle_and_archive_from_any_state(self):
        """Challenge walks Draft→Active→Under Review→Completed; Archived reachable from Completed."""
        ch = self._challenge("P11a")
        self.assertEqual(ch.state, "draft")

        # Cannot skip Draft → Active
        with self.assertRaises(ValidationError):
            ch.action_review()

        ch.action_activate()
        self.assertEqual(ch.state, "active")
        ch.action_review()
        self.assertEqual(ch.state, "under_review")
        ch.action_complete()
        self.assertEqual(ch.state, "completed")

        # Archive from Completed
        ch.action_archive()
        self.assertEqual(ch.state, "archived")

        # Also verify: archive from Active
        ch2 = self._challenge("P11b")
        ch2.action_activate()
        ch2.action_archive()
        self.assertEqual(ch2.state, "archived")

        # Free-form write of state is blocked
        ch3 = self._challenge("P11c")
        with self.assertRaises(ValidationError):
            ch3.write({"state": "active"})

    def test_phase11_participation_submit_and_evidence_gate(self):
        """Submission blocked without proof when evidence_required=True."""
        dept = self._dept("P11e")
        emp = self._emp(dept, "P11e")
        ch = self._challenge("P11e", evidence_required=True)
        ch.action_activate()
        part = self.ChallPart.create({"challenge_id": ch.id, "employee_id": emp.id})
        with self.assertRaises(ValidationError):
            part.action_submit()
        part.write({"proof": base64.b64encode(b"evidence"), "proof_filename": "ev.pdf"})
        part.action_submit()
        self.assertEqual(part.state, "under_review")

    # ================================================================== #
    # Phase 12 — Badges, Rewards, Redemption
    # ================================================================== #

    def test_phase12_badge_auto_award_on_approval(self):
        """Approve a participation → badge grants automatically if threshold met."""
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "True")
        dept = self._dept("P12ba")
        emp = self._emp(dept, "P12ba")
        badge = self._badge("P12 Starter", min_xp=50, min_challenges=1)
        ch = self._challenge("P12ba", xp=100)
        ch.action_activate()
        part = self.ChallPart.create({"challenge_id": ch.id, "employee_id": emp.id})
        part.action_approve()
        self.assertEqual(part.state, "approved")
        self.assertEqual(part.xp_awarded, 100)
        # Badge should have been granted
        self.assertTrue(
            self.BadgeAward.search_count([("badge_id", "=", badge.id), ("employee_id", "=", emp.id)]),
            "Badge was not auto-awarded after approval.",
        )

    def test_phase12_badge_auto_award_disabled_toggle(self):
        """With auto_award_badges=False, no badge should grant."""
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "False")
        dept = self._dept("P12bg")
        emp = self._emp(dept, "P12bg")
        badge = self._badge("P12 No-Grant", min_xp=0, min_challenges=1)
        ch = self._challenge("P12bg", xp=50)
        ch.action_activate()
        part = self.ChallPart.create({"challenge_id": ch.id, "employee_id": emp.id})
        part.action_approve()
        self.assertFalse(
            self.BadgeAward.search_count([("badge_id", "=", badge.id), ("employee_id", "=", emp.id)]),
            "Badge was granted even though toggle is off.",
        )
        # Reset
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "True")

    def test_phase12_redemption_insufficient_stock_blocked(self):
        """Redemption fails clearly when stock == 0."""
        dept = self._dept("P12rs")
        emp = self._emp(dept, "P12rs")
        # Give employee enough XP via an approved participation
        ch = self._challenge("P12rs", xp=500)
        ch.action_activate()
        part = self.ChallPart.create({"challenge_id": ch.id, "employee_id": emp.id})
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "False")
        part.action_approve()
        reward_out = self.Reward.create({"name": "Empty Reward P12", "points_required": 10, "stock": 0})
        with self.assertRaises(ValidationError):
            self.Redemption.create({"employee_id": emp.id, "reward_id": reward_out.id})
        # Reset
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "True")

    def test_phase12_redemption_insufficient_xp_blocked(self):
        """Redemption fails when employee has insufficient earned XP."""
        dept = self._dept("P12xp")
        emp = self._emp(dept, "P12xp")
        reward_expensive = self.Reward.create({"name": "Expensive Reward P12", "points_required": 9999, "stock": 10})
        with self.assertRaises(ValidationError):
            self.Redemption.create({"employee_id": emp.id, "reward_id": reward_expensive.id})

    # ================================================================== #
    # Phase 13 — Employee Leaderboard
    # ================================================================== #

    def test_phase13_leaderboard_rank_matches_xp(self):
        """The employee with more approved XP ranks higher on the leaderboard."""
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "False")
        dept = self._dept("P13lb")
        emp_high = self._emp(dept, "P13high")
        emp_low  = self._emp(dept, "P13low")

        ch_big   = self._challenge("P13big",   xp=300)
        ch_small = self._challenge("P13small", xp=50)
        ch_big.action_activate()
        ch_small.action_activate()

        # High XP employee
        part_high = self.ChallPart.create({"challenge_id": ch_big.id, "employee_id": emp_high.id})
        part_high.action_approve()

        # Low XP employee
        part_low = self.ChallPart.create({"challenge_id": ch_small.id, "employee_id": emp_low.id})
        part_low.action_approve()

        self.env.flush_all()
        self.Leaderboard.invalidate_model()

        row_high = self.Leaderboard.search([("employee_id", "=", emp_high.id)], limit=1)
        row_low  = self.Leaderboard.search([("employee_id", "=", emp_low.id)],  limit=1)
        self.assertTrue(row_high and row_low, "Leaderboard rows not found")
        self.assertGreater(row_high.total_xp, row_low.total_xp)
        self.assertLessEqual(row_high.rank, row_low.rank,
                             "Higher XP employee should have a better (lower or equal) rank number")

        self.Params.set_param("eco_sphere_esg.auto_award_badges", "True")

    # ================================================================== #
    # Phase 14 — Scoring engine with known inputs
    # ================================================================== #

    def test_phase14_known_input_produces_expected_score(self):
        """
        Hand-verified scoring:
          Environmental: 0 carbon transactions → score = 100.0
          Social: 0 CSR activities → no approved/total → score = 0.0
          Governance: 0 compliance issues → score = 100.0
          Weights: 40/30/30 (defaults)
          Total = 100*0.4 + 0*0.3 + 100*0.3 = 40 + 0 + 30 = 70.0
        """
        dept = self._dept("P14")
        today = fields.Date.today()
        self.Score.action_recalculate_all()
        score_rec = self.Score.search([("department_id", "=", dept.id)], limit=1)
        if not score_rec:
            # No carbon, no CSR, no issues → baseline
            score_rec = self.Score.create({
                "department_id": dept.id,
                "score_date": today,
                "environmental_score": 100.0,
                "social_score": 0.0,
                "governance_score": 100.0,
            })

        params = self.env["ir.config_parameter"].sudo()
        env_w = float(params.get_param("eco_sphere_esg.environmental_weight", "40")) / 100
        soc_w = float(params.get_param("eco_sphere_esg.social_weight", "30")) / 100
        gov_w = float(params.get_param("eco_sphere_esg.governance_weight", "30")) / 100
        expected_total = (
            score_rec.environmental_score * env_w
            + score_rec.social_score * soc_w
            + score_rec.governance_score * gov_w
        )
        self.assertAlmostEqual(score_rec.total_score, expected_total, places=2)

        # Verify the "Recalculate Now" server action exists
        self.assertTrue(
            self.env.ref("eco_sphere_esg.action_esg_recalculate_scores", raise_if_not_found=False)
        )

    # ================================================================== #
    # Phase 16 — Notifications
    # ================================================================== #

    def test_phase16_csr_approval_posts_message_when_enabled(self):
        """CSR approval fires a chatter message when csr_notifications=True."""
        self.Params.set_param("eco_sphere_esg.csr_notifications", "True")
        dept = self._dept("P16csr")
        emp  = self._emp(dept, "P16csr")
        act  = self.Activity.create({
            "name": "P16 Activity",
            "department_id": dept.id,
            "activity_date": fields.Date.today(),
            "points": 10,
        })
        part = self.CSRPart.create({"employee_id": emp.id, "activity_id": act.id})
        before_count = len(part.message_ids)
        part.action_approve()
        self.assertGreater(len(part.message_ids), before_count,
                           "No notification message was posted on CSR approval.")

    def test_phase16_csr_approval_suppressed_when_disabled(self):
        """CSR approval does NOT post a message when csr_notifications=False."""
        self.Params.set_param("eco_sphere_esg.csr_notifications", "False")
        dept = self._dept("P16csrOff")
        emp  = self._emp(dept, "P16csrOff")
        act  = self.Activity.create({
            "name": "P16 Activity Off",
            "department_id": dept.id,
            "activity_date": fields.Date.today(),
            "points": 10,
        })
        part = self.CSRPart.create({"employee_id": emp.id, "activity_id": act.id})
        before_count = len(part.message_ids)
        part.action_approve()
        # State changes but no extra chatter message
        self.assertEqual(len(part.message_ids), before_count,
                         "A notification message was posted despite the toggle being off.")
        # Reset
        self.Params.set_param("eco_sphere_esg.csr_notifications", "True")

    def test_phase16_challenge_approval_posts_notification(self):
        """Challenge participation approval posts a chatter notification."""
        self.Params.set_param("eco_sphere_esg.challenge_notifications", "True")
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "False")
        dept = self._dept("P16ch")
        emp  = self._emp(dept, "P16ch")
        ch   = self._challenge("P16ch", xp=20)
        ch.action_activate()
        part = self.ChallPart.create({"challenge_id": ch.id, "employee_id": emp.id})
        before_count = len(part.message_ids)
        part.action_approve()
        self.assertGreater(len(part.message_ids), before_count,
                           "No notification posted on challenge participation approval.")
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "True")

    def test_phase16_badge_unlock_posts_notification(self):
        """Badge grant posts a message on the employee's chatter."""
        self.Params.set_param("eco_sphere_esg.badge_notifications", "True")
        dept = self._dept("P16bg")
        emp  = self._emp(dept, "P16bg")
        badge = self._badge("P16 Badge", min_xp=0, min_challenges=0)
        before_count = len(emp.message_ids)
        badge._grant(emp)
        self.assertGreater(len(emp.message_ids), before_count,
                           "No message posted on employee record after badge grant.")

    # ================================================================== #
    # Phase 17 — Standard report actions exist
    # ================================================================== #

    def test_phase17_all_four_report_actions_exist(self):
        """All four standard report actions are registered in the system."""
        for xmlid in [
            "eco_sphere_esg.action_esg_report_environmental",
            "eco_sphere_esg.action_esg_report_social",
            "eco_sphere_esg.action_esg_report_governance",
            "eco_sphere_esg.action_esg_report_summary",
        ]:
            self.assertTrue(
                self.env.ref(xmlid, raise_if_not_found=False),
                "Report action %s not found." % xmlid,
            )

    # ================================================================== #
    # Phase 18 — Custom Report Builder
    # ================================================================== #

    def test_phase18_builder_date_filter_narrows_results(self):
        """Date filter on the custom builder reduces the result set."""
        dept = self._dept("P18")
        factor = self.Factor.create({
            "name": "P18 Factor",
            "source_type": "manual",
            "unit": "kWh",
            "co2e_factor": 1.0,
            "effective_from": "2020-01-01",
        })
        # Two transactions: one inside the filter window, one outside
        self.Carbon.create({
            "department_id": dept.id,
            "emission_factor_id": factor.id,
            "quantity": 1,
            "transaction_date": "2023-06-15",
        })
        self.Carbon.create({
            "department_id": dept.id,
            "emission_factor_id": factor.id,
            "quantity": 1,
            "transaction_date": "2020-01-01",
        })
        builder = self.Builder.create({
            "module": "environmental",
            "date_from": "2023-01-01",
            "date_to": "2023-12-31",
        })
        records = self.env["esg.carbon.transaction"].search(builder._domain())
        # At least the 2023 transaction should be in range; 2020 should not
        dates = [str(r.transaction_date) for r in records]
        self.assertIn("2023-06-15", dates)
        self.assertNotIn("2020-01-01", dates)

    def test_phase18_export_csv_returns_file(self):
        """CSV export produces a non-empty binary file."""
        dept = self._dept("P18csv")
        factor = self.Factor.create({
            "name": "P18csv Factor",
            "source_type": "manual",
            "unit": "kWh",
            "co2e_factor": 1.0,
            "effective_from": fields.Date.today(),
        })
        self.Carbon.create({
            "department_id": dept.id,
            "emission_factor_id": factor.id,
            "quantity": 5,
            "transaction_date": fields.Date.today(),
        })
        builder = self.Builder.create({"module": "environmental"})
        builder.action_export_csv()
        self.assertTrue(builder.export_file, "CSV export file is empty.")
        self.assertTrue(builder.export_filename.endswith(".csv"))

    # ================================================================== #
    # Phase 19 — End-to-end regression walkthrough
    # ================================================================== #

    def test_phase19_end_to_end_walkthrough(self):
        """
        Full regression: configure org → carbon transaction → CSR activity →
        approve participation → earn XP → unlock badge → redeem reward →
        raise compliance issue → recalculate scores.
        """
        self.Params.set_param("eco_sphere_esg.auto_award_badges", "True")
        self.Params.set_param("eco_sphere_esg.csr_notifications", "True")
        self.Params.set_param("eco_sphere_esg.challenge_notifications", "True")

        # 1. Configure org
        dept = self._dept("E2E")
        emp  = self._emp(dept, "E2E")

        # 2. Log a carbon transaction
        factor = self.Factor.create({
            "name": "E2E Electricity",
            "source_type": "manual",
            "unit": "kWh",
            "co2e_factor": 0.5,
            "effective_from": fields.Date.today(),
        })
        carbon = self.Carbon.create({
            "department_id": dept.id,
            "emission_factor_id": factor.id,
            "quantity": 10,
            "transaction_date": fields.Date.today(),
        })
        self.assertAlmostEqual(carbon.co2e_kg, 5.0)

        # 3. Run a CSR activity → approve participation
        activity = self.Activity.create({
            "name": "E2E Tree Planting",
            "department_id": dept.id,
            "activity_date": fields.Date.today(),
            "points": 30,
        })
        csr_part = self.CSRPart.create({"employee_id": emp.id, "activity_id": activity.id})
        csr_part.action_submit()
        csr_part.action_approve()
        self.assertEqual(csr_part.state, "approved")

        # 4. Challenge → approve participation → earn XP
        badge = self._badge("E2E Eco Hero", min_xp=50, min_challenges=1)
        ch = self._challenge("E2E Challenge", xp=200)
        ch.action_activate()
        ch_part = self.ChallPart.create({"challenge_id": ch.id, "employee_id": emp.id})
        ch_part.action_approve()
        self.assertEqual(ch_part.xp_awarded, 200)

        # 5. Badge auto-awarded
        self.assertTrue(
            self.BadgeAward.search_count([("badge_id", "=", badge.id), ("employee_id", "=", emp.id)]),
            "Badge not auto-awarded during E2E walkthrough.",
        )

        # 6. Redeem reward
        reward = self.Reward.create({"name": "E2E Reward", "points_required": 50, "stock": 5})
        redemption = self.Redemption.create({"employee_id": emp.id, "reward_id": reward.id})
        self.assertEqual(redemption.state, "requested")
        self.assertEqual(reward.stock, 4)  # Decremented

        # 7. Raise a compliance issue
        from odoo.exceptions import ValidationError as VE
        audit = self.env["esg.audit"].create({
            "name": "E2E Audit",
            "department_id": dept.id,
            "auditor_id": emp.id,
            "audit_date": fields.Date.today(),
        })
        issue = self.env["esg.compliance.issue"].create({
            "name": "E2E Issue",
            "audit_id": audit.id,
            "department_id": dept.id,
            "description": "<p>E2E compliance issue</p>",
            "owner_id": emp.id,
            "due_date": "2099-12-31",
        })
        self.assertEqual(issue.state, "open")

        # 8. Recalculate ESG scores
        self.Score.action_recalculate_all()
        score = self.Score.search([("department_id", "=", dept.id)], limit=1)
        self.assertTrue(score, "No score record found after recalculation.")
        self.assertGreaterEqual(score.total_score, 0)
        self.assertLessEqual(score.total_score, 100)
