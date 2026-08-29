import base64
import json
import os
from urllib import request as urlrequest

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
    difficulty = fields.Selection(
        [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
        required=True, default="medium",
    )
    evidence_required = fields.Boolean(default=False)
    is_template = fields.Boolean(default=False, index=True, help="Private reusable challenge blueprint for administrators.")
    challenge_type = fields.Selection([
        ("quiz", "Knowledge quiz"), ("scenario", "Decision scenario"),
        ("checklist", "Action checklist"), ("photo", "Photo evidence"),
        ("action", "Self-reported action"),
    ], required=True, default="action")
    game_config = fields.Json(default=dict, help="Challenge rules and content. Correct quiz answers never leave the server.")
    deadline = fields.Date(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("under_review", "Under Review"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        required=True, default="draft", tracking=True,
    )
    participation_ids = fields.One2many("esg.challenge.participation", "challenge_id")
    _sql_constraints = [("esg_challenge_xp_nonnegative", "CHECK(xp_value >= 0)", "XP cannot be negative.")]

    def _transition(self, target, allowed):
        if any(record.state not in allowed for record in self):
            raise ValidationError(_("This challenge cannot move to the requested state."))
        self.with_context(esg_state_action=True).write({"state": target})

    def action_activate(self):
        self._transition("active", {"draft"})

    def action_review(self):
        self._transition("under_review", {"active"})

    def action_complete(self):
        self._transition("completed", {"under_review"})

    def action_archive(self):
        # Archived is reachable from any prior state
        self.with_context(esg_state_action=True).write({"state": "archived"})

    def write(self, values):
        if "state" in values and not self.env.context.get("esg_state_action"):
            raise ValidationError(_("Use the challenge action buttons to change its lifecycle state."))
        return super().write(values)


class ESGChallengeParticipation(models.Model):
    _name = "esg.challenge.participation"
    _description = "Challenge Participation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    challenge_id = fields.Many2one("esg.challenge", required=True, ondelete="cascade")
    employee_id = fields.Many2one(
        "hr.employee", required=True, default=lambda self: self.env.user.employee_id
    )
    progress = fields.Float(default=0.0, help="Completion percentage.")
    proof = fields.Binary(attachment=True)
    proof_filename = fields.Char()
    state = fields.Selection(
        [
            ("joined", "Joined"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="joined", tracking=True,
    )
    xp_awarded = fields.Integer(default=0, readonly=True)
    activity_data = fields.Json(default=dict, readonly=True)
    attempt_count = fields.Integer(default=0, readonly=True)
    eligibility_status = fields.Selection([
        ("not_started", "Not started"), ("pending_review", "Pending review"),
        ("eligible", "Eligible"), ("not_eligible", "Not eligible"),
    ], default="not_started", readonly=True)
    verification_reason = fields.Text(readonly=True)
    _sql_constraints = [
        (
            "esg_challenge_participation_unique",
            "unique(challenge_id, employee_id)",
            "An employee can join a challenge only once.",
        )
    ]

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
        params = self.env["ir.config_parameter"].sudo()
        notify = params.get_param("eco_sphere_esg.challenge_notifications", "True") == "True"
        for record in self:
            record.write({"state": "approved", "eligibility_status": "eligible", "xp_awarded": record.challenge_id.xp_value})
            if notify:
                record.message_post(
                    body=_(
                        "Challenge participation approved. %s XP awarded to %s."
                    ) % (record.xp_awarded, record.employee_id.name)
                )
            record._auto_award_badges()

    def action_reject(self):
        params = self.env["ir.config_parameter"].sudo()
        notify = params.get_param("eco_sphere_esg.challenge_notifications", "True") == "True"
        for record in self:
            record.write({"state": "rejected", "eligibility_status": "not_eligible"})
            if notify:
                record.message_post(
                    body=_("Challenge participation rejected for %s.") % record.employee_id.name
                )

    def _award(self):
        """Approve a verified activity once, then award its configured XP."""
        for record in self:
            if record.state == "approved":
                continue
            record.write({
                "state": "approved", "eligibility_status": "eligible",
                "xp_awarded": record.challenge_id.xp_value,
            })
            record._auto_award_badges()

    def _validate_photo_with_vision(self, proof, filename):
        """Use configured server-side vision, otherwise require an honest human review."""
        self.ensure_one()
        if not proof:
            return "pending_review", _("No photo was received; an administrator must review this submission."), 0.0
        params = self.env["ir.config_parameter"].sudo()
        api_key = params.get_param("eco_sphere_esg.vision_api_key") or os.getenv("ECOSPHERE_VISION_API_KEY")
        if not api_key:
            return "pending_review", _("Photo received. Automatic plant verification is not configured, so this is waiting for administrator review."), 0.0
        try:
            image_data = proof.decode() if isinstance(proof, bytes) else proof
            prompt = (self.challenge_id.game_config or {}).get("vision_prompt") or "Does this image clearly contain a real plant?"
            payload = {
                "model": params.get_param("eco_sphere_esg.vision_model", "gpt-4.1-mini"),
                "input": [{"role": "user", "content": [
                    {"type": "input_text", "text": f"{prompt} Return only JSON: {{\"eligible\": true|false, \"confidence\": 0-1, \"reason\": \"short explanation\"}}."},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_data}"},
                ]}],
            }
            req = urlrequest.Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
            response = json.loads(urlrequest.urlopen(req, timeout=20).read().decode())
            text = response.get("output_text", "")
            if not text:
                text = "".join(part.get("text", "") for output in response.get("output", []) for part in output.get("content", []) if part.get("type") == "output_text")
            text = text.strip().removeprefix("```json").removesuffix("```").strip()
            verdict = json.loads(text)
            confidence = float(verdict.get("confidence", 0))
            reason = str(verdict.get("reason") or _("Image reviewed."))[:500]
            if verdict.get("eligible") is True and confidence >= 0.80:
                return "eligible", reason, confidence
            return "not_eligible", reason or _("A plant could not be confidently verified in this photo."), confidence
        except Exception:
            return "pending_review", _("Photo received, but automated verification was unavailable. It is waiting for administrator review."), 0.0

    def _auto_award_badges(self):
        """Check if any badges should be unlocked after this approval."""
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("eco_sphere_esg.auto_award_badges", "True")
            != "True"
        ):
            return
        for record in self:
            approved = self.search(
                [("employee_id", "=", record.employee_id.id), ("state", "=", "approved")]
            )
            total_xp = sum(approved.mapped("xp_awarded"))
            completed = len(approved)
            for badge in self.env["esg.badge"].search([]):
                if total_xp >= badge.minimum_xp and completed >= badge.minimum_challenges:
                    badge._grant(record.employee_id)


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
        """Grant this badge to an employee if they do not already have it."""
        Award = self.env["esg.badge.award"]
        notify = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("eco_sphere_esg.badge_notifications", "True")
            == "True"
        )
        for badge in self:
            if not Award.search_count([("badge_id", "=", badge.id), ("employee_id", "=", employee.id)]):
                Award.create({"badge_id": badge.id, "employee_id": employee.id})
                if notify:
                    employee.message_post(
                        body=_("You unlocked the EcoSphere badge: %s") % badge.name
                    )

    @api.model
    def _cron_auto_award_badges(self):
        """Nightly cron: check all employees against all badge unlock rules."""
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("eco_sphere_esg.auto_award_badges", "True")
            != "True"
        ):
            return True
        Participation = self.env["esg.challenge.participation"]
        for employee in self.env["hr.employee"].search([]):
            approved = Participation.search(
                [("employee_id", "=", employee.id), ("state", "=", "approved")]
            )
            xp = sum(approved.mapped("xp_awarded"))
            for badge in self.search([]):
                if xp >= badge.minimum_xp and len(approved) >= badge.minimum_challenges:
                    badge._grant(employee)
        return True


class ESGBadgeAward(models.Model):
    _name = "esg.badge.award"
    _description = "Badge Award"
    _order = "awarded_on desc"

    badge_id = fields.Many2one("esg.badge", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade")
    awarded_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    _sql_constraints = [
        (
            "esg_badge_award_unique",
            "unique(badge_id, employee_id)",
            "Badge already awarded to this employee.",
        )
    ]


class ESGReward(models.Model):
    _name = "esg.reward"
    _description = "ESG Reward"

    name = fields.Char(required=True)
    description = fields.Text()
    points_required = fields.Integer(required=True)
    stock = fields.Integer(required=True, default=0)
    active = fields.Boolean(default=True)
    _sql_constraints = [
        ("esg_reward_points_nonnegative", "CHECK(points_required >= 0)", "Required points cannot be negative."),
        ("esg_reward_stock_nonnegative", "CHECK(stock >= 0)", "Stock cannot be negative."),
    ]
