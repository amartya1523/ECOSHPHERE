import base64
import csv
import io

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
    export_file = fields.Binary(readonly=True)
    export_filename = fields.Char(readonly=True)

    def _target(self):
        return {"environmental": "esg.carbon.transaction", "social": "esg.csr.participation", "governance": "esg.compliance.issue", "gamification": "esg.challenge.participation"}.get(self.module, "esg.department.score")

    def _domain(self):
        domain = []
        if self.department_id:
            field = "department_id" if self._target() not in ("esg.csr.participation", "esg.challenge.participation") else "activity_id.department_id"
            domain.append((field, "=", self.department_id.id))
        if self.employee_id and self._target() in ("esg.csr.participation", "esg.challenge.participation"):
            domain.append(("employee_id", "=", self.employee_id.id))
        if self.challenge_id and self._target() == "esg.challenge.participation": domain.append(("challenge_id", "=", self.challenge_id.id))
        if self.category_id and self._target() == "esg.challenge.participation": domain.append(("challenge_id.category_id", "=", self.category_id.id))
        return domain

    def action_run_report(self):
        return {"type": "ir.actions.act_window", "name": "Custom ESG Report", "res_model": self._target(), "view_mode": "tree,pivot,graph", "domain": self._domain(), "target": "current"}

    def action_export_csv(self):
        records = self.env[self._target()].search(self._domain())
        output = io.StringIO(); writer = csv.writer(output)
        names = [field for field in ("display_name", "create_date") if field in records._fields]
        writer.writerow(names)
        for record in records: writer.writerow([getattr(record, name, "") for name in names])
        self.write({"export_file": base64.b64encode(output.getvalue().encode()), "export_filename": "ecosphere-report.csv"})
        return {"type": "ir.actions.act_url", "url": "/web/content?model=esg.report.builder&id=%s&field=export_file&filename_field=export_filename&download=true" % self.id, "target": "self"}

    def action_export_excel(self):
        # Excel opens CSV natively; a UTF-8 BOM preserves non-ASCII names.
        return self.action_export_csv()
