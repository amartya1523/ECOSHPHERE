from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ESGCSRActivity(models.Model):
    _name = "esg.csr.activity"
    _description = "CSR Activity"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "activity_date desc, id desc"

    name = fields.Char(required=True, tracking=True)
    category_id = fields.Many2one("esg.category", domain=[("category_type", "=", "csr")])
    description = fields.Html()
    activity_date = fields.Date(required=True, default=fields.Date.context_today)
    evidence_required = fields.Boolean(default=False)
    points = fields.Integer(default=0)
    active = fields.Boolean(default=True)
    participation_ids = fields.One2many("esg.csr.participation", "activity_id")
    participant_count = fields.Integer(compute="_compute_participant_count")

    def _compute_participant_count(self):
        for activity in self:
            activity.participant_count = len(activity.participation_ids)


class ESGCSRParticipation(models.Model):
    _name = "esg.csr.participation"
    _description = "CSR Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    employee_id = fields.Many2one("hr.employee", required=True, default=lambda self: self.env.user.employee_id)
    activity_id = fields.Many2one("esg.csr.activity", required=True, ondelete="cascade")
    proof = fields.Binary(attachment=True)
    proof_filename = fields.Char()
    state = fields.Selection([("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", tracking=True)
    points_earned = fields.Integer(related="activity_id.points", readonly=True)
    completion_date = fields.Date(default=fields.Date.context_today)
    _sql_constraints = [("esg_csr_employee_activity_unique", "unique(employee_id, activity_id)", "An employee can join an activity only once.")]

    def action_approve(self):
        require_evidence = self.env["ir.config_parameter"].sudo().get_param("eco_sphere_esg.require_csr_evidence", "False") == "True"
        for participation in self:
            if (require_evidence or participation.activity_id.evidence_required) and not participation.proof:
                raise ValidationError(_("Evidence is required before this participation can be approved."))
            participation.state = "approved"
            participation.message_post(body=_("Participation approved."))

    def action_reject(self):
        self.write({"state": "rejected"})
        self.message_post(body=_("Participation rejected."))
