import base64

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

    @staticmethod
    def _player_config(challenge):
        config = challenge.game_config or {}
        if challenge.challenge_type in {"quiz", "scenario"}:
            return {**config, "questions": [{key: value for key, value in question.items() if key != "answer"} for question in config.get("questions", [])]}
        return config

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
                'participants': Participation.sudo().search_count([('challenge_id', '=', challenge.id)]),
                'participation': {'id': joined.id, 'state': joined.state, 'progress': joined.progress, 'eligibility_status': joined.eligibility_status, 'verification_reason': joined.verification_reason or ''} if joined else False,
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
        return {'is_manager': is_manager, 'can_join': bool(employee), 'challenges': challenge_rows, 'badges': badge_rows, 'leaderboard': leaderboard, 'templates': templates, 'reviews': reviews}

    @http.route('/ecosphere/api/gamification/challenges/create', type='json', auth='user', methods=['POST'], csrf=False)
    def gamification_create_challenge(self, name, description, xp_value, difficulty, deadline, state='active'):
        self._require_manager()
        if not (name or '').strip() or not (description or '').strip() or not deadline:
            raise ValidationError(_("Name, description, and deadline are required."))
        if state not in {'draft', 'active'} or difficulty not in {'easy', 'medium', 'hard'}:
            raise ValidationError(_("Invalid challenge status or difficulty."))
        challenge = request.env['esg.challenge'].create({
            'name': name.strip(), 'description': description.strip(), 'xp_value': max(int(xp_value or 0), 0),
            'difficulty': difficulty, 'deadline': deadline, 'state': state, 'challenge_type': 'action',
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
