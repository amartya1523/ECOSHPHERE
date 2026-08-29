from odoo import fields, http, _
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
        'leaderboard': ('esg.employee.leaderboard', ('employee_id', 'department_id', 'total_xp', 'approved_challenges', 'badge_count')),
        'departments': ('esg.department', ('name', 'code', 'manager_id', 'parent_id', 'active')),
        'categories': ('esg.category', ('name', 'category_type', 'active')),
    }

    def _resource(self, slug):
        definition = self.RESOURCES.get(slug)
        if not definition:
            raise ValidationError(_("Unknown EcoSphere resource."))
        model, allowed = definition
        return request.env[model].sudo(), allowed

    def _ensure_reference_data(self):
        env = request.env
        department = env['esg.department'].sudo().search([], limit=1)
        if not department:
            department = env['esg.department'].sudo().create({'name': 'Operations', 'code': 'OPS'})

        factor = env['esg.emission.factor'].sudo().search([], limit=1)
        if not factor:
            factor = env['esg.emission.factor'].sudo().create({
                'name': 'Grid Electricity',
                'source_type': 'manual',
                'unit': 'kWh',
                'co2e_factor': 0.708,
                'effective_from': fields.Date.today(),
            })

        if not env['product.template'].sudo().search([], limit=1):
            env['product.template'].sudo().create({'name': 'EcoSphere Demo Product', 'sale_ok': True, 'purchase_ok': True})

        csr_category = env['esg.category'].sudo().search([('category_type', '=', 'csr')], limit=1)
        if not csr_category:
            csr_category = env['esg.category'].sudo().create({'name': 'Community', 'category_type': 'csr'})

        challenge_category = env['esg.category'].sudo().search([('category_type', '=', 'challenge')], limit=1)
        if not challenge_category:
            challenge_category = env['esg.category'].sudo().create({'name': 'Carbon Reduction', 'category_type': 'challenge'})

        if not env['esg.csr.activity'].sudo().search([], limit=1):
            env['esg.csr.activity'].sudo().create({
                'name': 'Beach Cleanup',
                'category_id': csr_category.id,
                'department_id': department.id,
                'description': '<p>Join a local cleanup and submit your participation.</p>',
                'activity_date': fields.Date.today(),
                'points': 70,
            })

        if not env['esg.challenge'].sudo().search([], limit=1):
            env['esg.challenge'].sudo().with_context(esg_state_action=True).create({
                'name': 'Plastic-Free Week',
                'category_id': challenge_category.id,
                'description': '<p>Reduce single-use plastic for one work week.</p>',
                'xp_value': 180,
                'difficulty': 'easy',
                'deadline': fields.Date.add(fields.Date.today(), days=30),
                'state': 'active',
            })

        if not env['esg.reward'].sudo().search([], limit=1):
            env['esg.reward'].sudo().create({
                'name': 'Green Lunch Voucher',
                'description': 'Redeem earned XP for a sustainable lunch.',
                'points_required': 100,
                'stock': 25,
            })

        if not env['esg.policy'].sudo().search([], limit=1):
            env['esg.policy'].sudo().create({
                'name': 'Code of Ethics',
                'reference': 'ETHICS-001',
                'content': '<p>Act responsibly and document governance commitments.</p>',
                'effective_date': fields.Date.today(),
                'state': 'effective',
            })

        return department

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

    @http.route('/ecosphere/api/resources/<string:slug>', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_list(self, slug, limit=100, query=None):
        self._ensure_reference_data()
        records, allowed = self._resource(slug)
        records.check_access_rights('read')
        domain = [('display_name', 'ilike', query)] if query else []
        rows = records.search_read(domain, list(allowed), limit=min(max(int(limit or 100), 1), 200), order='id desc')
        read_only_model = not getattr(records, '_auto', True)
        return {
            'records': rows,
            'fields': self._field_schema(records, allowed),
            'can_create': False if read_only_model else records.check_access_rights('create', raise_exception=False),
            'can_write': False if read_only_model else records.check_access_rights('write', raise_exception=False),
            'can_delete': False if read_only_model else records.check_access_rights('unlink', raise_exception=False),
        }

    @http.route('/ecosphere/api/resources/<string:slug>/options/<string:field_name>', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_options(self, slug, field_name, query=None):
        self._ensure_reference_data()
        records, allowed = self._resource(slug)
        if field_name not in allowed or records._fields[field_name].type != 'many2one':
            raise ValidationError(_("Invalid relation field."))
        relation = request.env[records._fields[field_name].comodel_name].sudo()
        relation.check_access_rights('read')
        domain = [('display_name', 'ilike', query)] if query else []
        return relation.name_search(name=query or '', args=domain, limit=100)

    @http.route('/ecosphere/api/resources/<string:slug>/create', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_create(self, slug, values):
        self._ensure_reference_data()
        records, allowed = self._resource(slug)
        records.check_access_rights('create')
        if slug in {'challenges'}:
            records = records.with_context(esg_state_action=True)
        record = records.create(self._clean_values(records, allowed, values))
        return {'id': record.id, 'message': _("Saved successfully.")}

    @http.route('/ecosphere/api/resources/<string:slug>/<int:record_id>/update', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_update(self, slug, record_id, values):
        self._ensure_reference_data()
        records, allowed = self._resource(slug)
        record = records.browse(record_id).exists()
        if not record:
            raise ValidationError(_("This record no longer exists."))
        record.check_access_rights('write')
        record.check_access_rule('write')
        if slug in {'challenges'}:
            record = record.with_context(esg_state_action=True)
        record.write(self._clean_values(records, allowed, values))
        return {'id': record.id, 'message': _("Changes saved.")}

    @http.route('/ecosphere/api/resources/<string:slug>/<int:record_id>/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def resource_delete(self, slug, record_id):
        self._ensure_reference_data()
        records, _allowed = self._resource(slug)
        record = records.browse(record_id).exists()
        if not record:
            raise ValidationError(_("This record no longer exists."))
        record.check_access_rights('unlink')
        record.check_access_rule('unlink')
        record.unlink()
        return {'message': _("Deleted successfully.")}
    @http.route('/ecosphere/api/signup', type='json', auth='public', methods=['POST'], csrf=False)
    def signup(self, name, email, password):
        name, email = (name or '').strip(), (email or '').strip().lower()
        if len(name) < 2 or '@' not in email or len(password or '') < 8:
            raise ValidationError(_("Enter your name, a valid email address, and a password of at least 8 characters."))
        Users = request.env['res.users'].sudo()
        if Users.search_count([('login', '=', email)]):
            raise ValidationError(_("An account already exists for this email address."))
        # This is a single-workspace local deployment: a self-registered account
        # is the workspace owner. Production installations should disable this
        # public route and provision users through an invitation/SSO flow.
        group = request.env.ref('eco_sphere_esg.group_esg_manager').sudo()
        internal_group = request.env.ref('base.group_user').sudo()
        user = Users.with_context(no_reset_password=True).create({
            'name': name, 'login': email, 'email': email, 'password': password,
            'groups_id': [(6, 0, [internal_group.id, group.id])],
        })
        request.env['hr.employee'].sudo().create({
            'name': name,
            'work_email': email,
            'user_id': user.id,
            'esg_department_id': self._ensure_reference_data().id,
        })
        return {'id': user.id, 'login': user.login}

    @http.route('/ecosphere/api/dashboard', type='http', auth='user', methods=['GET'], csrf=False)
    def dashboard(self):
        self._ensure_reference_data()
        scores = request.env['esg.department.score'].sudo()
        scores.action_recalculate_all()
        latest = {}
        for score in scores.search([], order='score_date desc, id desc'):
            latest.setdefault(score.department_id.id, score)
        rows = list(latest.values())
        average = lambda field: round(sum(getattr(row, field) for row in rows) / len(rows), 1) if rows else 0.0
        return request.make_json_response({
            'user': {'name': request.env.user.name},
            'kpis': {'environmental': average('environmental_score'), 'social': average('social_score'), 'governance': average('governance_score'), 'overall': average('total_score')},
            'ranking': [{'name': row.department_id.name, 'score': round(row.total_score, 1)} for row in sorted(rows, key=lambda row: row.total_score, reverse=True)[:5]],
        })
