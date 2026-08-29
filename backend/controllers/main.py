from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError


class EcoSphereAPI(http.Controller):
    @http.route('/ecosphere/api/signup', type='json', auth='public', methods=['POST'], csrf=False)
    def signup(self, name, email, password):
        name, email = (name or '').strip(), (email or '').strip().lower()
        if len(name) < 2 or '@' not in email or len(password or '') < 8:
            raise ValidationError(_("Enter your name, a valid email address, and a password of at least 8 characters."))
        Users = request.env['res.users'].sudo()
        if Users.search_count([('login', '=', email)]):
            raise ValidationError(_("An account already exists for this email address."))
        group = request.env.ref('eco_sphere_esg.group_esg_user').sudo()
        internal_group = request.env.ref('base.group_user').sudo()
        user = Users.with_context(no_reset_password=True).create({
            'name': name, 'login': email, 'email': email, 'password': password,
            'groups_id': [(6, 0, [internal_group.id, group.id])],
        })
        return {'id': user.id, 'login': user.login}

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
            'user': {'name': request.env.user.name},
            'kpis': {'environmental': average('environmental_score'), 'social': average('social_score'), 'governance': average('governance_score'), 'overall': average('total_score')},
            'ranking': [{'name': row.department_id.name, 'score': round(row.total_score, 1)} for row in sorted(rows, key=lambda row: row.total_score, reverse=True)[:5]],
        })
