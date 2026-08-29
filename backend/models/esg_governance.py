from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class ESGPolicy(models.Model):
    _name = "esg.policy"
    _description = "ESG Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, name"

    name = fields.Char(required=True)
    reference = fields.Char(required=True, copy=False)
    category_id = fields.Many2one(
        "esg.category",
        domain=[("category_type", "=", "governance")],
        string="Category",
    )
    version = fields.Char(required=True, default="v1.0")
    content = fields.Html(required=True)
    document = fields.Binary(attachment=True)
    document_filename = fields.Char()
    effective_date = fields.Date(required=True, default=fields.Date.context_today)
    review_date = fields.Date(tracking=True)
    reviewer_id = fields.Many2one("hr.employee", string="Reviewer", tracking=True)
    last_reviewed_on = fields.Datetime(readonly=True)
    acknowledgement_required = fields.Boolean(default=True, tracking=True)
    assignment_type = fields.Selection([
        ("all", "All Employees"),
        ("department", "Department"),
        ("employee", "Specific Employee"),
    ], required=True, default="all", tracking=True)
    assignment_department_id = fields.Many2one("esg.department", string="Assigned Department")
    assignment_employee_id = fields.Many2one("hr.employee", string="Assigned Employee")
    state = fields.Selection([
        ("draft", "Draft"),
        ("published", "Published"),
        ("active", "Active"),
        ("effective", "Effective"),
        ("archived", "Archived"),
    ], required=True, default="draft", tracking=True)
    active = fields.Boolean(default=True)
    acknowledgement_ids = fields.One2many("esg.policy.acknowledgement", "policy_id")
    acknowledgement_total = fields.Integer(compute="_compute_acknowledgement_progress")
    acknowledged_count = fields.Integer(compute="_compute_acknowledgement_progress")
    pending_count = fields.Integer(compute="_compute_acknowledgement_progress")
    acknowledgement_progress = fields.Float(compute="_compute_acknowledgement_progress")
    _sql_constraints = [("esg_policy_reference_unique", "unique(reference)", "Policy reference must be unique.")]

    def _is_esg_admin(self):
        return self.env.su or self.env.is_superuser() or self.env.user.has_group("eco_sphere_esg.group_esg_admin")

    def _require_esg_admin(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can manage policies."))

    @api.depends("acknowledgement_ids.state", "acknowledgement_required")
    def _compute_acknowledgement_progress(self):
        for policy in self:
            if not policy.acknowledgement_required:
                policy.acknowledgement_total = 0
                policy.acknowledged_count = 0
                policy.pending_count = 0
                policy.acknowledgement_progress = 0.0
                continue
            total = len(policy.acknowledgement_ids)
            acknowledged = len(policy.acknowledgement_ids.filtered(lambda row: row.state == "acknowledged"))
            policy.acknowledgement_total = total
            policy.acknowledged_count = acknowledged
            policy.pending_count = max(total - acknowledged, 0)
            policy.acknowledgement_progress = acknowledged * 100.0 / total if total else 0.0

    def _target_employees(self):
        Employee = self.env["hr.employee"].sudo()
        self.ensure_one()
        if self.assignment_type == "employee":
            return self.assignment_employee_id
        if self.assignment_type == "department":
            if not self.assignment_department_id:
                return Employee.browse()
            return Employee.search([("esg_department_id", "child_of", self.assignment_department_id.id), ("user_id", "!=", False)])
        user_group = self.env.ref("eco_sphere_esg.group_esg_user", raise_if_not_found=False)
        domain = [("user_id", "!=", False)]
        if user_group:
            domain.append(("user_id.groups_id", "in", user_group.id))
        return Employee.search(domain)

    def _sync_acknowledgements(self):
        Acknowledgement = self.env["esg.policy.acknowledgement"].sudo()
        for policy in self:
            if not policy.acknowledgement_required or policy.state not in {"published", "active", "effective"}:
                continue
            for employee in policy._target_employees():
                if not Acknowledgement.search_count([("policy_id", "=", policy.id), ("employee_id", "=", employee.id)]):
                    Acknowledgement.create({"policy_id": policy.id, "employee_id": employee.id})

    @api.constrains("name", "version", "effective_date", "assignment_type", "assignment_department_id", "assignment_employee_id")
    def _check_policy_required_fields(self):
        for policy in self:
            if not (policy.name or "").strip():
                raise ValidationError(_("Policy title is required."))
            if not (policy.version or "").strip():
                raise ValidationError(_("Policy version is required."))
            if not policy.effective_date:
                raise ValidationError(_("Effective date is required."))
            if policy.assignment_type == "department" and not policy.assignment_department_id:
                raise ValidationError(_("Choose the department assigned to this policy."))
            if policy.assignment_type == "employee" and not policy.assignment_employee_id:
                raise ValidationError(_("Choose the employee assigned to this policy."))

    @api.model_create_multi
    def create(self, values_list):
        self._require_esg_admin()
        for values in values_list:
            if not values.get("reference"):
                base = "".join(character for character in (values.get("name") or "POL").upper() if character.isalnum())[:8] or "POL"
                version = "".join(character for character in (values.get("version") or "V1").upper() if character.isalnum())[:6]
                reference = "%s-%s" % (base, version)
                counter = 2
                while self.sudo().search_count([("reference", "=", reference)]):
                    reference = "%s-%s-%s" % (base, version, counter)
                    counter += 1
                values["reference"] = reference
        policies = super().create(values_list)
        policies._sync_acknowledgements()
        return policies

    def write(self, values):
        admin_only = set(values) - {"message_follower_ids", "message_ids"}
        if admin_only:
            self._require_esg_admin()
        previous_states = {policy.id: policy.state for policy in self}
        result = super().write(values)
        if {"state", "assignment_type", "assignment_department_id", "assignment_employee_id", "acknowledgement_required"}.intersection(values):
            self._sync_acknowledgements()
        if "state" in values:
            for policy in self:
                if previous_states.get(policy.id) == "archived" and policy.state != "archived":
                    raise ValidationError(_("Archived policies cannot be reopened. Create a new version instead."))
        return result

    def unlink(self):
        self._require_esg_admin()
        return super().unlink()

    def action_make_effective(self):
        self.action_activate()

    def action_publish(self):
        for policy in self:
            if policy.state != "draft":
                raise ValidationError(_("Only draft policies can be published."))
        self.write({"state": "published"})
        self._post_assignment_notifications(_("New policy assigned: %s"))

    def action_activate(self):
        for policy in self:
            if policy.state not in {"draft", "published"}:
                raise ValidationError(_("Only draft or published policies can be activated."))
        self.write({"state": "active"})
        self._post_assignment_notifications(_("Policy is active: %s"))

    def action_archive(self):
        for policy in self:
            if policy.state == "archived":
                continue
            policy.write({"state": "archived", "active": False})

    def action_mark_reviewed(self):
        self._require_esg_admin()
        self.write({"last_reviewed_on": fields.Datetime.now()})

    def action_send_acknowledgement_reminders(self):
        self._require_esg_admin()
        total = 0
        for policy in self:
            pending = policy.acknowledgement_ids.filtered(lambda row: row.state == "pending")
            for acknowledgement in pending:
                acknowledgement.message_post(body=_("Reminder: please acknowledge policy %s.") % policy.display_name)
            total += len(pending)
        return total

    def _post_assignment_notifications(self, template):
        notifications_enabled = self.env["ir.config_parameter"].sudo().get_param("eco_sphere_esg.policy_notifications", "True") == "True"
        if not notifications_enabled:
            return
        for policy in self.filtered("acknowledgement_required"):
            for acknowledgement in policy.acknowledgement_ids.filtered(lambda row: row.state == "pending"):
                acknowledgement.message_post(body=template % policy.display_name)

    @api.model
    def _cron_send_acknowledgement_reminders(self):
        pending = self.env["esg.policy.acknowledgement"].search([
            ("state", "=", "pending"),
            ("policy_id.state", "in", ["published", "active", "effective"]),
        ])
        for acknowledgement in pending:
            acknowledgement.message_post(
                body=_("Reminder: please acknowledge policy %s.") % acknowledgement.policy_id.display_name
            )
        return True


class ESGPolicyAcknowledgement(models.Model):
    _name = "esg.policy.acknowledgement"
    _description = "Policy Acknowledgement"
    _inherit = ["mail.thread"]
    _order = "acknowledged_on desc"

    policy_id = fields.Many2one("esg.policy", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", required=True, default=lambda self: self.env.user.employee_id)
    acknowledged_on = fields.Datetime(readonly=True)
    state = fields.Selection([("pending", "Pending"), ("acknowledged", "Acknowledged")], default="pending", required=True)
    department_id = fields.Many2one(related="employee_id.esg_department_id", store=True, readonly=True)
    policy_version = fields.Char(related="policy_id.version", store=True, readonly=True)
    _sql_constraints = [("esg_policy_employee_unique", "unique(policy_id, employee_id)", "This employee has already been assigned this policy.")]

    def _is_esg_admin(self):
        return self.env.su or self.env.is_superuser() or self.env.user.has_group("eco_sphere_esg.group_esg_admin")

    def _is_own_acknowledgement(self):
        return bool(self.env.user.employee_id) and all(row.employee_id == self.env.user.employee_id for row in self)

    @api.model_create_multi
    def create(self, values_list):
        if not self._is_esg_admin() and not self.env.su:
            raise AccessError(_("Only an EcoSphere administrator can assign policy acknowledgements."))
        return super().create(values_list)

    def write(self, values):
        if self.env.su:
            return super().write(values)
        if self._is_esg_admin():
            return super().write(values)
        if set(values) <= {"state", "acknowledged_on"} and values.get("state") == "acknowledged" and self._is_own_acknowledgement():
            return super().write(values)
        raise AccessError(_("You can only acknowledge your own assigned policies."))

    def unlink(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can remove acknowledgement records."))
        return super().unlink()

    def action_acknowledge(self):
        for acknowledgement in self:
            if acknowledgement.employee_id != self.env.user.employee_id and not acknowledgement._is_esg_admin():
                raise AccessError(_("You can only acknowledge your own assigned policies."))
            if acknowledgement.policy_id.state not in {"active", "effective"}:
                raise ValidationError(_("Only active policies can be acknowledged."))
            if acknowledgement.state == "acknowledged":
                continue
            acknowledgement.write({"state": "acknowledged", "acknowledged_on": fields.Datetime.now()})
            acknowledgement.message_post(body=_("Policy acknowledged by %s.") % acknowledgement.employee_id.name)


class ESGAudit(models.Model):
    _name = "esg.audit"
    _description = "ESG Audit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "audit_date desc"

    name = fields.Char(required=True)
    department_id = fields.Many2one("esg.department", required=True)
    auditor_id = fields.Many2one("hr.employee", required=True)
    audit_date = fields.Date(required=True, default=fields.Date.context_today)
    due_date = fields.Date(tracking=True)
    findings = fields.Text()
    evidence = fields.Binary(attachment=True)
    evidence_filename = fields.Char()
    state = fields.Selection([("under_review", "Under Review"), ("completed", "Completed")], default="under_review", required=True)
    issue_ids = fields.One2many("esg.compliance.issue", "audit_id")

    def _is_esg_admin(self):
        return self.env.su or self.env.is_superuser() or self.env.user.has_group("eco_sphere_esg.group_esg_admin")

    def _require_esg_admin(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can manage audits."))

    @api.model_create_multi
    def create(self, values_list):
        self._require_esg_admin()
        return super().create(values_list)

    def write(self, values):
        if set(values) - {"message_follower_ids", "message_ids"}:
            self._require_esg_admin()
        return super().write(values)

    def unlink(self):
        self._require_esg_admin()
        return super().unlink()

    def action_complete(self):
        self._require_esg_admin()
        self.write({"state": "completed"})

    def action_reopen(self):
        self._require_esg_admin()
        self.write({"state": "under_review"})


class ESGComplianceIssue(models.Model):
    _name = "esg.compliance.issue"
    _description = "Compliance Issue"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "is_overdue desc, due_date asc"

    name = fields.Char(required=True)
    audit_id = fields.Many2one("esg.audit", ondelete="set null")
    department_id = fields.Many2one("esg.department", required=True)
    severity = fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], required=True, default="medium", tracking=True)
    description = fields.Html(required=True)
    evidence = fields.Binary(attachment=True)
    evidence_filename = fields.Char()
    owner_id = fields.Many2one("hr.employee", required=True, tracking=True)
    due_date = fields.Date(required=True, tracking=True)
    state = fields.Selection([
        ("open", "Open"),
        ("under_review", "Under Review"),
        ("action_required", "Action Required"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    ], required=True, default="open", tracking=True)
    is_overdue = fields.Boolean(default=False, readonly=True, index=True)
    resolved_on = fields.Datetime(readonly=True)
    resolution_note = fields.Text()

    def _is_esg_admin(self):
        return self.env.su or self.env.is_superuser() or self.env.user.has_group("eco_sphere_esg.group_esg_admin")

    def _current_employee(self):
        employee = self.env.user.employee_id
        if not employee and not self._is_esg_admin():
            raise AccessError(_("Only employee accounts can raise compliance issues."))
        return employee

    def _fallback_department(self):
        department = self.env["esg.department"].sudo().search([("code", "=", "UNASSIGNED")], limit=1)
        if department:
            return department
        return self.env["esg.department"].sudo().create({"name": _("Unassigned"), "code": "UNASSIGNED"})

    @api.constrains("owner_id", "due_date")
    def _check_required_ownership(self):
        for issue in self:
            if not issue.owner_id:
                raise ValidationError(_("A compliance issue must have an owner."))
            if not issue.due_date:
                raise ValidationError(_("A compliance issue must have a due date."))

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if not self._is_esg_admin():
                employee = self._current_employee()
                values["owner_id"] = employee.id
                values["state"] = "open"
                values.pop("resolved_on", None)
                if not values.get("department_id") and employee.esg_department_id:
                    values["department_id"] = employee.esg_department_id.id
                elif not values.get("department_id"):
                    values["department_id"] = self._fallback_department().id
            if not values.get("owner_id"):
                raise ValidationError(_("A compliance issue must have an owner."))
            if not values.get("due_date"):
                raise ValidationError(_("A compliance issue must have a due date."))
        issues = super().create(values_list)
        issues._refresh_overdue_flag()
        if self.env["ir.config_parameter"].sudo().get_param("eco_sphere_esg.compliance_notifications", "True") == "True":
            for issue in issues:
                issue.message_post(body=_("New compliance issue raised. Owner: %s") % issue.owner_id.name)
        return issues

    def write(self, values):
        if not self._is_esg_admin():
            protected = {"state", "resolved_on", "owner_id", "audit_id", "severity", "due_date", "resolution_note"}
            if protected.intersection(values):
                raise AccessError(_("Only an EcoSphere administrator can review or reassign compliance issues."))
            if any(issue.create_uid != self.env.user for issue in self):
                raise AccessError(_("You can only update compliance issues you raised."))
        result = super().write(values)
        if {"state", "due_date"}.intersection(values):
            self._refresh_overdue_flag()
        return result

    def unlink(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can remove compliance issues."))
        return super().unlink()

    def _refresh_overdue_flag(self):
        today = fields.Date.today()
        for issue in self:
            overdue = issue.state in {"open", "under_review", "action_required"} and bool(issue.due_date and issue.due_date < today)
            if issue.is_overdue != overdue:
                issue.with_context(skip_esg_overdue_refresh=True).write({"is_overdue": overdue})

    @api.model
    def _cron_update_overdue(self):
        issues = self.search([("state", "=", "open")])
        issues._refresh_overdue_flag()
        return True

    def action_resolve(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can resolve compliance issues."))
        self.write({"state": "resolved", "resolved_on": fields.Datetime.now()})

    def action_review(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can review compliance issues."))
        self.write({"state": "under_review", "resolved_on": False})

    def action_require_action(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can request action on compliance issues."))
        self.write({"state": "action_required", "resolved_on": False})

    def action_reject(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can reject compliance issues."))
        self.write({"state": "rejected", "resolved_on": fields.Datetime.now()})

    def action_reopen(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can reopen compliance issues."))
        self.write({"state": "open", "resolved_on": False})

    def action_send_owner_reminder(self):
        if not self._is_esg_admin():
            raise AccessError(_("Only an EcoSphere administrator can send compliance reminders."))
        total = 0
        for issue in self.filtered(lambda row: row.state in {"open", "under_review", "action_required"}):
            issue.message_post(body=_("Reminder sent to %s for compliance issue %s.") % (issue.owner_id.name, issue.display_name))
            total += 1
        return total
