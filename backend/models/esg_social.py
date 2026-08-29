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
    department_id = fields.Many2one("esg.department", required=True, tracking=True)
    evidence_required = fields.Boolean(default=False)
    points = fields.Integer(default=0)
    capacity = fields.Integer(default=0, help="Zero means that participation is unlimited.")
    active = fields.Boolean(default=True)
    participation_ids = fields.One2many("esg.csr.participation", "activity_id")
    participant_count = fields.Integer(compute="_compute_participant_count")

    def _compute_participant_count(self):
        for activity in self:
            activity.participant_count = len(activity.participation_ids)

    @api.constrains("capacity", "points")
    def _check_nonnegative_values(self):
        for activity in self:
            if activity.capacity < 0 or activity.points < 0:
                raise ValidationError(_("Capacity and points cannot be negative."))


class ESGCSRParticipation(models.Model):
    _name = "esg.csr.participation"
    _description = "CSR Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    employee_id = fields.Many2one(
        "hr.employee", required=True, default=lambda self: self.env.user.employee_id
    )
    activity_id = fields.Many2one("esg.csr.activity", required=True, ondelete="cascade")
    proof = fields.Binary(attachment=True)
    proof_filename = fields.Char()
    submitted_at = fields.Datetime(readonly=True)
    reviewed_at = fields.Datetime(readonly=True)
    reviewed_by_id = fields.Many2one("res.users", readonly=True)
    approval_note = fields.Text()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft", required=True, tracking=True,
    )
    points_earned = fields.Integer(related="activity_id.points", readonly=True)
    completion_date = fields.Date(default=fields.Date.context_today)
    _sql_constraints = [
        (
            "esg_csr_employee_activity_unique",
            "unique(employee_id, activity_id)",
            "An employee can join an activity only once.",
        )
    ]

    @api.constrains("state", "proof", "activity_id")
    def _check_approval_evidence(self):
        require_evidence = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("eco_sphere_esg.require_csr_evidence", "False")
            == "True"
        )
        for participation in self:
            if (
                participation.state == "approved"
                and (require_evidence or participation.activity_id.evidence_required)
                and not participation.proof
            ):
                raise ValidationError(
                    _("Evidence is required before this participation can be approved.")
                )

    def action_submit(self):
        self.write({"state": "submitted", "submitted_at": fields.Datetime.now()})

    def action_approve(self):
        params = self.env["ir.config_parameter"].sudo()
        notify = params.get_param("eco_sphere_esg.csr_notifications", "True") == "True"
        for participation in self:
            participation.write({"state": "approved", "reviewed_at": fields.Datetime.now(), "reviewed_by_id": self.env.user.id})
            if notify:
                participation.message_post(
                    body=_(
                        "CSR participation approved for %s on activity '%s'."
                    ) % (participation.employee_id.name, participation.activity_id.name)
                )

    def action_reject(self):
        params = self.env["ir.config_parameter"].sudo()
        notify = params.get_param("eco_sphere_esg.csr_notifications", "True") == "True"
        self.write({"state": "rejected", "reviewed_at": fields.Datetime.now(), "reviewed_by_id": self.env.user.id})
        if notify:
            for participation in self:
                participation.message_post(
                    body=_("CSR participation rejected for %s.") % participation.employee_id.name
                )


class ESGDiversityMetric(models.Model):
    _name = "esg.diversity.metric"
    _description = "Diversity Metric"
    _order = "period desc, department_id"

    department_id = fields.Many2one("esg.department", required=True, index=True)
    metric_type = fields.Selection(
        [
            ("gender_representation", "Gender Representation"),
            ("age_distribution", "Age Distribution"),
            ("disability_inclusion", "Disability Inclusion"),
            ("nationality_mix", "Nationality Mix"),
            ("other", "Other"),
        ],
        required=True, default="gender_representation",
    )
    value = fields.Float(required=True)
    period = fields.Date(required=True, default=fields.Date.context_today, index=True)
    notes = fields.Text()

    @api.constrains("value")
    def _check_value(self):
        for record in self:
            if record.value < 0:
                raise ValidationError(_("A diversity metric cannot be negative."))


class ESGTrainingCompletion(models.Model):
    _name = "esg.training.completion"
    _description = "Training Completion"
    _order = "completion_date desc, id desc"

    name = fields.Char(required=True, string="Training")
    employee_id = fields.Many2one("hr.employee", required=True, index=True)
    department_id = fields.Many2one(
        related="employee_id.esg_department_id", store=True, readonly=True, index=True
    )
    completion_date = fields.Date(required=True, default=fields.Date.context_today)
    status = fields.Selection(
        [
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("expired", "Expired"),
        ],
        required=True, default="completed",
    )
    certificate = fields.Binary(attachment=True)
    certificate_filename = fields.Char()
    _sql_constraints = [
        (
            "esg_training_employee_course_unique",
            "unique(name, employee_id)",
            "This employee already has a completion record for this training.",
        ),
    ]
