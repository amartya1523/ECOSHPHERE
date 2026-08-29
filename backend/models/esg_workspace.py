from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    esg_environmental_weight = fields.Float(default=40.0)
    esg_social_weight = fields.Float(default=30.0)
    esg_governance_weight = fields.Float(default=30.0)
    esg_auto_emission_calculation = fields.Boolean(default=False)
    esg_require_csr_evidence = fields.Boolean(default=False)
    esg_auto_award_badges = fields.Boolean(default=True)
    esg_compliance_notifications = fields.Boolean(default=True)
    esg_csr_notifications = fields.Boolean(default=True)
    esg_challenge_notifications = fields.Boolean(default=True)


class ResUsers(models.Model):
    _inherit = "res.users"

    esg_email_notifications = fields.Boolean(default=True)
    esg_in_app_notifications = fields.Boolean(default=True)
