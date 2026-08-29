import os

from odoo import SUPERUSER_ID, api, fields


def post_init_hook(env):
    seed_demo_accounts(env)


def seed_demo_accounts(env):
    if os.getenv("ECOSPHERE_SEED_DEMO_ACCOUNTS", "0") != "1":
        return

    env = api.Environment(env.cr, SUPERUSER_ID, {})
    Company = env["res.company"].sudo()
    Department = env["esg.department"].sudo()
    Employee = env["hr.employee"].sudo()
    Users = env["res.users"].sudo()
    Challenge = env["esg.challenge"].sudo()

    company = Company.search([("name", "=", "Northstar Co.")], limit=1)
    if not company:
        company = Company.create({"name": "Northstar Co."})

    department = Department.search([("code", "=", "OPS")], limit=1)
    if not department:
        department = Department.create({"name": "Operations", "code": "OPS", "company_id": company.id})

    groups = {
        "internal": env.ref("base.group_user").id,
        "manager": env.ref("eco_sphere_esg.group_esg_manager").id,
        "user": env.ref("eco_sphere_esg.group_esg_user").id,
    }

    _ensure_user(
        Users,
        "Amartya Singh",
        "admin@ecosphere.local",
        "Admin@EcoSphere2026",
        company,
        [groups["internal"], groups["manager"]],
    )
    employee_user = _ensure_user(
        Users,
        "Priya Mehta",
        "employee@ecosphere.local",
        "Employee@EcoSphere2026",
        company,
        [groups["internal"], groups["user"]],
    )
    employee = Employee.search([("user_id", "=", employee_user.id)], limit=1)
    if not employee:
        employee = Employee.create({
            "name": "Priya Mehta",
            "user_id": employee_user.id,
            "company_id": company.id,
            "esg_department_id": department.id,
        })
    elif not employee.esg_department_id:
        employee.write({"esg_department_id": department.id})

    category = env.ref("eco_sphere_esg.category_challenge_carbon", raise_if_not_found=False)
    if not Challenge.search([("name", "=", "Plastic-Free Week"), ("is_template", "=", False)], limit=1):
        Challenge.with_context(esg_state_action=True).create({
            "name": "Plastic-Free Week",
            "description": "Complete five low-waste workplace actions and submit your progress.",
            "xp_value": 120,
            "difficulty": "medium",
            "deadline": fields.Date.to_string(fields.Date.add(fields.Date.today(), months=3)),
            "is_template": False,
            "challenge_type": "checklist",
            "category_id": category.id if category else False,
            "state": "active",
            "game_config": {
                "items": [
                    "Carry a reusable water bottle",
                    "Refuse single-use cutlery",
                    "Use a reusable lunch container",
                    "Avoid individually wrapped snacks",
                    "Share one waste-reduction tip with a colleague",
                ],
            },
        })


def _ensure_user(Users, name, login, password, company, group_ids):
    user = Users.search([("login", "=", login)], limit=1)
    values = {
        "name": name,
        "login": login,
        "email": login,
        "password": password,
        "company_id": company.id,
        "company_ids": [(6, 0, [company.id])],
        "groups_id": [(6, 0, group_ids)],
    }
    if user:
        user.write(values)
    else:
        user = Users.with_context(no_reset_password=True).create(values)
    return user
