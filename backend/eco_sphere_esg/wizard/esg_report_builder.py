from odoo import fields, models


class ESGReportBuilder(models.TransientModel):
    _name = "esg.report.builder"
    _description = "ESG Custom Report Builder"

    date_from = fields.Date()
    date_to = fields.Date()
    department_id = fields.Many2one("esg.department")
    module = fields.Selection([("environmental", "Environmental"), ("social", "Social"), ("governance", "Governance"), ("gamification", "Gamification")])
    employee_id = fields.Many2one("hr.employee")
    challenge_id = fields.Many2one("esg.challenge")
    category_id = fields.Many2one("esg.category")

    def action_run_report(self):
        return {"type": "ir.actions.act_window", "name": "ESG Department Scores", "res_model": "esg.department.score", "view_mode": "list,pivot,graph", "target": "current"}
