import base64
import csv
import io

from odoo import http, _, fields
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext


class EcoSphereAPI(http.Controller):
    # The browser never receives a model name from the caller.  This allow-list is
    # deliberately small and is the security boundary for the React application.
    # Keep fields here explicit: adding an Odoo field does not accidentally expose it.
    RESOURCES = {
        'emission-factors': ('esg.emission.factor', ('name', 'source_type', 'unit', 'co2e_factor', 'effective_from', 'effective_to', 'active')),
        'product-profiles': ('esg.product.profile', ('product_id', 'emission_factor_id', 'recyclable_content', 'notes', 'active')),
        'carbon-transactions': ('esg.carbon.transaction', ('transaction_date', 'department_id', 'emission_factor_id', 'quantity', 'co2e_kg', 'source_reference', 'notes')),
        'environmental-goals': ('esg.environmental.goal', ('name', 'department_id', 'target_metric', 'target_value', 'current_value', 'deadline', 'state')),
        'csr-activities': ('esg.csr.activity', ('name', 'category_id', 'description', 'activity_date', 'department_id', 'evidence_required', 'points', 'active')),
        'employee-participation': ('esg.csr.participation', ('employee_id', 'activity_id', 'completion_date', 'state')),
        'diversity-dashboard': ('esg.diversity.metric', ('department_id', 'metric_type', 'value', 'period', 'notes')),
        'training-completions': ('esg.training.completion', ('name', 'employee_id', 'department_id', 'completion_date', 'status')),
        'policies': ('esg.policy', ('name', 'category_id', 'version', 'effective_date', 'acknowledgement_required', 'acknowledgement_progress', 'state', 'assignment_type', 'assignment_department_id', 'assignment_employee_id', 'content', 'active')),
        'policy-acknowledgements': ('esg.policy.acknowledgement', ('policy_id', 'employee_id', 'department_id', 'policy_version', 'acknowledged_on', 'state')),
        'audits': ('esg.audit', ('name', 'department_id', 'auditor_id', 'audit_date', 'findings', 'state')),
        'compliance-issues': ('esg.compliance.issue', ('name', 'audit_id', 'department_id', 'severity', 'description', 'owner_id', 'due_date', 'state')),
        'challenges': ('esg.challenge', ('name', 'category_id', 'description', 'xp_value', 'difficulty', 'evidence_required', 'deadline', 'state')),
        'challenge-participation': ('esg.challenge.participation', ('challenge_id', 'employee_id', 'progress', 'state')),
        'badges': ('esg.badge', ('name', 'description', 'minimum_xp', 'minimum_challenges')),
        'rewards': ('esg.reward', ('name', 'description', 'points_required', 'stock', 'active')),
        'redemptions': ('esg.reward.redemption', ('employee_id', 'reward_id', 'state')),
        'departments': ('esg.department', ('name', 'code', 'manager_id', 'parent_id', 'active')),
        'categories': ('esg.category', ('name', 'category_type', 'active')),
    }

    def _resource(self, slug):
        definition = self.RESOURCES.get(slug)
        if not definition:
            raise ValidationError(_("Unknown EcoSphere resource."))
        model, allowed = definition
        return request.env[model], allowed

    def _field_schema(self, records, allowed):
        fields_info = records.fields_get(list(allowed), attributes=['string', 'type', 'required', 'readonly', 'selection', 'relation'])
        return [{'name': name, **fields_info[name]} for name in allowed if name in fields_info]

    def _clean_values(self, records, allowed, values):
        if not isinstance(values, dict):
            raise ValidationError(_("Invalid form data."))
        result = {}
        for name, value in values.items():
            if name not in allowed or name not in records._fields:
                continue
            field = records._fields[name]
            if field.readonly:
                continue
            if field.type == 'many2one':
                result[name] = int(value) if value not in (None, '', False) else False
            elif field.type in ('float', 'monetary'):
                result[name] = float(value) if value not in (None, '') else 0.0
            elif field.type in ('integer',):
                result[name] = int(value) if value not in (None, '') else 0
            elif field.type == 'boolean':
                result[name] = bool(value)
            else:
                result[name] = value or False
        return result

    def _require_manager(self):
        if not request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            raise ValidationError(_("Only an EcoSphere administrator can manage employee access."))

    def _require_managed_resource(self, slug):
        """Keep workflow-owned data off the generic CRUD endpoint.

        CSR participation must always go through the Social endpoints below: they
        attach the signed-in employee, validate evidence and enforce the review
        state machine. Diversity entries are manager-maintained organisation data.
        """
        if slug == 'employee-participation':
            raise ValidationError(_("Use the Social workspace to join an activity or submit evidence."))
        if slug == 'diversity-dashboard':
            self._require_manager()

    def _social_department(self, department_id=None, department_name=None):
        """Resolve an existing department or create a named one for a new activity."""
        Department = request.env['esg.department']
        if department_id:
            department = Department.browse(int(department_id)).exists()
            if department:
                return department
            raise ValidationError(_("Selected department no longer exists."))
        name = (department_name or '').strip()
        if not name:
            raise ValidationError(_("Choose or enter the department responsible for this activity."))
        department = Department.search([('name', '=ilike', name)], limit=1)
        if department:
            return department
        base_code = ''.join(character for character in name.upper() if character.isalnum())[:8] or 'DEPT'
        code, counter = base_code, 2
        while Department.search_count([('code', '=', code)]):
            code = '%s%s' % (base_code[:max(1, 10 - len(str(counter)))], counter)
            counter += 1
        return Department.create({'name': name, 'code': code})

    @staticmethod
    def _player_config(challenge):
        config = challenge.game_config or {}
        if challenge.challenge_type in {"quiz", "scenario"}:
            return {**config, "questions": [{key: value for key, value in question.items() if key != "answer"} for question in config.get("questions", [])]}
        return config

    @http.route('/ecosphere/api/resources/<string:slug>', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_list(self, slug, limit=100, query=None):
        if slug == 'employee-participation':
            self._require_managed_resource(slug)
        records, allowed = self._resource(slug)
        records.check_access_rights('read')
        domain = [('display_name', 'ilike', query)] if query else []
        rows = records.search_read(domain, list(allowed), limit=min(max(int(limit or 100), 1), 200), order='id desc')
        managed = slug == 'diversity-dashboard' and not request.env.user.has_group('eco_sphere_esg.group_esg_manager')
        is_admin = request.env.user.has_group('eco_sphere_esg.group_esg_admin')
        return {
            'records': rows,
            'fields': self._field_schema(records, allowed),
            'can_create': False if managed else records.check_access_rights('create', raise_exception=False),
            'can_write': False if managed else records.check_access_rights('write', raise_exception=False),
            'can_delete': False if managed else records.check_access_rights('unlink', raise_exception=False),
            'is_manager': is_admin,
        }

    @http.route('/ecosphere/api/resources/<string:slug>/options/<string:field_name>', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_options(self, slug, field_name, query=None):
        records, allowed = self._resource(slug)
        if field_name not in allowed or records._fields[field_name].type != 'many2one':
            raise ValidationError(_("Invalid relation field."))
        relation = request.env[records._fields[field_name].comodel_name]
        if slug == 'policies' and field_name == 'assignment_employee_id' and request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            relation = relation.sudo()
        relation.check_access_rights('read')
        domain = [('display_name', 'ilike', query)] if query else []
        return relation.name_search(name=query or '', args=domain, limit=100)

    @http.route('/ecosphere/api/resources/<string:slug>/create', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_create(self, slug, values):
        self._require_managed_resource(slug)
        records, allowed = self._resource(slug)
        records.check_access_rights('create')
        record = records.create(self._clean_values(records, allowed, values))
        return {'id': record.id, 'message': _("Saved successfully.")}

    @http.route('/ecosphere/api/resources/<string:slug>/<int:record_id>/update', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_update(self, slug, record_id, values):
        self._require_managed_resource(slug)
        records, allowed = self._resource(slug)
        record = records.browse(record_id).exists()
        if not record:
            raise ValidationError(_("This record no longer exists."))
        record.check_access_rights('write')
        record.check_access_rule('write')
        record.write(self._clean_values(records, allowed, values))
        return {'id': record.id, 'message': _("Changes saved.")}

    @http.route('/ecosphere/api/resources/<string:slug>/<int:record_id>/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_delete(self, slug, record_id):
        self._require_managed_resource(slug)
        records, _allowed = self._resource(slug)
        record = records.browse(record_id).exists()
        if not record:
            raise ValidationError(_("This record no longer exists."))
        record.check_access_rights('unlink')
        record.check_access_rule('unlink')
        record.unlink()
        return {'message': _("Deleted successfully.")}

    @http.route('/ecosphere/api/policies/<int:policy_id>/<string:action>', type='json', auth='user', methods=['POST'], csrf=False)
    def policy_action(self, policy_id, action):
        policy = request.env['esg.policy'].browse(policy_id).exists()
        if not policy:
            raise ValidationError(_("This policy no longer exists."))
        if action == 'publish':
            policy.action_publish()
            return {'message': _("Policy published and assigned.")}
        if action == 'activate':
            policy.action_activate()
            return {'message': _("Policy activated.")}
        if action == 'archive':
            policy.action_archive()
            return {'message': _("Policy archived.")}
        if action == 'remind':
            count = policy.action_send_acknowledgement_reminders()
            return {'message': _("Sent %(count)s acknowledgement reminder(s).") % {'count': count}}
        raise ValidationError(_("Unknown policy action."))

    @http.route('/ecosphere/api/policy-acknowledgements/<int:acknowledgement_id>/acknowledge', type='json', auth='user', methods=['POST'], csrf=False)
    def policy_acknowledge(self, acknowledgement_id):
        acknowledgement = request.env['esg.policy.acknowledgement'].browse(acknowledgement_id).exists()
        if not acknowledgement:
            raise ValidationError(_("This acknowledgement is no longer available."))
        acknowledgement.action_acknowledge()
        return {'message': _("Policy acknowledged.")}

    def _policy_assignment_summary(self, policy):
        if policy.assignment_type == 'department':
            return _("Department: %s") % (policy.assignment_department_id.display_name or _("Unassigned"))
        if policy.assignment_type == 'employee':
            return _("Employee: %s") % (policy.assignment_employee_id.display_name or _("Unassigned"))
        return _("All employees")

    def _policy_acknowledgement_row(self, acknowledgement):
        today = fields.Date.context_today(acknowledgement)
        policy = acknowledgement.policy_id
        needs_reminder = (
            acknowledgement.state == 'pending'
            and policy.state in {'active', 'effective'}
            and bool(policy.effective_date)
            and policy.effective_date < today
        )
        return {
            'id': acknowledgement.id,
            'employee': acknowledgement.employee_id.display_name,
            'department': acknowledgement.department_id.display_name or '',
            'department_id': acknowledgement.department_id.id or False,
            'state': acknowledgement.state,
            'acknowledged_on': str(acknowledgement.acknowledged_on or ''),
            'needs_reminder': needs_reminder,
        }

    def _policy_row(self, policy, is_admin):
        own_ack = policy.acknowledgement_ids.filtered(lambda row: row.employee_id == request.env.user.employee_id)[:1]
        acknowledgements = policy.acknowledgement_ids.sudo() if is_admin else own_ack
        return {
            'id': policy.id,
            'name': policy.name,
            'category': policy.category_id.display_name or '',
            'category_id': policy.category_id.id or False,
            'version': policy.version,
            'effective_date': str(policy.effective_date or ''),
            'acknowledgement_required': policy.acknowledgement_required,
            'acknowledgement_progress': round(policy.acknowledgement_progress or 0.0),
            'acknowledged_count': policy.acknowledged_count,
            'pending_count': policy.pending_count,
            'acknowledgement_total': policy.acknowledgement_total,
            'state': 'active' if policy.state == 'effective' else policy.state,
            'assignment_type': policy.assignment_type,
            'assignment_department_id': policy.assignment_department_id.id or False,
            'assignment_employee_id': policy.assignment_employee_id.id or False,
            'assignment_summary': self._policy_assignment_summary(policy),
            'content': policy.content or '',
            'content_text': html2plaintext(policy.content or '').strip(),
            'active': policy.active,
            'needs_reminder': any(self._policy_acknowledgement_row(row)['needs_reminder'] for row in acknowledgements),
            'my_acknowledgement': own_ack and {
                'id': own_ack.id,
                'state': own_ack.state,
                'acknowledged_on': str(own_ack.acknowledged_on or ''),
                'needs_reminder': self._policy_acknowledgement_row(own_ack)['needs_reminder'],
            } or False,
            'acknowledgements': [self._policy_acknowledgement_row(acknowledgement) for acknowledgement in acknowledgements],
            'version_history': [{
                'id': row.id,
                'version': row.version,
                'state': 'active' if row.state == 'effective' else row.state,
                'effective_date': str(row.effective_date or ''),
            } for row in request.env['esg.policy'].search([('name', '=', policy.name)], order='effective_date desc, id desc')],
        }

    def _filtered_policy_rows(self, rows, query=None, status='all', acknowledgement='all', policy_id=None, department_id=None):
        if query:
            needle = query.strip().lower()
            rows = [row for row in rows if needle in ' '.join([row['name'], row['category'], row['version'], row['assignment_summary']]).lower()]
        if policy_id:
            rows = [row for row in rows if row['id'] == int(policy_id)]
        if status and status != 'all':
            rows = [row for row in rows if row['state'] == status]
        if department_id:
            selected = int(department_id)
            rows = [
                row for row in rows
                if row['assignment_department_id'] == selected
                or any(acknowledgement.get('department_id') == selected for acknowledgement in row['acknowledgements'])
            ]
        return rows

    @http.route('/ecosphere/api/policy-workspace', type='json', auth='user', methods=['POST'], csrf=False)
    def policy_workspace(self, query=None, status='all', acknowledgement='all', policy_id=None, department_id=None):
        is_admin = request.env.user.has_group('eco_sphere_esg.group_esg_admin')
        Policy = request.env['esg.policy']
        policies = Policy.search([], order='effective_date desc, id desc')
        rows = [self._policy_row(policy, is_admin) for policy in policies]
        policy_options = [(row['id'], '%s %s' % (row['name'], row['version'])) for row in rows]
        rows = self._filtered_policy_rows(rows, query=query, status=status, policy_id=policy_id, department_id=department_id if is_admin else None)
        if acknowledgement == 'required':
            rows = [row for row in rows if row['acknowledgement_required']]
        elif acknowledgement == 'optional':
            rows = [row for row in rows if not row['acknowledgement_required']]
        elif acknowledgement == 'pending':
            if is_admin:
                rows = [row for row in rows if row['pending_count'] > 0]
            else:
                rows = [row for row in rows if row['my_acknowledgement'] and row['my_acknowledgement']['state'] == 'pending']
        elif acknowledgement == 'overdue':
            if is_admin:
                rows = [row for row in rows if any(item['needs_reminder'] for item in row['acknowledgements'])]
            else:
                rows = [row for row in rows if row['my_acknowledgement'] and row['my_acknowledgement']['needs_reminder']]
        elif acknowledgement == 'acknowledged' and not is_admin:
            rows = [row for row in rows if row['my_acknowledgement'] and row['my_acknowledgement']['state'] == 'acknowledged']
        total = len(rows)
        active = len([row for row in rows if row['state'] == 'active'])
        pending = sum(row['pending_count'] for row in rows) if is_admin else len([row for row in rows if row['my_acknowledgement'] and row['my_acknowledgement']['state'] == 'pending'])
        required = sum(row['acknowledgement_total'] for row in rows if row['acknowledgement_required']) if is_admin else len([row for row in rows if row['acknowledgement_required']])
        acknowledged = sum(row['acknowledged_count'] for row in rows if row['acknowledgement_required']) if is_admin else len([row for row in rows if row['my_acknowledgement'] and row['my_acknowledgement']['state'] == 'acknowledged'])
        return {
            'is_manager': is_admin,
            'can_create': Policy.check_access_rights('create', raise_exception=False),
            'can_write': Policy.check_access_rights('write', raise_exception=False),
            'policies': rows,
            'metrics': {
                'total': total,
                'active': active,
                'pending': pending,
                'needs_reminder': sum(len([item for item in row['acknowledgements'] if item['needs_reminder']]) for row in rows) if is_admin else len([row for row in rows if row['my_acknowledgement'] and row['my_acknowledgement']['needs_reminder']]),
                'acknowledgement_rate': round(acknowledged * 100.0 / required) if required else 0,
            },
            'policy_options': policy_options,
            'categories': request.env['esg.category'].name_search('', args=[('category_type', '=', 'governance')], limit=100),
            'departments': request.env['esg.department'].name_search('', limit=100) if is_admin else [],
            'employees': request.env['hr.employee'].sudo().name_search('', limit=100) if is_admin else [],
        }

    def _acknowledgement_domain(self, acknowledgement_ids=None, policy_id=None, department_id=None, state=None):
        domain = []
        if acknowledgement_ids:
            domain.append(('id', 'in', [int(row_id) for row_id in acknowledgement_ids]))
        if policy_id:
            domain.append(('policy_id', '=', int(policy_id)))
        if department_id:
            domain.append(('department_id', '=', int(department_id)))
        if state and state != 'all':
            domain.append(('state', '=', state))
        return domain

    @http.route('/ecosphere/api/policy-acknowledgements/remind', type='json', auth='user', methods=['POST'], csrf=False)
    def policy_acknowledgement_remind(self, acknowledgement_ids=None, policy_id=None, department_id=None):
        self._require_manager()
        domain = self._acknowledgement_domain(acknowledgement_ids=acknowledgement_ids, policy_id=policy_id, department_id=department_id, state='pending')
        acknowledgements = request.env['esg.policy.acknowledgement'].sudo().search(domain)
        for acknowledgement in acknowledgements:
            acknowledgement.message_post(body=_("Reminder: please acknowledge policy %s.") % acknowledgement.policy_id.display_name)
        return {'message': _("Sent %(count)s acknowledgement reminder(s).") % {'count': len(acknowledgements)}, 'count': len(acknowledgements)}

    @http.route('/ecosphere/api/policy-acknowledgements/export', type='json', auth='user', methods=['POST'], csrf=False)
    def policy_acknowledgement_export(self, policy_id=None, department_id=None, state='all'):
        self._require_manager()
        domain = self._acknowledgement_domain(policy_id=policy_id, department_id=department_id, state=state)
        acknowledgements = request.env['esg.policy.acknowledgement'].sudo().search(domain, order='policy_id, employee_id')
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['Policy', 'Version', 'Employee', 'Department', 'Status', 'Acknowledged On'])
        for acknowledgement in acknowledgements:
            writer.writerow([
                acknowledgement.policy_id.display_name,
                acknowledgement.policy_version,
                acknowledgement.employee_id.display_name,
                acknowledgement.department_id.display_name or '',
                acknowledgement.state,
                str(acknowledgement.acknowledged_on or ''),
            ])
        return {
            'filename': 'policy-acknowledgements.csv',
            'csv': buffer.getvalue(),
        }

    def _audit_issue_row(self, issue):
        return {
            'id': issue.id,
            'name': issue.name,
            'audit_id': issue.audit_id.id or False,
            'audit': issue.audit_id.display_name or '',
            'department_id': issue.department_id.id or False,
            'department': issue.department_id.display_name or '',
            'severity': issue.severity,
            'description': issue.description or '',
            'description_text': html2plaintext(issue.description or '').strip(),
            'owner_id': issue.owner_id.id or False,
            'owner': issue.owner_id.display_name or '',
            'due_date': str(issue.due_date or ''),
            'state': issue.state,
            'is_overdue': issue.is_overdue,
            'resolved_on': str(issue.resolved_on or ''),
            'raised_by': issue.create_uid.display_name or '',
        }

    def _audit_row(self, audit, is_admin):
        issues = audit.issue_ids.sudo() if is_admin else audit.issue_ids
        open_issues = issues.filtered(lambda issue: issue.state == 'open')
        critical_issues = issues.filtered(lambda issue: issue.severity == 'critical')
        return {
            'id': audit.id,
            'name': audit.name,
            'department_id': audit.department_id.id or False,
            'department': audit.department_id.display_name or '',
            'auditor_id': audit.auditor_id.id or False,
            'auditor': audit.auditor_id.display_name or '',
            'audit_date': str(audit.audit_date or ''),
            'findings': audit.findings or '',
            'findings_text': html2plaintext(audit.findings or '').strip(),
            'state': audit.state,
            'issue_count': len(issues),
            'open_issue_count': len(open_issues),
            'critical_issue_count': len(critical_issues),
            'overdue_issue_count': len(issues.filtered('is_overdue')),
            'issues': [self._audit_issue_row(issue) for issue in issues],
        }

    def _filtered_audit_rows(self, rows, query=None, status='all', severity='all', department_id=None, audit_id=None):
        if query:
            needle = query.strip().lower()
            rows = [row for row in rows if needle in ' '.join([row['name'], row['department'], row['auditor'], row['findings_text']]).lower()]
        if audit_id:
            rows = [row for row in rows if row['id'] == int(audit_id)]
        if status and status != 'all':
            rows = [row for row in rows if row['state'] == status]
        if department_id:
            selected = int(department_id)
            rows = [row for row in rows if row['department_id'] == selected]
        if severity and severity != 'all':
            rows = [row for row in rows if any(issue['severity'] == severity for issue in row['issues'])]
        return rows

    @http.route('/ecosphere/api/audit-workspace', type='json', auth='user', methods=['POST'], csrf=False)
    def audit_workspace(self, query=None, status='all', issue_status='all', severity='all', department_id=None, audit_id=None):
        is_admin = request.env.user.has_group('eco_sphere_esg.group_esg_admin')
        Audit = request.env['esg.audit']
        Issue = request.env['esg.compliance.issue']
        audits = Audit.search([], order='audit_date desc, id desc')
        rows = [self._audit_row(audit, is_admin) for audit in audits]
        audit_options = [(row['id'], row['name']) for row in rows]
        rows = self._filtered_audit_rows(rows, query=query, status=status, severity=severity, department_id=department_id if is_admin else None, audit_id=audit_id)
        if issue_status and issue_status != 'all':
            rows = [row for row in rows if any(issue['state'] == issue_status for issue in row['issues'])]
        issue_domain = []
        if audit_id:
            issue_domain.append(('audit_id', '=', int(audit_id)))
        if department_id and is_admin:
            issue_domain.append(('department_id', '=', int(department_id)))
        if issue_status and issue_status != 'all':
            issue_domain.append(('state', '=', issue_status))
        if severity and severity != 'all':
            issue_domain.append(('severity', '=', severity))
        issue_records = Issue.search(issue_domain, order='is_overdue desc, due_date asc, id desc')
        issues = [self._audit_issue_row(issue) for issue in issue_records]
        if query:
            needle = query.strip().lower()
            issues = [issue for issue in issues if needle in ' '.join([issue['name'], issue['audit'], issue['department'], issue['owner'], issue['description_text']]).lower()]
        total_issues = len(issues)
        open_issues = len([issue for issue in issues if issue['state'] == 'open'])
        overdue_issues = len([issue for issue in issues if issue['is_overdue']])
        return {
            'is_manager': is_admin,
            'can_create_audit': Audit.check_access_rights('create', raise_exception=False),
            'can_raise_issue': Issue.check_access_rights('create', raise_exception=False),
            'audits': rows,
            'issues': issues,
            'metrics': {
                'total': len(rows),
                'under_review': len([row for row in rows if row['state'] == 'under_review']),
                'completed': len([row for row in rows if row['state'] == 'completed']),
                'open_issues': open_issues,
                'overdue_issues': overdue_issues,
                'resolution_rate': round((total_issues - open_issues) * 100.0 / total_issues) if total_issues else 0,
            },
            'audit_options': audit_options,
            'departments': request.env['esg.department'].name_search('', limit=100) if is_admin else [],
            'employees': request.env['hr.employee'].sudo().name_search('', limit=100) if is_admin else [],
        }

    @http.route('/ecosphere/api/audits/create', type='json', auth='user', methods=['POST'], csrf=False)
    def audit_create(self, values):
        if not request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            raise ValidationError(_("Only an EcoSphere administrator can manage audits."))
        cleaned = self._clean_values(request.env['esg.audit'], self.RESOURCES['audits'][1], values)
        audit = request.env['esg.audit'].create(cleaned)
        return {'id': audit.id, 'message': _("Audit created.")}

    @http.route('/ecosphere/api/audits/<int:audit_id>/update', type='json', auth='user', methods=['POST'], csrf=False)
    def audit_update(self, audit_id, values):
        if not request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            raise ValidationError(_("Only an EcoSphere administrator can manage audits."))
        audit = request.env['esg.audit'].browse(audit_id).exists()
        if not audit:
            raise ValidationError(_("This audit no longer exists."))
        cleaned = self._clean_values(request.env['esg.audit'], self.RESOURCES['audits'][1], values)
        audit.write(cleaned)
        return {'id': audit.id, 'message': _("Audit updated.")}

    @http.route('/ecosphere/api/audits/<int:audit_id>/<string:action>', type='json', auth='user', methods=['POST'], csrf=False)
    def audit_action(self, audit_id, action):
        if not request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            raise ValidationError(_("Only an EcoSphere administrator can change audit status."))
        audit = request.env['esg.audit'].browse(audit_id).exists()
        if not audit:
            raise ValidationError(_("This audit no longer exists."))
        if action == 'complete':
            audit.action_complete()
            return {'message': _("Audit marked completed.")}
        if action == 'reopen':
            audit.action_reopen()
            return {'message': _("Audit reopened for review.")}
        raise ValidationError(_("Unknown audit action."))

    @http.route('/ecosphere/api/compliance-issues/create', type='json', auth='user', methods=['POST'], csrf=False)
    def compliance_issue_create(self, values):
        Issue = request.env['esg.compliance.issue']
        cleaned = self._clean_values(Issue, self.RESOURCES['compliance-issues'][1], values)
        issue = Issue.create(cleaned)
        return {'id': issue.id, 'message': _("Compliance issue raised for review.")}

    @http.route('/ecosphere/api/compliance-issues/<int:issue_id>/update', type='json', auth='user', methods=['POST'], csrf=False)
    def compliance_issue_update(self, issue_id, values):
        issue = request.env['esg.compliance.issue'].browse(issue_id).exists()
        if not issue:
            raise ValidationError(_("This compliance issue no longer exists."))
        cleaned = self._clean_values(request.env['esg.compliance.issue'], self.RESOURCES['compliance-issues'][1], values)
        issue.write(cleaned)
        return {'id': issue.id, 'message': _("Compliance issue updated.")}

    @http.route('/ecosphere/api/compliance-issues/<int:issue_id>/<string:action>', type='json', auth='user', methods=['POST'], csrf=False)
    def compliance_issue_action(self, issue_id, action):
        if not request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            raise ValidationError(_("Only an EcoSphere administrator can review compliance issue status."))
        issue = request.env['esg.compliance.issue'].browse(issue_id).exists()
        if not issue:
            raise ValidationError(_("This compliance issue no longer exists."))
        if action == 'resolve':
            issue.action_resolve()
            return {'message': _("Compliance issue resolved.")}
        if action == 'reopen':
            issue.action_reopen()
            return {'message': _("Compliance issue reopened.")}
        raise ValidationError(_("Unknown compliance issue action."))

    @http.route('/ecosphere/api/audit-workspace/export', type='json', auth='user', methods=['POST'], csrf=False)
    def audit_workspace_export(self, audit_id=None, department_id=None, issue_status='all', severity='all'):
        if not request.env.user.has_group('eco_sphere_esg.group_esg_admin'):
            raise ValidationError(_("Only an EcoSphere administrator can export audit data."))
        data = self.audit_workspace(status='all', issue_status=issue_status, severity=severity, department_id=department_id, audit_id=audit_id)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['Audit', 'Department', 'Auditor', 'Audit Date', 'Audit Status', 'Issue', 'Severity', 'Owner', 'Due Date', 'Issue Status', 'Overdue'])
        for audit in data['audits']:
            if audit['issues']:
                for issue in audit['issues']:
                    writer.writerow([audit['name'], audit['department'], audit['auditor'], audit['audit_date'], audit['state'], issue['name'], issue['severity'], issue['owner'], issue['due_date'], issue['state'], 'Yes' if issue['is_overdue'] else 'No'])
            else:
                writer.writerow([audit['name'], audit['department'], audit['auditor'], audit['audit_date'], audit['state'], '', '', '', '', '', ''])
        return {'filename': 'audit-workspace.csv', 'csv': buffer.getvalue()}

    @http.route('/ecosphere/api/team', type='json', auth='user', methods=['POST'], csrf=False)
    def team_list(self):
        self._require_manager()
        user_group = request.env.ref('eco_sphere_esg.group_esg_user')
        # An enterprise is an Odoo company.  Never expose users from another
        # company, even when they have the same EcoSphere security group.
        users = request.env['res.users'].sudo().with_context(active_test=False).search([
            ('id', '!=', request.env.ref('base.user_root').id),
            ('groups_id', 'in', user_group.id),
            ('company_id', '=', request.env.company.id),
        ], order='active desc, name')
        return {'members': [{
            'id': user.id, 'name': user.name, 'email': user.login,
            'active': user.active,
            'role': 'Administrator' if user.has_group('eco_sphere_esg.group_esg_manager') else 'Employee',
        } for user in users]}

    @http.route('/ecosphere/api/team/create', type='json', auth='user', methods=['POST'], csrf=False)
    def team_create(self, name, email, password, department_id=None):
        self._require_manager()
        name, email = (name or '').strip(), (email or '').strip().lower()
        if len(name) < 2 or '@' not in email or len(password or '') < 8:
            raise ValidationError(_("Enter a name, valid work email, and password of at least 8 characters."))
        Users = request.env['res.users'].sudo()
        if Users.search_count([('login', '=', email)]):
            raise ValidationError(_("An account already exists for this email address."))
        employee_group = request.env.ref('eco_sphere_esg.group_esg_user').sudo()
        internal_group = request.env.ref('base.group_user').sudo()
        workspace = request.env.company
        user = Users.with_context(no_reset_password=True).create({
            'name': name, 'login': email, 'email': email, 'password': password,
            'company_id': workspace.id,
            'company_ids': [(6, 0, [workspace.id])],
            'groups_id': [(6, 0, [internal_group.id, employee_group.id])],
        })
        employee_values = {'name': name, 'user_id': user.id}
        if department_id:
            department = request.env['esg.department'].browse(int(department_id)).exists()
            if not department:
                raise ValidationError(_("Selected department no longer exists."))
            employee_values['esg_department_id'] = department.id
        request.env['hr.employee'].sudo().create(employee_values)
        return {'id': user.id, 'message': _("Employee account created. Share the login credentials securely.")}

    def _settings_payload(self):
        """Return only the signed-in person's settings and active workspace data."""
        user = request.env.user
        company = request.env.company
        manager = user.has_group('eco_sphere_esg.group_esg_manager')
        payload = {
            'is_manager': manager,
            'profile': {
                'name': user.name,
                'email': user.login,
                'email_notifications': user.esg_email_notifications,
                'in_app_notifications': user.esg_in_app_notifications,
            },
        }
        if not manager:
            return payload
        departments = request.env['esg.department'].sudo().search([
            ('company_id', '=', company.id),
        ], order='active desc, name')
        payload.update({
            'workspace': {'id': company.id, 'name': company.name},
            'configuration': {
                'environmental_weight': company.esg_environmental_weight,
                'social_weight': company.esg_social_weight,
                'governance_weight': company.esg_governance_weight,
                'auto_emission_calculation': company.esg_auto_emission_calculation,
                'require_csr_evidence': company.esg_require_csr_evidence,
                'auto_award_badges': company.esg_auto_award_badges,
                'compliance_notifications': company.esg_compliance_notifications,
                'csr_notifications': company.esg_csr_notifications,
                'challenge_notifications': company.esg_challenge_notifications,
            },
            'departments': [{
                'id': department.id,
                'name': department.name,
                'code': department.code,
                'active': department.active,
                'employees': department.employee_count,
            } for department in departments],
        })
        return payload

    @http.route('/ecosphere/api/settings', type='json', auth='user', methods=['POST'], csrf=False)
    def settings(self):
        return self._settings_payload()

    @http.route('/ecosphere/api/settings/profile', type='json', auth='user', methods=['POST'], csrf=False)
    def settings_profile(self, name=None, email_notifications=True, in_app_notifications=True):
        clean_name = (name or '').strip()
        if len(clean_name) < 2:
            raise ValidationError(_("Enter a name of at least two characters."))
        request.env.user.write({
            'name': clean_name,
            'esg_email_notifications': bool(email_notifications),
            'esg_in_app_notifications': bool(in_app_notifications),
        })
        return {'message': _("Personal settings saved."), **self._settings_payload()}

    @http.route('/ecosphere/api/settings/workspace', type='json', auth='user', methods=['POST'], csrf=False)
    def settings_workspace(self, name, configuration=None):
        self._require_manager()
        name = (name or '').strip()
        config = configuration if isinstance(configuration, dict) else {}
        if len(name) < 2:
            raise ValidationError(_("Enter a workspace name of at least two characters."))
        weights = [float(config.get(key, 0)) for key in ('environmental_weight', 'social_weight', 'governance_weight')]
        if any(weight < 0 or weight > 100 for weight in weights) or round(sum(weights), 2) != 100:
            raise ValidationError(_("Environmental, social, and governance weights must add up to 100%."))
        company = request.env.company.sudo()
        company.write({
            'name': name,
            'esg_environmental_weight': weights[0],
            'esg_social_weight': weights[1],
            'esg_governance_weight': weights[2],
            'esg_auto_emission_calculation': bool(config.get('auto_emission_calculation')),
            'esg_require_csr_evidence': bool(config.get('require_csr_evidence')),
            'esg_auto_award_badges': bool(config.get('auto_award_badges')),
            'esg_compliance_notifications': bool(config.get('compliance_notifications')),
            'esg_csr_notifications': bool(config.get('csr_notifications')),
            'esg_challenge_notifications': bool(config.get('challenge_notifications')),
        })
        return {'message': _("Workspace configuration saved."), **self._settings_payload()}

    @http.route('/ecosphere/api/settings/departments/save', type='json', auth='user', methods=['POST'], csrf=False)
    def settings_department_save(self, name, code, department_id=None):
        self._require_manager()
        name, code = (name or '').strip(), (code or '').strip().upper()
        if len(name) < 2 or len(code) < 2:
            raise ValidationError(_("Enter a department name and code of at least two characters."))
        Department = request.env['esg.department'].sudo()
        company = request.env.company
        department = Department.browse(int(department_id)).exists() if department_id else Department.browse()
        if department and department.company_id != company:
            raise ValidationError(_("That department belongs to another workspace."))
        duplicate_domain = [('company_id', '=', company.id), ('code', '=', code)]
        if department:
            duplicate_domain.append(('id', '!=', department.id))
        if Department.search_count(duplicate_domain):
            raise ValidationError(_("A department with this code already exists in your workspace."))
        values = {'name': name, 'code': code, 'company_id': company.id}
        if department:
            department.write(values)
        else:
            department = Department.create(values)
        return {'id': department.id, 'message': _("Department saved."), **self._settings_payload()}

    @http.route('/ecosphere/api/settings/departments/<int:department_id>/archive', type='json', auth='user', methods=['POST'], csrf=False)
    def settings_department_archive(self, department_id):
        self._require_manager()
        department = request.env['esg.department'].sudo().browse(department_id).exists()
        if not department or department.company_id != request.env.company:
            raise ValidationError(_("Department not found in this workspace."))
        department.write({'active': False})
        return {'message': _("Department archived."), **self._settings_payload()}

    @http.route('/ecosphere/api/signup', type='json', auth='public', methods=['POST'], csrf=False)
    def signup(self, name, workspace_name, email, password):
        """Provision an enterprise owner; employee accounts remain admin-only."""
        name, workspace_name, email = (name or '').strip(), (workspace_name or '').strip(), (email or '').strip().lower()
        if len(name) < 2 or len(workspace_name) < 2 or '@' not in email or len(password or '') < 8:
            raise ValidationError(_("Enter your name, workspace name, valid work email, and a password of at least 8 characters."))
        Users = request.env['res.users'].sudo()
        if Users.search_count([('login', '=', email)]):
            raise ValidationError(_("An account already exists for this email address."))
        manager_group = request.env.ref('eco_sphere_esg.group_esg_manager').sudo()
        workspace = request.env['res.company'].sudo().create({'name': workspace_name})
        user = Users.with_context(no_reset_password=True).create({
            'name': name,
            'login': email,
            'email': email,
            'password': password,
            'company_id': workspace.id,
            'company_ids': [(6, 0, [workspace.id])],
            'groups_id': [(6, 0, [manager_group.id])],
        })
        return {'id': user.id, 'workspace': workspace.name, 'message': _("Enterprise administrator account created.")}

    @http.route('/ecosphere/api/gamification', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification(self):
        """Role-aware gamification feed for the React workspace."""
        is_manager = request.env.user.has_group('eco_sphere_esg.group_esg_manager')
        employee = request.env.user.employee_id
        Challenge = request.env['esg.challenge']
        Participation = request.env['esg.challenge.participation']
        domain = [('is_template', '=', False)] + ([] if is_manager else [('state', '=', 'active')])
        challenges = Challenge.search(domain, order='deadline asc, id desc')
        own_participation = {}
        if employee:
            own_participation = {
                row.challenge_id.id: row for row in Participation.search([('employee_id', '=', employee.id)])
            }
        challenge_rows = []
        for challenge in challenges:
            joined = own_participation.get(challenge.id)
            participation_rows = Participation.sudo().search([('challenge_id', '=', challenge.id)], order='create_date desc')
            challenge_rows.append({
                'id': challenge.id,
                'name': challenge.name,
                'description': challenge.description or '',
                'xp_value': challenge.xp_value,
                'difficulty': challenge.difficulty,
                'evidence_required': challenge.evidence_required,
                'challenge_type': challenge.challenge_type,
                'game_config': challenge.game_config if is_manager else self._player_config(challenge),
                'deadline': str(challenge.deadline or ''),
                'state': challenge.state,
                'participants': len(participation_rows),
                'participation': {'id': joined.id, 'state': joined.state, 'progress': joined.progress, 'eligibility_status': joined.eligibility_status, 'verification_reason': joined.verification_reason or ''} if joined else False,
                'participant_details': ([{
                    'employee': row.employee_id.name,
                    'joined_on': str(row.create_date or ''),
                    'state': row.state,
                    'progress': row.progress,
                    'xp': row.xp_awarded,
                    'eligibility': row.eligibility_status,
                    'reason': row.verification_reason or '',
                } for row in participation_rows] if is_manager else []),
            })
        awarded = request.env['esg.badge.award'].sudo()
        badges = request.env['esg.badge'].search([])
        badge_rows = [{'id': badge.id, 'name': badge.name, 'description': badge.description or '', 'minimum_xp': badge.minimum_xp, 'unlocked': bool(employee and awarded.search_count([('badge_id', '=', badge.id), ('employee_id', '=', employee.id)]))} for badge in badges]
        totals = {}
        for row in Participation.sudo().search([('state', '=', 'approved')]):
            totals[row.employee_id.id] = totals.get(row.employee_id.id, {'name': row.employee_id.name, 'xp': 0})
            totals[row.employee_id.id]['xp'] += row.xp_awarded
        leaderboard = [dict(value, rank=index + 1) for index, value in enumerate(sorted(totals.values(), key=lambda item: item['xp'], reverse=True)[:5])]
        templates = []
        reviews = []
        if is_manager:
            templates = [{'id': row.id, 'name': row.name, 'description': row.description or '', 'xp_value': row.xp_value, 'difficulty': row.difficulty, 'challenge_type': row.challenge_type, 'game_config': row.game_config or {}} for row in Challenge.search([('is_template', '=', True)], order='id')]
            for row in Participation.search([('state', '=', 'under_review')], order='create_date desc', limit=50):
                reviews.append({'id': row.id, 'employee': row.employee_id.name, 'challenge': row.challenge_id.name, 'proof': row.proof.decode() if row.proof else False, 'proof_filename': row.proof_filename or '', 'reason': row.verification_reason or ''})
        rewards = [{'id': row.id, 'name': row.name, 'description': row.description or '', 'points_required': row.points_required, 'stock': row.stock, 'active': row.active} for row in request.env['esg.reward'].search([('active', '=', True)])]
        activity = []
        if is_manager:
            for row in Participation.sudo().search([], order='create_date desc', limit=100):
                activity.append({'employee': row.employee_id.name, 'challenge': row.challenge_id.name, 'state': row.state, 'progress': row.progress, 'xp': row.xp_awarded, 'eligibility': row.eligibility_status})
        return {'is_manager': is_manager, 'can_join': bool(employee), 'challenges': challenge_rows, 'badges': badge_rows, 'rewards': rewards, 'leaderboard': leaderboard, 'activity': activity, 'templates': templates, 'reviews': reviews}

    @http.route('/ecosphere/api/gamification/challenges/create', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification_create_challenge(self, name, description, xp_value, difficulty, deadline, state='active', challenge_type='action', game_config=None):
        self._require_manager()
        if not (name or '').strip() or not (description or '').strip() or not deadline:
            raise ValidationError(_("Name, description, and deadline are required."))
        allowed_types = {'quiz', 'scenario', 'checklist', 'photo', 'action'}
        if state not in {'draft', 'active'} or difficulty not in {'easy', 'medium', 'hard'} or challenge_type not in allowed_types:
            raise ValidationError(_("Invalid challenge settings."))
        config = game_config if isinstance(game_config, dict) else {}
        if challenge_type in {'quiz', 'scenario'}:
            questions = config.get('questions', [])
            if not isinstance(questions, list) or not questions or len(questions) > 12:
                raise ValidationError(_("Add between 1 and 12 questions."))
            cleaned_questions = []
            for question in questions:
                prompt = str(question.get('prompt') or '').strip()
                options = [str(value).strip() for value in question.get('options', []) if str(value).strip()]
                try:
                    answer = int(question.get('answer'))
                except (TypeError, ValueError):
                    answer = -1
                if not prompt or len(options) < 2 or answer < 0 or answer >= len(options):
                    raise ValidationError(_("Every question needs a prompt, at least two options, and one correct answer."))
                cleaned_questions.append({'prompt': prompt[:500], 'options': options[:6], 'answer': answer})
            try:
                pass_score = int(config.get('pass_score', 80))
            except (TypeError, ValueError):
                pass_score = 80
            if not 1 <= pass_score <= 100:
                raise ValidationError(_("Pass score must be between 1 and 100."))
            config = {'questions': cleaned_questions, 'pass_score': pass_score}
        elif challenge_type == 'checklist':
            items = [str(value).strip() for value in config.get('items', []) if str(value).strip()]
            if not items or len(items) > 12:
                raise ValidationError(_("Add between 1 and 12 checklist actions."))
            config = {'items': items[:12]}
        elif challenge_type == 'photo':
            config = {'evidence_rule': 'A clear original photo must visibly contain the required subject.'}
        else:
            config = {}
        challenge = request.env['esg.challenge'].create({
            'name': name.strip(), 'description': description.strip(), 'xp_value': max(int(xp_value or 0), 0),
            'difficulty': difficulty, 'deadline': deadline, 'state': state, 'challenge_type': challenge_type, 'game_config': config,
        })
        return {'id': challenge.id, 'message': _("Challenge created.")}

    @http.route('/ecosphere/api/gamification/templates/<int:template_id>/publish', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification_publish_template(self, template_id, deadline, name=None, state='active'):
        self._require_manager()
        template = request.env['esg.challenge'].browse(template_id).exists()
        if not template or not template.is_template or not deadline or state not in {'draft', 'active'}:
            raise ValidationError(_("Select a valid template, publication state, and deadline."))
        challenge = template.copy({'name': (name or template.name).strip(), 'deadline': deadline, 'state': state, 'is_template': False})
        return {'id': challenge.id, 'message': _("Challenge published to the employee portal.")}

    @http.route('/ecosphere/api/gamification/challenges/<int:challenge_id>/join', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification_join_challenge(self, challenge_id):
        employee = request.env.user.employee_id
        if not employee:
            raise ValidationError(_("Your employee profile is not ready. Ask an administrator to create your employee access."))
        challenge = request.env['esg.challenge'].browse(challenge_id).exists()
        if not challenge or challenge.state != 'active':
            raise ValidationError(_("Only active challenges can be joined."))
        Participation = request.env['esg.challenge.participation']
        if Participation.search_count([('challenge_id', '=', challenge.id), ('employee_id', '=', employee.id)]):
            raise ValidationError(_("You have already joined this challenge."))
        participation = Participation.create({'challenge_id': challenge.id, 'employee_id': employee.id})
        return {'id': participation.id, 'message': _("You joined the challenge. Start making progress!")}

    @http.route('/ecosphere/api/gamification/participations/<int:participation_id>/play', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification_play(self, participation_id, payload=None):
        participation = request.env['esg.challenge.participation'].browse(participation_id).exists()
        if not participation or participation.employee_id != request.env.user.employee_id:
            raise ValidationError(_("You can only complete your own challenge participation."))
        if participation.state in {'approved', 'rejected'}:
            raise ValidationError(_("This challenge submission has already been finalised."))
        payload = payload or {}
        challenge = participation.challenge_id
        config = challenge.game_config or {}
        if challenge.challenge_type in {'quiz', 'scenario'}:
            questions = config.get('questions', [])
            answers = payload.get('answers', {}) if isinstance(payload, dict) else {}
            if not questions or len(answers) != len(questions):
                raise ValidationError(_("Answer every question before submitting."))
            correct = sum(1 for index, question in enumerate(questions) if str(answers.get(str(index))) == str(question.get('answer')))
            score = round((correct / len(questions)) * 100)
            required = int(config.get('pass_score', 80))
            values = {'activity_data': {'answers': answers, 'score': score}, 'attempt_count': participation.attempt_count + 1, 'progress': score}
            if score >= required:
                participation.write(values)
                participation._award()
                return {'message': _("Great work — you passed and earned %(xp)s XP.") % {'xp': challenge.xp_value}, 'status': 'eligible'}
            values.update({'eligibility_status': 'not_eligible', 'verification_reason': _("Score %(score)s%%. %(required)s%% is required to earn XP.") % {'score': score, 'required': required}})
            participation.write(values)
            return {'message': _("Not eligible for XP yet. Review the material and try again."), 'status': 'not_eligible'}
        if challenge.challenge_type == 'checklist':
            completed = payload.get('completed_items', []) if isinstance(payload, dict) else []
            items = config.get('items', [])
            if len(set(completed)) < len(items):
                raise ValidationError(_("Complete every checklist action before submitting."))
            participation.write({'activity_data': {'completed_items': completed}, 'progress': 100})
            participation._award()
            return {'message': _("Checklist completed — %(xp)s XP awarded.") % {'xp': challenge.xp_value}, 'status': 'eligible'}
        if challenge.challenge_type == 'photo':
            proof = payload.get('proof') if isinstance(payload, dict) else False
            filename = (payload.get('filename') if isinstance(payload, dict) else '') or 'plant-photo.jpg'
            try:
                decoded = base64.b64decode(proof or '', validate=True)
            except Exception:
                raise ValidationError(_("Upload a valid JPG or PNG photo."))
            if not decoded or len(decoded) > 5 * 1024 * 1024:
                raise ValidationError(_("Photos must be between 1 byte and 5 MB."))
            status, reason, confidence = participation._validate_photo_with_vision(proof, filename)
            participation.write({'proof': proof, 'proof_filename': filename[:255], 'activity_data': {'vision_confidence': confidence}, 'progress': 100, 'eligibility_status': status, 'verification_reason': reason})
            if status == 'eligible':
                participation._award()
                return {'message': _("Plant verified — %(xp)s XP awarded.") % {'xp': challenge.xp_value}, 'status': status}
            if status == 'not_eligible':
                participation.write({'state': 'rejected'})
                return {'message': _("Not eligible for promotion: %(reason)s") % {'reason': reason}, 'status': status}
            participation.write({'state': 'under_review'})
            return {'message': _("Photo submitted for administrator review."), 'status': status}
        participation.write({'activity_data': payload, 'progress': 100, 'state': 'under_review', 'eligibility_status': 'pending_review'})
        return {'message': _("Action submitted for administrator review."), 'status': 'pending_review'}

    @http.route('/ecosphere/api/gamification/participations/<int:participation_id>/review', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification_review(self, participation_id, approved, note=None):
        self._require_manager()
        participation = request.env['esg.challenge.participation'].browse(participation_id).exists()
        if not participation or participation.state != 'under_review':
            raise ValidationError(_("This submission is no longer awaiting review."))
        if approved:
            participation.write({'verification_reason': (note or _("Approved by administrator."))[:500]})
            participation._award()
            return {'message': _("Submission approved and XP awarded.")}
        participation.write({'state': 'rejected', 'eligibility_status': 'not_eligible', 'verification_reason': (note or _("Not eligible for promotion: the evidence does not meet this challenge's criteria."))[:500]})
        return {'message': _("Submission marked not eligible.")}

    def _social_activity_row(self, activity, participation=False):
        return {
            'id': activity.id, 'name': activity.name, 'description': activity.description or '',
            'activity_date': str(activity.activity_date or ''), 'department': activity.department_id.name,
            'department_id': activity.department_id.id, 'category': activity.category_id.name or '',
            'category_id': activity.category_id.id or False, 'points': activity.points,
            'capacity': activity.capacity, 'active': activity.active,
            'evidence_required': activity.evidence_required, 'participants': activity.participant_count,
            'participation': participation and {
                'id': participation.id, 'state': participation.state, 'proof_filename': participation.proof_filename or '',
                'approval_note': participation.approval_note or '', 'completion_date': str(participation.completion_date or ''),
            } or False,
        }

    @http.route('/ecosphere/api/social', type='json', auth='user', methods=['POST'], csrf=False)
    def social(self):
        """Role-safe social-impact feed. Employees only receive their own submissions."""
        is_manager = request.env.user.has_group('eco_sphere_esg.group_esg_manager')
        employee = request.env.user.employee_id
        Activity = request.env['esg.csr.activity']
        Participation = request.env['esg.csr.participation']
        activities = Activity.search([] if is_manager else [('active', '=', True)], order='activity_date asc, id desc')
        own = {row.activity_id.id: row for row in Participation.search([('employee_id', '=', employee.id)])} if employee else {}
        activity_rows = [self._social_activity_row(row, own.get(row.id)) for row in activities]
        submissions = []
        if is_manager:
            for row in Participation.sudo().search([], order='create_date desc', limit=100):
                submissions.append({'id': row.id, 'employee': row.employee_id.name, 'activity': row.activity_id.name, 'state': row.state, 'proof': row.proof.decode() if row.proof else False, 'proof_filename': row.proof_filename or '', 'points': row.points_earned, 'note': row.approval_note or '', 'submitted_at': str(row.submitted_at or '')})
        return {
            'is_manager': is_manager, 'can_participate': bool(employee), 'activities': activity_rows,
            'my_participations': [self._social_activity_row(row.activity_id, row) for row in own.values()],
            'submissions': submissions,
            'metrics': {'activities': len(activity_rows), 'joined': len(own), 'pending': len([row for row in own.values() if row.state == 'submitted']), 'approved_points': sum(row.points_earned for row in own.values() if row.state == 'approved')},
            'departments': request.env['esg.department'].name_search('', limit=100) if is_manager else [],
            'categories': [(row['id'], row['name']) for row in request.env['esg.category'].search_read([('category_type', '=', 'csr')], ['name'])] if is_manager else [],
        }

    @http.route('/ecosphere/api/social/activities/create', type='json', auth='user', methods=['POST'], csrf=False)
    def social_activity_create(self, name, description, activity_date, department_id=None, department_name=None, points=0, capacity=0, evidence_required=False, category_id=None, active=True):
        self._require_manager()
        if len((name or '').strip()) < 2 or not activity_date:
            raise ValidationError(_("Name, activity date, and department are required."))
        department = self._social_department(department_id, department_name)
        activity = request.env['esg.csr.activity'].create({'name': name.strip(), 'description': (description or '').strip(), 'activity_date': activity_date, 'department_id': department.id, 'category_id': int(category_id) if category_id else False, 'points': max(int(points or 0), 0), 'capacity': max(int(capacity or 0), 0), 'evidence_required': bool(evidence_required), 'active': bool(active)})
        return {'id': activity.id, 'message': _("CSR activity saved.")}

    @http.route('/ecosphere/api/social/activities/<int:activity_id>/update', type='json', auth='user', methods=['POST'], csrf=False)
    def social_activity_update(self, activity_id, values=None):
        self._require_manager()
        activity = request.env['esg.csr.activity'].browse(activity_id).exists()
        if not activity:
            raise ValidationError(_("This CSR activity no longer exists."))
        values = values or {}
        allowed = {'name', 'description', 'activity_date', 'department_id', 'category_id', 'points', 'capacity', 'evidence_required', 'active'}
        cleaned = {key: value for key, value in values.items() if key in allowed}
        if 'department_name' in values:
            cleaned['department_id'] = self._social_department(cleaned.get('department_id'), values['department_name']).id
        for key in ('department_id', 'category_id', 'points', 'capacity'):
            if key in cleaned:
                cleaned[key] = int(cleaned[key]) if cleaned[key] not in ('', None, False) else False
        activity.write(cleaned)
        return {'id': activity.id, 'message': _("CSR activity updated.")}

    @http.route('/ecosphere/api/social/activities/<int:activity_id>/archive', type='json', auth='user', methods=['POST'], csrf=False)
    def social_activity_archive(self, activity_id):
        self._require_manager()
        activity = request.env['esg.csr.activity'].browse(activity_id).exists()
        if not activity:
            raise ValidationError(_("This CSR activity no longer exists."))
        activity.write({'active': False})
        return {'message': _("CSR activity archived. It is no longer visible to employees.")}

    @http.route('/ecosphere/api/social/activities/<int:activity_id>/join', type='json', auth='user', methods=['POST'], csrf=False)
    def social_activity_join(self, activity_id):
        employee = request.env.user.employee_id
        if not employee:
            raise ValidationError(_("Your employee profile is not ready. Ask an administrator to create employee access."))
        activity = request.env['esg.csr.activity'].browse(activity_id).exists()
        if not activity or not activity.active:
            raise ValidationError(_("This activity is not currently open for participation."))
        Participation = request.env['esg.csr.participation']
        if activity.capacity and activity.participant_count >= activity.capacity:
            raise ValidationError(_("This activity has reached its participation capacity."))
        if Participation.search_count([('employee_id', '=', employee.id), ('activity_id', '=', activity.id)]):
            raise ValidationError(_("You have already joined this activity."))
        row = Participation.create({'employee_id': employee.id, 'activity_id': activity.id})
        return {'id': row.id, 'message': _("You joined the activity. Submit your completion when ready.")}

    @http.route('/ecosphere/api/social/participations/<int:participation_id>/submit', type='json', auth='user', methods=['POST'], csrf=False)
    def social_participation_submit(self, participation_id, proof=None, filename=None):
        employee = request.env.user.employee_id
        row = request.env['esg.csr.participation'].browse(participation_id).exists()
        if not row or row.employee_id != employee:
            raise ValidationError(_("You can only submit your own participation."))
        if row.state == 'approved':
            raise ValidationError(_("This participation has already been approved."))
        if row.activity_id.evidence_required:
            try:
                decoded = base64.b64decode(proof or '', validate=True)
            except Exception:
                raise ValidationError(_("Upload a valid JPG, PNG, or PDF proof file."))
            if not decoded or len(decoded) > 5 * 1024 * 1024:
                raise ValidationError(_("Proof files must be up to 5 MB."))
            suffix = (filename or '').lower().rsplit('.', 1)[-1]
            if suffix not in {'jpg', 'jpeg', 'png', 'pdf'}:
                raise ValidationError(_("Use a JPG, PNG, or PDF proof file."))
            row.write({'proof': proof, 'proof_filename': (filename or 'proof-file')[:255]})
        row.action_submit()
        return {'message': _("Completion submitted for administrator approval.")}

    @http.route('/ecosphere/api/social/participations/<int:participation_id>/review', type='json', auth='user', methods=['POST'], csrf=False)
    def social_participation_review(self, participation_id, approved, note=None):
        self._require_manager()
        row = request.env['esg.csr.participation'].browse(participation_id).exists()
        if not row or row.state != 'submitted':
            raise ValidationError(_("This participation is not awaiting review."))
        row.write({'approval_note': (note or '').strip()[:500]})
        if approved:
            row.action_approve()
            return {'message': _("Participation approved and points awarded.")}
        row.action_reject()
        return {'message': _("Participation rejected. The employee can update and resubmit evidence.")}

    @http.route('/ecosphere/api/dashboard', type='http', auth='user', methods=['GET'], csrf=False)
    def dashboard(self):
        scores = request.env['esg.department.score'].sudo()
        scores.action_recalculate_all()
        latest = {}
        for score in scores.search([], order='score_date desc, id desc'):
            latest.setdefault(score.department_id.id, score)
        rows = list(latest.values())
        average = lambda field: round(sum(getattr(row, field) for row in rows) / len(rows), 1) if rows else 0.0
        return request.make_json_response({
            'user': {
                'name': request.env.user.name,
                'email': request.env.user.login,
                'initials': ''.join(part[:1] for part in request.env.user.name.split()[:2]).upper(),
                'role': 'ESG Manager' if request.env.user.has_group('eco_sphere_esg.group_esg_manager') else 'ESG User',
                'workspace': request.env.company.name,
            },
            'kpis': {'environmental': average('environmental_score'), 'social': average('social_score'), 'governance': average('governance_score'), 'overall': average('total_score')},
            'ranking': [{'name': row.department_id.name, 'score': round(row.total_score, 1)} for row in sorted(rows, key=lambda row: row.total_score, reverse=True)[:5]],
            'counts': {
                'carbon_transactions': request.env['esg.carbon.transaction'].search_count([]),
                'environmental_goals': request.env['esg.environmental.goal'].search_count([]),
                'csr_activities': request.env['esg.csr.activity'].search_count([]),
                'active_challenges': request.env['esg.challenge'].search_count([('state', '=', 'active')]),
                'open_issues': request.env['esg.compliance.issue'].search_count([('state', '=', 'open')]),
            },
        })
