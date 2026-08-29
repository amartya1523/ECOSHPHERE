from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ESGEmissionFactor(models.Model):
    _name = "esg.emission.factor"
    _description = "Emission Factor"
    _order = "name"

    name = fields.Char(required=True)
    source_type = fields.Selection([("purchase", "Purchase"), ("manufacturing", "Manufacturing"), ("expense", "Expense"), ("fleet", "Fleet"), ("manual", "Manual")], required=True, default="manual")
    unit = fields.Char(required=True, default="unit")
    co2e_factor = fields.Float(string="kg CO2e per Unit", required=True, digits=(16, 6))
    active = fields.Boolean(default=True)
    _sql_constraints = [("esg_factor_nonnegative", "CHECK(co2e_factor >= 0)", "Emission factor cannot be negative.")]


class ESGProductProfile(models.Model):
    _name = "esg.product.profile"
    _description = "Product ESG Profile"

    product_id = fields.Many2one("product.template", required=True, ondelete="cascade")
    emission_factor_id = fields.Many2one("esg.emission.factor", required=True)
    recyclable_content = fields.Float(string="Recyclable Content (%)")
    notes = fields.Text()
    _sql_constraints = [("esg_product_profile_unique", "unique(product_id)", "Only one ESG profile is allowed per product.")]


class ESGCarbonTransaction(models.Model):
    _name = "esg.carbon.transaction"
    _description = "Carbon Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "transaction_date desc, id desc"

    name = fields.Char(default=lambda self: self.env["ir.sequence"].next_by_code("esg.carbon.transaction") or _("New"), readonly=True, copy=False)
    transaction_date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    department_id = fields.Many2one("esg.department", required=True, index=True, tracking=True)
    emission_factor_id = fields.Many2one("esg.emission.factor", required=True)
    quantity = fields.Float(required=True, default=1.0)
    co2e_kg = fields.Float(string="CO2e (kg)", compute="_compute_co2e", store=True, readonly=False)
    source_type = fields.Selection(related="emission_factor_id.source_type", store=True)
    source_reference = fields.Char(help="ERP source document/reference used for auto-calculation.")
    is_auto_calculated = fields.Boolean(default=False, readonly=True)
    notes = fields.Text()
    _sql_constraints = [("esg_carbon_quantity_positive", "CHECK(quantity > 0)", "Quantity must be greater than zero."), ("esg_carbon_nonnegative", "CHECK(co2e_kg >= 0)", "CO2e cannot be negative.")]

    @api.depends("quantity", "emission_factor_id.co2e_factor")
    def _compute_co2e(self):
        for record in self:
            record.co2e_kg = record.quantity * record.emission_factor_id.co2e_factor


class ESGEnvironmentalGoal(models.Model):
    _name = "esg.environmental.goal"
    _description = "Environmental Goal"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deadline asc, id desc"

    name = fields.Char(required=True, tracking=True)
    department_id = fields.Many2one("esg.department", required=True, tracking=True)
    target_co2e = fields.Float(string="Target CO2e (kg)", required=True)
    current_co2e = fields.Float(string="Current CO2e (kg)", default=0.0, tracking=True)
    progress = fields.Float(compute="_compute_progress", store=True)
    deadline = fields.Date(required=True)
    state = fields.Selection([("active", "Active"), ("on_track", "On Track"), ("completed", "Completed")], default="active", required=True, tracking=True)
    _sql_constraints = [("esg_goal_target_positive", "CHECK(target_co2e > 0)", "Target CO2e must be greater than zero."), ("esg_goal_current_nonnegative", "CHECK(current_co2e >= 0)", "Current CO2e cannot be negative.")]

    @api.depends("target_co2e", "current_co2e")
    def _compute_progress(self):
        for goal in self:
            goal.progress = min(100.0, (goal.current_co2e / goal.target_co2e * 100.0) if goal.target_co2e else 0.0)

    @api.constrains("deadline")
    def _check_deadline(self):
        for goal in self:
            if goal.deadline < fields.Date.today() and goal.state != "completed":
                raise ValidationError(_("An active goal must have a present or future deadline."))
