from odoo import fields, models, tools


class ESGEmployeeLeaderboard(models.Model):
    """Read-only SQL view ranking employees by XP earned from approved challenge participation."""

    _name = "esg.employee.leaderboard"
    _description = "Employee ESG Leaderboard"
    _auto = False
    _order = "total_xp desc, badge_count desc"

    employee_id = fields.Many2one("hr.employee", readonly=True)
    department_id = fields.Many2one("esg.department", readonly=True)
    total_xp = fields.Integer(string="Total XP", readonly=True)
    approved_challenges = fields.Integer(string="Approved Challenges", readonly=True)
    badge_count = fields.Integer(string="Badges", readonly=True)
    rank = fields.Integer(string="Rank", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW esg_employee_leaderboard AS (
                WITH participation_stats AS (
                    SELECT
                        employee_id,
                        COALESCE(SUM(xp_awarded), 0)::integer AS total_xp,
                        COUNT(*)::integer                       AS approved_challenges
                    FROM esg_challenge_participation
                    WHERE state = 'approved'
                    GROUP BY employee_id
                ),
                badge_stats AS (
                    SELECT
                        employee_id,
                        COUNT(*)::integer AS badge_count
                    FROM esg_badge_award
                    GROUP BY employee_id
                )
                SELECT
                    emp.id                                                          AS id,
                    emp.id                                                          AS employee_id,
                    emp.esg_department_id                                           AS department_id,
                    COALESCE(ps.total_xp, 0)                                        AS total_xp,
                    COALESCE(ps.approved_challenges, 0)                             AS approved_challenges,
                    COALESCE(bs.badge_count, 0)                                     AS badge_count,
                    RANK() OVER (ORDER BY COALESCE(ps.total_xp, 0) DESC)::integer  AS rank
                FROM hr_employee emp
                LEFT JOIN participation_stats ps ON ps.employee_id = emp.id
                LEFT JOIN badge_stats         bs ON bs.employee_id = emp.id
            )
        """)
