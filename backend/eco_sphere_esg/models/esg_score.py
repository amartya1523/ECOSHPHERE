from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ESGDepartmentScore(models.Model):
    _name = "esg.department.score"
    _description = "Department ESG Score"
    _order = "score_date desc, total_score desc"

    department_id = fields.Many2one("esg.department", required=True, ondelete="cascade")
    score_date = fields.Date(required=True, default=fields.Date.context_today)
    environmental_score = fields.Float(default=0.0)
    social_score = fields.Float(default=0.0)
    governance_score = fields.Float(default=0.0)
    total_score = fields.Float(compute="_compute_total", store=True)
    _sql_constraints = [("esg_score_department_date_unique", "unique(department_id, score_date)", "One daily score is allowed per department.")]

    @api.depends("environmental_score", "social_score", "governance_score")
    def _compute_total(self):
        params = self.env["ir.config_parameter"].sudo()
        env_weight = float(params.get_param("eco_sphere_esg.environmental_weight", "40")) / 100
        social_weight = float(params.get_param("eco_sphere_esg.social_weight", "30")) / 100
        gov_weight = float(params.get_param("eco_sphere_esg.governance_weight", "30")) / 100
        for score in self:
            score.total_score = (score.environmental_score * env_weight + score.social_score * social_weight + score.governance_score * gov_weight)

    @api.model
    def _score_values_for_department(self, department, score_date):
        """Deterministic 0–100 rollup; lower carbon and fewer overdue issues score higher."""
        carbon_domain = [("department_id", "=", department.id), ("transaction_date", "<=", score_date)]
        carbon = self.env["esg.carbon.transaction"].read_group(carbon_domain, ["co2e_kg:sum"], [])[0].get("co2e_kg", 0.0)
        environmental = max(0.0, min(100.0, 100.0 - carbon / 10.0))

        activities = self.env["esg.csr.participation"].search_count([("activity_id.department_id", "=", department.id)])
        approved = self.env["esg.csr.participation"].search_count([("activity_id.department_id", "=", department.id), ("state", "=", "approved")])
        social = 0.0 if not activities else approved * 100.0 / activities

        issues = self.env["esg.compliance.issue"].search_count([("department_id", "=", department.id)])
        overdue = self.env["esg.compliance.issue"].search_count([("department_id", "=", department.id), ("is_overdue", "=", True)])
        governance = 100.0 if not issues else max(0.0, 100.0 - overdue * 100.0 / issues)
        return {"environmental_score": environmental, "social_score": social, "governance_score": governance}

    @api.model
    def action_recalculate_all(self):
        score_date = fields.Date.today()
        for department in self.env["esg.department"].search([]):
            values = self._score_values_for_department(department, score_date)
            score = self.search([("department_id", "=", department.id), ("score_date", "=", score_date)], limit=1)
            if score:
                score.write(values)
            else:
                self.create({"department_id": department.id, "score_date": score_date, **values})
        return True

    @api.model
    def _cron_recalculate_scores(self):
        return self.action_recalculate_all()

    @api.constrains("environmental_score", "social_score", "governance_score")
    def _check_score_range(self):
        for score in self:
            if any(not 0 <= value <= 100 for value in (score.environmental_score, score.social_score, score.governance_score)):
                raise ValidationError(_("Each ESG score must be between 0 and 100."))


class ESGRewardRedemption(models.Model):
    _name = "esg.reward.redemption"
    _description = "Reward Redemption"
    _inherit = ["mail.thread"]
    _order = "redeemed_on desc"

    employee_id = fields.Many2one("hr.employee", required=True, default=lambda self: self.env.user.employee_id)
    reward_id = fields.Many2one("esg.reward", required=True)
    points_spent = fields.Integer(related="reward_id.points_required", readonly=True)
    redeemed_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    state = fields.Selection([("requested", "Requested"), ("fulfilled", "Fulfilled"), ("cancelled", "Cancelled")], default="requested", required=True)

    @api.model_create_multi
    def create(self, values_list):
        records = super().create(values_list)
        for record in records:
            if record.reward_id.stock <= 0:
                raise ValidationError(_("This reward is out of stock."))
            available = self._employee_balance(record.employee_id)
            if available < record.reward_id.points_required:
                raise ValidationError(_("The employee does not have enough earned XP for this reward."))
            record.reward_id.stock -= 1
        return records

    def action_cancel(self):
        for record in self.filtered(lambda r: r.state == "requested"):
            record.reward_id.stock += 1
            record.state = "cancelled"

    @api.model
    def _employee_balance(self, employee):
        earned = sum(self.env["esg.challenge.participation"].search([("employee_id", "=", employee.id), ("state", "=", "approved")]).mapped("xp_awarded"))
        spent = sum(self.search([("employee_id", "=", employee.id), ("state", "in", ["requested", "fulfilled"])]).mapped("points_spent"))
        return earned - spent


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auto_emission_calculation = fields.Boolean(config_parameter="eco_sphere_esg.auto_emission_calculation")
    require_csr_evidence = fields.Boolean(config_parameter="eco_sphere_esg.require_csr_evidence")
    auto_award_badges = fields.Boolean(config_parameter="eco_sphere_esg.auto_award_badges")
    compliance_notifications = fields.Boolean(config_parameter="eco_sphere_esg.compliance_notifications")
    csr_notifications = fields.Boolean(config_parameter="eco_sphere_esg.csr_notifications", default=True)
    challenge_notifications = fields.Boolean(config_parameter="eco_sphere_esg.challenge_notifications", default=True)
    policy_notifications = fields.Boolean(config_parameter="eco_sphere_esg.policy_notifications", default=True)
    badge_notifications = fields.Boolean(config_parameter="eco_sphere_esg.badge_notifications", default=True)
    environmental_weight = fields.Float(config_parameter="eco_sphere_esg.environmental_weight", default=40.0)
    social_weight = fields.Float(config_parameter="eco_sphere_esg.social_weight", default=30.0)
    governance_weight = fields.Float(config_parameter="eco_sphere_esg.governance_weight", default=30.0)

    @api.constrains("environmental_weight", "social_weight", "governance_weight")
    def _check_weights(self):
        for setting in self:
            if round(setting.environmental_weight + setting.social_weight + setting.governance_weight, 2) != 100:
                raise ValidationError(_("ESG weights must add up to 100%."))
