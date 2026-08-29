from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ESGChallenge(models.Model):
    _name = "esg.challenge"
    _description = "Sustainability Challenge"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deadline asc, id desc"

    name = fields.Char(required=True)
    category_id = fields.Many2one("esg.category", domain=[("category_type", "=", "challenge")])
    description = fields.Html(required=True)
    xp_value = fields.Integer(required=True, default=0)
    difficulty = fields.Selection([("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")], required=True, default="medium")
    evidence_required = fields.Boolean(default=False)
    deadline = fields.Date(required=True)
    state = fields.Selection([("draft", "Draft"), ("active", "Active"), ("under_review", "Under Review"), ("completed", "Completed"), ("archived", "Archived")], required=True, default="draft", tracking=True)
    participation_ids = fields.One2many("esg.challenge.participation", "challenge_id")
    _sql_constraints = [("esg_challenge_xp_nonnegative", "CHECK(xp_value >= 0)", "XP cannot be negative.")]

    def action_activate(self): self.write({"state": "active"})
    def action_review(self): self.write({"state": "under_review"})
    def action_complete(self): self.write({"state": "completed"})
    def action_archive(self): self.write({"state": "archived"})


class ESGChallengeParticipation(models.Model):
    _name = "esg.challenge.participation"
    _description = "Challenge Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    challenge_id = fields.Many2one("esg.challenge", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True, default=lambda self: self.env.user.employee_id)
    progress = fields.Float(default=0.0, help="Completion percentage.")
    proof = fields.Binary(attachment=True)
    proof_filename = fields.Char()
    state = fields.Selection([("joined", "Joined"), ("under_review", "Under Review"), ("approved", "Approved"), ("rejected", "Rejected")], default="joined", tracking=True)
    xp_awarded = fields.Integer(default=0, readonly=True)
    _sql_constraints = [("esg_challenge_participation_unique", "unique(challenge_id, employee_id)", "An employee can join a challenge only once.")]

    @api.constrains("progress")
    def _check_progress(self):
        for record in self:
            if not 0 <= record.progress <= 100:
                raise ValidationError(_("Progress must be between 0 and 100."))

    def action_submit(self):
        for record in self:
            if record.challenge_id.evidence_required and not record.proof:
                raise ValidationError(_("This challenge requires evidence before submission."))
            record.state = "under_review"

    def action_approve(self):
        for record in self:
            record.write({"state": "approved", "xp_awarded": record.challenge_id.xp_value})
            record._auto_award_badges()

    def _auto_award_badges(self):
        if self.env["ir.config_parameter"].sudo().get_param("eco_sphere_esg.auto_award_badges", "True") != "True":
            return
        Badge = self.env["esg.badge"]
        for record in self:
            total_xp = sum(self.search([("employee_id", "=", record.employee_id.id), ("state", "=", "approved")]).mapped("xp_awarded"))
            completed = self.search_count([("employee_id", "=", record.employee_id.id), ("state", "=", "approved")])
            for badge in Badge.search([]):
                if total_xp >= badge.minimum_xp and completed >= badge.minimum_challenges:
                    Badge._grant(badge, record.employee_id)


class ESGBadge(models.Model):
    _name = "esg.badge"
    _description = "ESG Badge"

    name = fields.Char(required=True)
    description = fields.Text()
    icon = fields.Binary(attachment=True)
    minimum_xp = fields.Integer(default=0)
    minimum_challenges = fields.Integer(default=0)
    award_ids = fields.One2many("esg.badge.award", "badge_id")

    def _grant(self, employee):
        Award = self.env["esg.badge.award"]
        for badge in self:
            if not Award.search_count([("badge_id", "=", badge.id), ("employee_id", "=", employee.id)]):
                Award.create({"badge_id": badge.id, "employee_id": employee.id})


class ESGBadgeAward(models.Model):
    _name = "esg.badge.award"
    _description = "Badge Award"
    _order = "awarded_on desc"
    badge_id = fields.Many2one("esg.badge", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade")
    awarded_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    _sql_constraints = [("esg_badge_award_unique", "unique(badge_id, employee_id)", "Badge already awarded to this employee.")]


class ESGReward(models.Model):
    _name = "esg.reward"
    _description = "ESG Reward"
    name = fields.Char(required=True)
    description = fields.Text()
    points_required = fields.Integer(required=True)
    stock = fields.Integer(required=True, default=0)
    active = fields.Boolean(default=True)
    _sql_constraints = [("esg_reward_points_nonnegative", "CHECK(points_required >= 0)", "Required points cannot be negative."), ("esg_reward_stock_nonnegative", "CHECK(stock >= 0)", "Stock cannot be negative.")]
