from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError


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
        'policies': ('esg.policy', ('name', 'reference', 'content', 'effective_date', 'state', 'active')),
        'policy-acknowledgements': ('esg.policy.acknowledgement', ('policy_id', 'employee_id', 'state')),
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
        return [{'name': name, **fields_info[name]} for name in allowed if name in fields_info and not fields_info[name].get('readonly')]

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
        if not request.env.user.has_group('eco_sphere_esg.group_esg_manager'):
            raise ValidationError(_("Only an EcoSphere administrator can manage employee access."))

    @http.route('/ecosphere/api/resources/<string:slug>', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_list(self, slug, limit=100, query=None):
        records, allowed = self._resource(slug)
        records.check_access_rights('read')
        domain = [('display_name', 'ilike', query)] if query else []
        rows = records.search_read(domain, list(allowed), limit=min(max(int(limit or 100), 1), 200), order='id desc')
        return {'records': rows, 'fields': self._field_schema(records, allowed), 'can_create': records.check_access_rights('create', raise_exception=False), 'can_write': records.check_access_rights('write', raise_exception=False), 'can_delete': records.check_access_rights('unlink', raise_exception=False)}

    @http.route('/ecosphere/api/resources/<string:slug>/options/<string:field_name>', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_options(self, slug, field_name, query=None):
        records, allowed = self._resource(slug)
        if field_name not in allowed or records._fields[field_name].type != 'many2one':
            raise ValidationError(_("Invalid relation field."))
        relation = request.env[records._fields[field_name].comodel_name]
        relation.check_access_rights('read')
        domain = [('display_name', 'ilike', query)] if query else []
        return relation.name_search(name=query or '', args=domain, limit=100)

    @http.route('/ecosphere/api/resources/<string:slug>/create', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_create(self, slug, values):
        records, allowed = self._resource(slug)
        records.check_access_rights('create')
        record = records.create(self._clean_values(records, allowed, values))
        return {'id': record.id, 'message': _("Saved successfully.")}

    @http.route('/ecosphere/api/resources/<string:slug>/<int:record_id>/update', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_update(self, slug, record_id, values):
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
        records, _allowed = self._resource(slug)
        record = records.browse(record_id).exists()
        if not record:
            raise ValidationError(_("This record no longer exists."))
        record.check_access_rights('unlink')
        record.check_access_rule('unlink')
        record.unlink()
        return {'message': _("Deleted successfully.")}

    @http.route('/ecosphere/api/team', type='json', auth='user', methods=['POST'], csrf=False)
    def team_list(self):
        self._require_manager()
        user_group = request.env.ref('eco_sphere_esg.group_esg_user')
        users = request.env['res.users'].with_context(active_test=False).search([
            ('id', '!=', request.env.ref('base.user_root').id),
            ('groups_id', 'in', user_group.id),
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
        user = Users.with_context(no_reset_password=True).create({
            'name': name, 'login': email, 'email': email, 'password': password,
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

    @http.route('/ecosphere/api/signup', type='json', auth='public', methods=['POST'], csrf=False)
    def signup(self, name, email, password):
        """Provision an enterprise owner; employee accounts remain admin-only."""
        name, email = (name or '').strip(), (email or '').strip().lower()
        if len(name) < 2 or '@' not in email or len(password or '') < 8:
            raise ValidationError(_("Enter a name, valid work email, and password of at least 8 characters."))
        Users = request.env['res.users'].sudo()
        if Users.search_count([('login', '=', email)]):
            raise ValidationError(_("An account already exists for this email address."))
        manager_group = request.env.ref('eco_sphere_esg.group_esg_manager').sudo()
        user = Users.with_context(no_reset_password=True).create({
            'name': name,
            'login': email,
            'email': email,
            'password': password,
            'groups_id': [(6, 0, [manager_group.id])],
        })
        return {'id': user.id, 'message': _("Enterprise administrator account created.")}

    @http.route('/ecosphere/api/dashboard', type='http', auth='user', methods=['GET'], csrf=False)
    def dashboard(self):
        scores = request.env['esg.department.score']
        scores.action_recalculate_all()
        latest = {}
        for score in scores.search([], order='score_date desc, id desc'):
            latest.setdefault(score.department_id.id, score)
        rows = list(latest.values())
        average = lambda field: round(sum(getattr(row, field) for row in rows) / len(rows), 1) if rows else 0.0
        return request.make_json_response({
            'user': {
                'name': request.env.user.name,
                'initials': ''.join(part[:1] for part in request.env.user.name.split()[:2]).upper(),
                'role': 'ESG Manager' if request.env.user.has_group('eco_sphere_esg.group_esg_manager') else 'ESG User',
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
