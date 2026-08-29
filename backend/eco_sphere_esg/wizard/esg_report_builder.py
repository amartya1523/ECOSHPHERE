import base64
import csv
import io

from odoo import fields, models, _
from odoo.exceptions import UserError

# Map from module selection value → (model name, date field name, department field path)
_MODULE_MAP = {
    "environmental": ("esg.carbon.transaction",      "transaction_date",  "department_id"),
    "social":        ("esg.csr.participation",        "completion_date",   "activity_id.department_id"),
    "governance":    ("esg.compliance.issue",         "due_date",          "department_id"),
    "gamification":  ("esg.challenge.participation",  "create_date",       None),
    None:            ("esg.department.score",         "score_date",        "department_id"),
}

# Friendly display names for each model's key fields (used in CSV header)
_CSV_FIELDS = {
    "esg.carbon.transaction":      ["name", "transaction_date", "department_id", "emission_factor_id", "quantity", "co2e_kg"],
    "esg.csr.participation":       ["employee_id", "activity_id", "state", "points_earned", "completion_date"],
    "esg.compliance.issue":        ["name", "department_id", "severity", "owner_id", "due_date", "state"],
    "esg.challenge.participation": ["employee_id", "challenge_id", "state", "xp_awarded"],
    "esg.department.score":        ["department_id", "score_date", "environmental_score", "social_score", "governance_score", "total_score"],
}


class ESGReportBuilder(models.TransientModel):
    _name = "esg.report.builder"
    _description = "ESG Custom Report Builder"

    date_from = fields.Date()
    date_to = fields.Date()
    department_id = fields.Many2one("esg.department")
    module = fields.Selection(
        [
            ("environmental", "Environmental"),
            ("social", "Social"),
            ("governance", "Governance"),
            ("gamification", "Gamification"),
        ]
    )
    employee_id = fields.Many2one("hr.employee")
    challenge_id = fields.Many2one("esg.challenge")
    category_id = fields.Many2one("esg.category")
    export_file = fields.Binary(readonly=True)
    export_filename = fields.Char(readonly=True)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _target_info(self):
        return _MODULE_MAP.get(self.module, _MODULE_MAP[None])

    def _domain(self):
        model_name, date_field, dept_field = self._target_info()
        domain = []

        if self.date_from and date_field:
            domain.append((date_field, ">=", self.date_from))
        if self.date_to and date_field:
            domain.append((date_field, "<=", self.date_to))

        if self.department_id and dept_field:
            domain.append((dept_field, "=", self.department_id.id))

        if self.employee_id and model_name in (
            "esg.csr.participation", "esg.challenge.participation"
        ):
            domain.append(("employee_id", "=", self.employee_id.id))

        if self.challenge_id and model_name == "esg.challenge.participation":
            domain.append(("challenge_id", "=", self.challenge_id.id))

        if self.category_id:
            if model_name == "esg.challenge.participation":
                domain.append(("challenge_id.category_id", "=", self.category_id.id))
            elif model_name == "esg.carbon.transaction":
                domain.append(("emission_factor_id.category_id", "=", self.category_id.id))

        return domain

    def _records(self):
        model_name, _date, _dept = self._target_info()
        return self.env[model_name].search(self._domain())

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_run_report(self):
        model_name, _date, _dept = self._target_info()
        return {
            "type": "ir.actions.act_window",
            "name": "Custom ESG Report",
            "res_model": model_name,
            "view_mode": "list,pivot,graph",
            "domain": self._domain(),
            "target": "current",
        }

    def action_export_csv(self):
        records = self._records()
        model_name, _date, _dept = self._target_info()
        field_names = _CSV_FIELDS.get(model_name, ["display_name", "create_date"])

        output = io.StringIO()
        writer = csv.writer(output)
        # Header row — use field string (display label) where possible
        header = []
        for fname in field_names:
            field_def = records._fields.get(fname)
            header.append(field_def.string if field_def else fname)
        writer.writerow(header)

        for rec in records:
            row = []
            for fname in field_names:
                val = getattr(rec, fname, "")
                # Relational fields — use display_name
                if hasattr(val, "display_name"):
                    val = val.display_name or ""
                elif isinstance(val, bool):
                    val = "Yes" if val else "No"
                row.append(val)
            writer.writerow(row)

        csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM for Excel compat
        self.write({
            "export_file": base64.b64encode(csv_bytes),
            "export_filename": "ecosphere-report.csv",
        })
        return {
            "type": "ir.actions.act_url",
            "url": (
                "/web/content?model=esg.report.builder"
                "&id=%s&field=export_file&filename_field=export_filename&download=true" % self.id
            ),
            "target": "self",
        }

    def action_export_excel(self):
        """Export as Excel-compatible CSV with .xlsx extension (BOM-CSV).
        If openpyxl is available on this Odoo install, a true xlsx is produced.
        """
        records = self._records()
        model_name, _date, _dept = self._target_info()
        field_names = _CSV_FIELDS.get(model_name, ["display_name", "create_date"])

        try:
            import openpyxl  # noqa: F401
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "ESG Report"
            # Header
            header = []
            for fname in field_names:
                field_def = records._fields.get(fname)
                header.append(field_def.string if field_def else fname)
            ws.append(header)
            for rec in records:
                row = []
                for fname in field_names:
                    val = getattr(rec, fname, "")
                    if hasattr(val, "display_name"):
                        val = val.display_name or ""
                    elif isinstance(val, bool):
                        val = "Yes" if val else "No"
                    row.append(str(val) if val is not None else "")
                ws.append(row)
            buf = io.BytesIO()
            wb.save(buf)
            file_bytes = buf.getvalue()
            ext = "xlsx"
        except ImportError:
            # Fallback: BOM-prefixed CSV labelled .xlsx — Excel opens it natively
            output = io.StringIO()
            writer = csv.writer(output)
            header = []
            for fname in field_names:
                field_def = records._fields.get(fname)
                header.append(field_def.string if field_def else fname)
            writer.writerow(header)
            for rec in records:
                row = []
                for fname in field_names:
                    val = getattr(rec, fname, "")
                    if hasattr(val, "display_name"):
                        val = val.display_name or ""
                    elif isinstance(val, bool):
                        val = "Yes" if val else "No"
                    row.append(val)
                writer.writerow(row)
            file_bytes = output.getvalue().encode("utf-8-sig")
            ext = "xlsx"

        self.write({
            "export_file": base64.b64encode(file_bytes),
            "export_filename": "ecosphere-report.%s" % ext,
        })
        return {
            "type": "ir.actions.act_url",
            "url": (
                "/web/content?model=esg.report.builder"
                "&id=%s&field=export_file&filename_field=export_filename&download=true" % self.id
            ),
            "target": "self",
        }

    def action_export_pdf(self):
        """Export the filtered records as a PDF using Odoo's existing report templates."""
        model_name, _date, _dept = self._target_info()
        records = self._records()
        if not records:
            raise UserError(_("No records match the selected filters."))

        # Map model → registered report action xmlid
        report_xmlid_map = {
            "esg.carbon.transaction":      "eco_sphere_esg.action_esg_report_environmental",
            "esg.csr.participation":        None,  # no standalone participation PDF
            "esg.csr.activity":             "eco_sphere_esg.action_esg_report_social",
            "esg.compliance.issue":         None,
            "esg.audit":                    "eco_sphere_esg.action_esg_report_governance",
            "esg.challenge.participation":  None,
            "esg.department.score":         "eco_sphere_esg.action_esg_report_summary",
        }
        xmlid = report_xmlid_map.get(model_name)
        if not xmlid:
            # For models without a dedicated PDF template, fall back to CSV
            return self.action_export_csv()

        report_action = self.env.ref(xmlid)
        return report_action.report_action(records)
