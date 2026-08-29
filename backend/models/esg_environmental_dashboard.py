from odoo import fields, models, tools


class ESGDepartmentCarbonReport(models.Model):
    """Read-only monthly environmental rollup used by the native dashboard."""

    _name = "esg.department.carbon.report"
    _description = "Department Carbon Tracking"
    _auto = False
    _order = "period_start desc, department_id"

    department_id = fields.Many2one("esg.department", readonly=True)
    period_start = fields.Date(string="Month", readonly=True)
    co2e_kg = fields.Float(string="CO2e (kg)", readonly=True)
    transaction_count = fields.Integer(readonly=True)
    goal_count = fields.Integer(readonly=True)
    average_goal_progress = fields.Float(string="Average Goal Progress (%)", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW esg_department_carbon_report AS (
                WITH monthly_carbon AS (
                    SELECT
                        department_id,
                        date_trunc('month', transaction_date)::date AS period_start,
                        SUM(co2e_kg) AS co2e_kg,
                        COUNT(*) AS transaction_count
                    FROM esg_carbon_transaction
                    GROUP BY department_id, date_trunc('month', transaction_date)::date
                ), department_goals AS (
                    SELECT
                        department_id,
                        COUNT(*) AS goal_count,
                        AVG(progress) AS average_goal_progress
                    FROM esg_environmental_goal
                    WHERE state != 'completed'
                    GROUP BY department_id
                )
                SELECT
                    row_number() OVER (ORDER BY monthly_carbon.period_start DESC, department.id) AS id,
                    department.id AS department_id,
                    monthly_carbon.period_start,
                    COALESCE(monthly_carbon.co2e_kg, 0.0) AS co2e_kg,
                    COALESCE(monthly_carbon.transaction_count, 0) AS transaction_count,
                    COALESCE(department_goals.goal_count, 0) AS goal_count,
                    COALESCE(department_goals.average_goal_progress, 0.0) AS average_goal_progress
                FROM esg_department department
                LEFT JOIN monthly_carbon ON monthly_carbon.department_id = department.id
                LEFT JOIN department_goals ON department_goals.department_id = department.id
            )
        """)
