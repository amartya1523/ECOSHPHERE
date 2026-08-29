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
    effective_from = fields.Date(required=True, default=fields.Date.context_today)
    effective_to = fields.Date()
    active = fields.Boolean(default=True)
    _sql_constraints = [("esg_factor_nonnegative", "CHECK(co2e_factor >= 0)", "Emission factor cannot be negative.")]

    @api.constrains("effective_from", "effective_to")
    def _check_effective_dates(self):
        for factor in self:
            if factor.effective_to and factor.effective_to < factor.effective_from:
                raise ValidationError(_("The emission factor end date must be after the start date."))


class ESGProductProfile(models.Model):
    _name = "esg.product.profile"
    _description = "Product ESG Profile"

    product_id = fields.Many2one("product.template", required=True, ondelete="cascade")
    emission_factor_id = fields.Many2one("esg.emission.factor", required=True)
    recyclable_content = fields.Float(string="Recyclable Content (%)")
    notes = fields.Text()
    active = fields.Boolean(default=True)
    _sql_constraints = [("esg_product_profile_unique", "unique(product_id)", "Only one ESG profile is allowed per product.")]

    @api.constrains("recyclable_content")
    def _check_recyclable_content(self):
        for profile in self:
            if not 0 <= profile.recyclable_content <= 100:
                raise ValidationError(_("Recyclable content must be between 0 and 100%."))


class ProductTemplate(models.Model):
    _inherit = "product.template"

    esg_profile_ids = fields.One2many("esg.product.profile", "product_id", string="ESG Profiles")


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
    purchase_line_id = fields.Many2one("purchase.order.line", readonly=True, copy=False, ondelete="set null")
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
    target_metric = fields.Selection([("co2e_kg", "CO2e (kg)"), ("energy_kwh", "Energy (kWh)"), ("water_l", "Water (L)"), ("waste_kg", "Waste (kg)")], required=True, default="co2e_kg", tracking=True)
    target_value = fields.Float(required=True, tracking=True)
    current_value = fields.Float(default=0.0, tracking=True)
    progress = fields.Float(compute="_compute_progress", store=True)
    deadline = fields.Date(required=True)
    state = fields.Selection([("active", "Active"), ("on_track", "On Track"), ("completed", "Completed")], default="active", required=True, tracking=True)
    _sql_constraints = [("esg_goal_target_positive", "CHECK(target_value > 0)", "Target value must be greater than zero."), ("esg_goal_current_nonnegative", "CHECK(current_value >= 0)", "Current value cannot be negative.")]

    @api.depends("target_value", "current_value")
    def _compute_progress(self):
        for goal in self:
            goal.progress = min(100.0, (goal.current_value / goal.target_value * 100.0) if goal.target_value else 0.0)

    @api.constrains("deadline")
    def _check_deadline(self):
        for goal in self:
            if goal.deadline < fields.Date.today() and goal.state != "completed":
                raise ValidationError(_("An active goal must have a present or future deadline."))


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    esg_department_id = fields.Many2one("esg.department", string="ESG Department", tracking=True)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    esg_carbon_transaction_id = fields.Many2one("esg.carbon.transaction", readonly=True, copy=False, ondelete="set null")

    @api.model_create_multi
    def create(self, values_list):
        lines = super().create(values_list)
        lines._sync_esg_carbon_transaction()
        return lines

    def write(self, values):
        result = super().write(values)
        if {"product_id", "product_qty", "order_id"}.intersection(values):
            self._sync_esg_carbon_transaction()
        return result

    def _sync_esg_carbon_transaction(self):
        if self.env["ir.config_parameter"].sudo().get_param("eco_sphere_esg.auto_emission_calculation", "False") != "True":
            return

        Carbon = self.env["esg.carbon.transaction"].sudo()
        Profile = self.env["esg.product.profile"].sudo()
        for line in self:
            if getattr(line, "display_type", False) or line.product_qty <= 0:
                continue
            order = line.order_id
            product_template = line.product_id.product_tmpl_id
            department = order.esg_department_id
            if not order or not product_template or not department:
                continue

            profile = Profile.search([("product_id", "=", product_template.id), ("active", "=", True)], limit=1)
            if not profile:
                continue

            transaction_date = fields.Date.to_date(order.date_order) if order.date_order else fields.Date.context_today(line)
            values = {
                "transaction_date": transaction_date,
                "department_id": department.id,
                "emission_factor_id": profile.emission_factor_id.id,
                "quantity": line.product_qty,
                "source_reference": order.name or _("Purchase Order %s") % order.id,
                "is_auto_calculated": True,
                "purchase_line_id": line.id,
            }
            if line.esg_carbon_transaction_id:
                line.esg_carbon_transaction_id.sudo().write(values)
            else:
                line.esg_carbon_transaction_id = Carbon.create(values).id
