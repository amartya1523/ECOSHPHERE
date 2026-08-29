from odoo import fields, models


class ESGCategory(models.Model):
    _name = "esg.category"
    _description = "ESG Category"
    _order = "category_type, name"

    name = fields.Char(required=True, translate=True)
    category_type = fields.Selection([
        ("csr", "CSR Activity"), ("challenge", "Challenge"),
        ("environmental", "Environmental"), ("governance", "Governance"),
    ], required=True, default="csr")
    active = fields.Boolean(default=True)
    _sql_constraints = [("esg_category_unique", "unique(name, category_type)", "Category already exists for this type.")]
