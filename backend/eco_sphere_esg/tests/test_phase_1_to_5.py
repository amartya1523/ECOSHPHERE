from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEcoSpherePhasesOneToFive(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env["esg.department"]
        cls.Category = cls.env["esg.category"]
        cls.Factor = cls.env["esg.emission.factor"]
        cls.Carbon = cls.env["esg.carbon.transaction"]
        cls.Goal = cls.env["esg.environmental.goal"]
        cls.Profile = cls.env["esg.product.profile"]
        cls.Config = cls.env["res.config.settings"]
        cls.Employee = cls.env["hr.employee"]
        cls.Product = cls.env["product.product"]
        cls.Partner = cls.env["res.partner"]
        cls.PurchaseOrder = cls.env["purchase.order"]
        cls.PurchaseLine = cls.env["purchase.order.line"]
        cls.unit = cls.env.ref("uom.product_uom_unit")

    def _department(self, name="Sustainability", code="SUS"):
        return self.Department.create({"name": name, "code": code})

    def _factor(self, name="Purchased Goods", factor=2.5, source_type="purchase"):
        return self.Factor.create({
            "name": name,
            "source_type": source_type,
            "unit": "unit",
            "co2e_factor": factor,
            "effective_from": fields.Date.today(),
        })

    def _product_with_profile(self, factor):
        product = self.Product.create({
            "name": "Low Carbon Component",
            "uom_id": self.unit.id,
            "uom_po_id": self.unit.id,
        })
        self.Profile.create({
            "product_id": product.product_tmpl_id.id,
            "emission_factor_id": factor.id,
            "recyclable_content": 35.0,
        })
        return product

    def test_phase_1_module_shell_security_and_menus_exist(self):
        self.assertEqual(self.env.ref("eco_sphere_esg.group_esg_user").name, "ESG User")
        self.assertEqual(self.env.ref("eco_sphere_esg.group_esg_admin").name, "ESG Admin")
        self.assertTrue(self.env.ref("eco_sphere_esg.menu_esg_root").exists())
        for xmlid in [
            "menu_esg_environmental",
            "menu_esg_social",
            "menu_esg_governance",
            "menu_esg_game",
            "menu_esg_settings",
            "menu_esg_reports",
        ]:
            self.assertTrue(self.env.ref("eco_sphere_esg.%s" % xmlid).exists())

    def test_phase_2_department_hierarchy_category_and_employee_count(self):
        parent = self._department("Operations", "OPS")
        child = self._department("Facilities", "FAC")
        child.parent_id = parent
        self.Employee.create({"name": "Asha Facilities", "esg_department_id": child.id})

        self.assertEqual(child.employee_count, 1)
        self.assertEqual(parent.employee_count, 1)

        category = self.Category.create({"name": "Community Volunteering", "category_type": "csr"})
        self.assertEqual(category.category_type, "csr")

    def test_phase_3_settings_save_and_weight_constraint(self):
        settings = self.Config.create({
            "auto_emission_calculation": True,
            "require_csr_evidence": True,
            "auto_award_badges": False,
            "environmental_weight": 40.0,
            "social_weight": 30.0,
            "governance_weight": 30.0,
        })
        settings.execute()

        params = self.env["ir.config_parameter"].sudo()
        self.assertEqual(params.get_param("eco_sphere_esg.auto_emission_calculation"), "True")
        self.assertEqual(float(params.get_param("eco_sphere_esg.environmental_weight")), 40.0)

        with self.assertRaises(ValidationError):
            self.Config.create({
                "environmental_weight": 50.0,
                "social_weight": 30.0,
                "governance_weight": 30.0,
            })

    def test_phase_4_manual_carbon_transaction_and_factor_dates(self):
        department = self._department("Finance", "FIN")
        factor = self._factor("Grid Power", 0.708, "manual")

        transaction = self.Carbon.create({
            "department_id": department.id,
            "emission_factor_id": factor.id,
            "quantity": 100.0,
            "transaction_date": fields.Date.today(),
        })
        self.assertAlmostEqual(transaction.co2e_kg, 70.8)

        with self.assertRaises(ValidationError):
            self.Factor.create({
                "name": "Invalid Effective Window",
                "source_type": "manual",
                "unit": "unit",
                "co2e_factor": 1.0,
                "effective_from": "2026-02-01",
                "effective_to": "2026-01-01",
            })

        self.assertTrue(self.env.ref("eco_sphere_esg.view_esg_carbon_search").exists())

    def test_phase_5_goal_tracking_and_purchase_auto_generation_toggle(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("eco_sphere_esg.auto_emission_calculation", "False")

        department = self._department("Procurement", "PROC")
        factor = self._factor("Purchased Component", 3.2, "purchase")
        product = self._product_with_profile(factor)
        partner = self.Partner.create({"name": "Green Supplier"})
        order = self.PurchaseOrder.create({"partner_id": partner.id, "esg_department_id": department.id})

        off_line = self.PurchaseLine.create({
            "order_id": order.id,
            "product_id": product.id,
            "name": product.display_name,
            "product_qty": 2.0,
            "product_uom": self.unit.id,
            "price_unit": 10.0,
            "date_planned": fields.Datetime.now(),
        })
        self.assertFalse(off_line.esg_carbon_transaction_id)

        params.set_param("eco_sphere_esg.auto_emission_calculation", "True")
        on_line = self.PurchaseLine.create({
            "order_id": order.id,
            "product_id": product.id,
            "name": product.display_name,
            "product_qty": 4.0,
            "product_uom": self.unit.id,
            "price_unit": 10.0,
            "date_planned": fields.Datetime.now(),
        })

        transaction = on_line.esg_carbon_transaction_id
        self.assertTrue(transaction)
        self.assertEqual(transaction.department_id, department)
        self.assertTrue(transaction.is_auto_calculated)
        self.assertAlmostEqual(transaction.co2e_kg, 12.8)

        on_line.product_qty = 5.0
        self.assertEqual(on_line.esg_carbon_transaction_id, transaction)
        self.assertAlmostEqual(transaction.co2e_kg, 16.0)

        goal = self.Goal.create({
            "name": "Reduce Purchased Emissions",
            "department_id": department.id,
            "target_metric": "co2e_kg",
            "target_value": 100.0,
            "current_value": 25.0,
            "deadline": fields.Date.add(fields.Date.today(), days=30),
        })
        self.assertAlmostEqual(goal.progress, 25.0)
