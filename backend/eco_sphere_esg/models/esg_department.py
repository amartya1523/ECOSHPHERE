from odoo import api, fields, models


class ESGDepartment(models.Model):
    _name = "esg.department"
    _description = "ESG Department"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    manager_id = fields.Many2one("hr.employee", string="ESG Head")
    parent_id = fields.Many2one("esg.department", string="Parent Department", ondelete="restrict")
    child_ids = fields.One2many("esg.department", "parent_id", string="Sub-departments")
    employee_ids = fields.One2many("hr.employee", "esg_department_id")
    employee_count = fields.Integer(compute="_compute_employee_count", store=True)
    active = fields.Boolean(default=True)
    _sql_constraints = [
        ("esg_department_code_unique", "unique(code)", "Department code must be unique."),
        ("esg_department_name_parent_unique", "unique(name, parent_id)", "A department with this name already exists at this level."),
    ]

    @api.depends("employee_ids")
    def _compute_employee_count(self):
        for department in self:
            department.employee_count = len(department.employee_ids)


class HREmployee(models.Model):
    _inherit = "hr.employee"

    esg_department_id = fields.Many2one("esg.department", string="ESG Department", index=True)
