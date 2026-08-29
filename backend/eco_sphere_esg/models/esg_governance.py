from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ESGPolicy(models.Model):
    _name = "esg.policy"
    _description = "ESG Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, name"

    name = fields.Char(required=True)
    reference = fields.Char(required=True, copy=False)
    content = fields.Html(required=True)
    effective_date = fields.Date(required=True, default=fields.Date.context_today)
    active = fields.Boolean(default=True)
    acknowledgement_ids = fields.One2many("esg.policy.acknowledgement", "policy_id")
    _sql_constraints = [("esg_policy_reference_unique", "unique(reference)", "Policy reference must be unique.")]


class ESGPolicyAcknowledgement(models.Model):
    _name = "esg.policy.acknowledgement"
    _description = "Policy Acknowledgement"
    _inherit = ["mail.thread"]
    _order = "acknowledged_on desc"

    policy_id = fields.Many2one("esg.policy", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True, default=lambda self: self.env.user.employee_id)
    acknowledged_on = fields.Datetime(readonly=True)
    state = fields.Selection([("pending", "Pending"), ("acknowledged", "Acknowledged")], default="pending", required=True)
    _sql_constraints = [("esg_policy_employee_unique", "unique(policy_id, employee_id)", "This employee has already been assigned this policy.")]

    def action_acknowledge(self):
        self.write({"state": "acknowledged", "acknowledged_on": fields.Datetime.now()})


class ESGAudit(models.Model):
    _name = "esg.audit"
    _description = "ESG Audit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "audit_date desc"

    name = fields.Char(required=True)
    department_id = fields.Many2one("esg.department", required=True)
    auditor_id = fields.Many2one("hr.employee", required=True)
    audit_date = fields.Date(required=True, default=fields.Date.context_today)
    findings = fields.Text()
    state = fields.Selection([("under_review", "Under Review"), ("completed", "Completed")], default="under_review", required=True)
    issue_ids = fields.One2many("esg.compliance.issue", "audit_id")


class ESGComplianceIssue(models.Model):
    _name = "esg.compliance.issue"
    _description = "Compliance Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "is_overdue desc, due_date asc"

    name = fields.Char(required=True)
    audit_id = fields.Many2one("esg.audit", ondelete="set null")
    department_id = fields.Many2one("esg.department", required=True)
    severity = fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], required=True, default="medium", tracking=True)
    description = fields.Html(required=True)
    owner_id = fields.Many2one("hr.employee", required=True, tracking=True)
    due_date = fields.Date(required=True, tracking=True)
    state = fields.Selection([("open", "Open"), ("resolved", "Resolved")], required=True, default="open", tracking=True)
    is_overdue = fields.Boolean(compute="_compute_is_overdue", search="_search_is_overdue")
    resolved_on = fields.Datetime(readonly=True)

    @api.depends("state", "due_date")
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for issue in self:
            issue.is_overdue = issue.state == "open" and bool(issue.due_date and issue.due_date < today)

    def _search_is_overdue(self, operator, value):
        if (operator, value) in [("=", True), ("!=", False)]:
            return [("state", "=", "open"), ("due_date", "<", fields.Date.today())]
        return ["|", ("state", "!=", "open"), ("due_date", ">=", fields.Date.today())]

    @api.model_create_multi
    def create(self, values_list):
        issues = super().create(values_list)
        if self.env["ir.config_parameter"].sudo().get_param("eco_sphere_esg.compliance_notifications", "True") == "True":
            for issue in issues:
                issue.message_post(body=_("New compliance issue raised. Owner: %s") % issue.owner_id.name)
        return issues

    def action_resolve(self):
        self.write({"state": "resolved", "resolved_on": fields.Datetime.now()})
