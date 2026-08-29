import json
from odoo import api, fields, models


class ESGOrgDashboard(models.AbstractModel):
    """Helper model providing KPI data for the Organisation Dashboard view."""

    _name = "esg.org.dashboard"
    _description = "EcoSphere Organisation Dashboard"

    @api.model
    def get_kpi_data(self):
        """Return pillar scores, overall score, and activity counts as a dict."""
        Score = self.env["esg.department.score"]
        today = fields.Date.today()

        # Latest per-department scores (most recent score_date per dept)
        all_scores = Score.search([], order="score_date desc")
        seen = set()
        latest = []
        for s in all_scores:
            if s.department_id.id not in seen:
                seen.add(s.department_id.id)
                latest.append(s)

        params = self.env["ir.config_parameter"].sudo()
        env_w = float(params.get_param("eco_sphere_esg.environmental_weight", "40")) / 100
        soc_w = float(params.get_param("eco_sphere_esg.social_weight", "30")) / 100
        gov_w = float(params.get_param("eco_sphere_esg.governance_weight", "30")) / 100

        def avg(values):
            return round(sum(values) / len(values), 1) if values else 0.0

        env_score = avg([s.environmental_score for s in latest])
        soc_score = avg([s.social_score for s in latest])
        gov_score = avg([s.governance_score for s in latest])
        overall = round(env_score * env_w + soc_score * soc_w + gov_score * gov_w, 1)

        # Activity counts
        carbon_count = self.env["esg.carbon.transaction"].search_count([])
        csr_count = self.env["esg.csr.participation"].search_count([("state", "=", "approved")])
        open_issues = self.env["esg.compliance.issue"].search_count([("state", "=", "open")])
        challenges_active = self.env["esg.challenge"].search_count([("state", "=", "active")])

        # Recent activity feed (last 15 entries across key models)
        feed = []
        for rec in self.env["esg.carbon.transaction"].search([], order="create_date desc", limit=5):
            feed.append({
                "icon": "fa-leaf",
                "color": "text-success",
                "text": "Carbon transaction logged: %s" % (rec.name or rec.display_name),
                "date": str(rec.create_date.date()) if rec.create_date else "",
            })
        for rec in self.env["esg.csr.participation"].search(
            [("state", "=", "approved")], order="create_date desc", limit=5
        ):
            feed.append({
                "icon": "fa-users",
                "color": "text-primary",
                "text": "CSR participation approved: %s" % rec.employee_id.name,
                "date": str(rec.create_date.date()) if rec.create_date else "",
            })
        for rec in self.env["esg.compliance.issue"].search([], order="create_date desc", limit=5):
            feed.append({
                "icon": "fa-exclamation-triangle",
                "color": "text-warning",
                "text": "Compliance issue raised: %s" % rec.name,
                "date": str(rec.create_date.date()) if rec.create_date else "",
            })
        for rec in self.env["esg.policy.acknowledgement"].search(
            [("state", "=", "acknowledged")], order="create_date desc", limit=5
        ):
            feed.append({
                "icon": "fa-file-text",
                "color": "text-info",
                "text": "Policy acknowledged: %s" % rec.policy_id.name,
                "date": str(rec.create_date.date()) if rec.create_date else "",
            })
        # Sort feed by date descending and cap at 15
        feed.sort(key=lambda x: x["date"], reverse=True)
        feed = feed[:15]

        return {
            "environmental_score": env_score,
            "social_score": soc_score,
            "governance_score": gov_score,
            "overall_score": overall,
            "carbon_transactions": carbon_count,
            "approved_participations": csr_count,
            "open_compliance_issues": open_issues,
            "active_challenges": challenges_active,
            "recent_activity": feed,
            "department_count": len(latest),
        }
