import json
import os
import re
from copy import deepcopy
from datetime import timedelta
from urllib import error as urlerror
from urllib import request as urlrequest

from odoo import fields
from odoo.exceptions import AccessError, ValidationError


TOOL_SCHEMAS = {
    "get_department_score": {
        "description": "Read latest ESG score for one scoped department and period.",
        "arguments": {"department_id": "integer", "period": "object"},
    },
    "get_carbon_transactions": {
        "description": "Read carbon transactions for a scoped department/date range.",
        "arguments": {"department_id": "integer", "date_range": "object"},
    },
    "get_compliance_issues": {
        "description": "Read scoped compliance issues, optionally by status or overdue flag.",
        "arguments": {"department_id": "integer", "status": "string?", "overdue_only": "boolean?"},
    },
    "get_employee_participation": {
        "description": "Read CSR participation and earned points for one employee.",
        "arguments": {"employee_id": "integer"},
    },
    "get_challenge_status": {
        "description": "Read active or joined challenge progress for one employee.",
        "arguments": {"employee_id": "integer?", "challenge_id": "integer?"},
    },
    "get_org_esg_summary": {
        "description": "Read aggregate ESG summary for the caller's accessible scope.",
        "arguments": {"period": "object"},
    },
}


PROJECT_CONTEXT = {
    "name": "EcoSphere",
    "purpose": "EcoSphere is an ESG management platform built as an Odoo module with a React dashboard. It brings carbon accounting, CSR participation, compliance tracking, scoring, reports, and employee gamification into one operational workspace.",
    "esg_meaning": "ESG means Environmental, Social, and Governance. In EcoSphere, Environmental covers emissions, carbon transactions, emission factors, and goals; Social covers CSR activities, employee participation, diversity metrics, and training; Governance covers policies, acknowledgements, audits, and compliance issues.",
    "built_modules": [
        "Environmental: emission factors, product ESG profiles, carbon transactions, environmental goals, carbon rollups.",
        "Social: CSR activities, proof-based participation workflow, diversity metrics, training completions.",
        "Governance: ESG policies, policy acknowledgements, audits, compliance issues, overdue tracking.",
        "Gamification: challenges, challenge participation, XP, badges, rewards, redemptions, employee leaderboard.",
        "Scoring and reports: department ESG scores, weighted total score, dashboards, standard ESG reports, custom report builder.",
        "AI query layer: Router, Executor, Validator, and Responder agents grounded in Odoo records.",
    ],
    "boundaries": [
        "Answer only EcoSphere, ESG-management, Odoo-record, dashboard, report, compliance, carbon, CSR, scoring, or gamification questions.",
        "Do not answer general knowledge, coding help, entertainment, news, weather, finance, or unrelated personal questions.",
        "For numeric business questions, use typed Odoo tools and cite records.",
    ],
}


class GroqLLMClient:
    base_url = "https://api.groq.com/openai/v1"

    def __init__(self, env):
        self.env = env
        params = env["ir.config_parameter"].sudo()
        self.api_key = (
            params.get_param("eco_sphere_esg.groq_api_key")
            or os.getenv("ECOSPHERE_GROQ_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or ""
        )
        self.model = (
            params.get_param("eco_sphere_esg.groq_model")
            or os.getenv("ECOSPHERE_GROQ_MODEL")
            or os.getenv("GROQ_MODEL")
            or "openai/gpt-oss-20b"
        )

    def available(self):
        return bool(self.api_key)

    def complete_json(self, system_prompt, user_prompt, max_tokens=700):
        content = self._complete(system_prompt, user_prompt, max_tokens=max_tokens, response_format={"type": "json_object"})
        return json.loads(self._strip_json_fence(content))

    def complete_text(self, system_prompt, user_prompt, max_tokens=500):
        return self._complete(system_prompt, user_prompt, max_tokens=max_tokens).strip()

    def _complete(self, system_prompt, user_prompt, max_tokens=500, response_format=None):
        if not self.available():
            raise ValidationError("Groq API key is not configured.")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        req = urlrequest.Request(
            "%s/chat/completions" % self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer %s" % self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "EcoSphere/1.0",
            },
            method="POST",
        )
        try:
            response = json.loads(urlrequest.urlopen(req, timeout=20).read().decode("utf-8"))
            return response["choices"][0]["message"]["content"] or ""
        except urlerror.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise ValidationError("Groq API request failed: %s %s" % (error.code, body[:300]))
        except Exception as error:
            raise ValidationError("Groq API request failed: %s" % error)

    def _strip_json_fence(self, value):
        text = (value or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
            text = re.sub(r"```$", "", text).strip()
        return text


class CallerContext:
    def __init__(self, env, role=None, department_id=None, employee_id=None):
        self.env = env
        self.user = env.user
        self.is_admin = bool(role == "admin" or self.user.has_group("eco_sphere_esg.group_esg_admin"))
        employee = self.user.employee_id
        self.employee_id = int(employee_id or (employee.id if employee else 0) or 0)
        self.department_id = int(department_id or (employee.esg_department_id.id if employee and employee.esg_department_id else 0) or 0)

    def accessible_department_ids(self):
        Department = self.env["esg.department"].sudo()
        if self.is_admin:
            return Department.search([("company_id", "=", self.env.company.id)]).ids
        if not self.department_id:
            return []
        return Department.search([("id", "child_of", [self.department_id])]).ids

    def enforce_department(self, requested_department_id=None):
        if not self.is_admin:
            return self.department_id or 0
        requested = int(requested_department_id or 0)
        accessible = self.accessible_department_ids()
        if requested and requested not in accessible:
            raise AccessError("That department is outside your accessible EcoSphere workspace.")
        return requested or (accessible[0] if len(accessible) == 1 else 0)


class RouterAgent:
    system_prompt = (
        "Classify an EcoSphere question, extract safe filters, select typed tools, "
        "apply RBAC scoping, and ask for clarification when intent is vague."
    )

    def __init__(self, env, llm=None):
        self.env = env
        self.llm = llm

    def route(self, question, history, caller):
        base = self._route_deterministic(question, history, caller)
        if not self.llm or not self.llm.available():
            return base
        try:
            llm_output = self._route_with_groq(question, history, caller, base)
            if llm_output:
                return llm_output
        except Exception as error:
            base["llm_error"] = str(error)
        return base

    def _route_deterministic(self, question, history, caller):
        text = (question or "").strip()
        lowered = text.lower()
        filters = deepcopy((history or {}).get("filters") or {})
        filters.update({"department_id": caller.department_id or filters.get("department_id") or 0})
        scoped_note = False

        requested_department = self._department_from_text(text)
        if caller.is_admin and requested_department:
            filters["department_id"] = requested_department.id
        elif requested_department and requested_department.id != caller.department_id:
            filters["department_id"] = caller.department_id or 0
            scoped_note = True
        elif not caller.is_admin:
            filters["department_id"] = caller.department_id or 0

        if caller.employee_id:
            filters.setdefault("employee_id", caller.employee_id)

        period = self._period_from_text(lowered)
        filters["period"] = period
        filters["date_range"] = {"start": period["start"], "end": period["end"], "label": period["label"]}

        metric = self._metric_from_text(lowered)
        if metric:
            filters["metric"] = metric

        if "carbon score" in lowered or any(term in lowered for term in ["score", "kpi", "esg score"]):
            intent, tools = "department_score", ["get_department_score"]
        elif any(term in lowered for term in ["carbon", "emission", "co2", "co2e", "ledger"]):
            intent, tools = "carbon_transactions", ["get_carbon_transactions"]
        elif any(term in lowered for term in ["overdue", "compliance", "issue", "issues", "risk"]):
            intent, tools = "compliance_issues", ["get_compliance_issues"]
            filters["overdue_only"] = "overdue" in lowered
            if "resolved" in lowered:
                filters["status"] = "resolved"
            elif "open" in lowered or "overdue" in lowered:
                filters["status"] = "open"
        elif any(term in lowered for term in ["participation", "csr", "volunteer", "points earned"]):
            intent, tools = "employee_participation", ["get_employee_participation"]
        elif any(term in lowered for term in ["challenge", "badge", "reward", "xp"]):
            intent, tools = "challenge_status", ["get_challenge_status"]
        elif any(term in lowered for term in ["summary", "report", "overall"]):
            intent, tools = "org_esg_summary", ["get_org_esg_summary"]
        elif self._is_project_context_question(lowered):
            intent, tools = "project_context", []
        elif self._is_out_of_scope(lowered):
            intent, tools = "out_of_scope", []
        elif self._is_vague(lowered):
            return {
                "intent": "clarify",
                "filters": filters,
                "needs_clarification": True,
                "clarifying_question": "Do you mean your department's ESG score, carbon transactions, compliance issues, CSR participation, challenge progress, or how EcoSphere works?",
                "candidate_tools": [],
                "rbac_scoped": scoped_note,
            }
        else:
            return {
                "intent": "clarify",
                "filters": filters,
                "needs_clarification": True,
                "clarifying_question": "I can help only with EcoSphere: ESG scores, carbon transactions, compliance issues, CSR participation, challenge progress, reports, or how this platform works. Which one should I check?",
                "candidate_tools": [],
                "rbac_scoped": scoped_note,
            }

        return {
            "intent": intent,
            "filters": filters,
            "needs_clarification": False,
            "clarifying_question": None,
            "candidate_tools": tools,
            "rbac_scoped": scoped_note,
        }

    def _route_with_groq(self, question, history, caller, fallback):
        department_rows = self.env["esg.department"].sudo().search([("company_id", "=", self.env.company.id)], limit=100)
        departments = [{"id": row.id, "name": row.name, "code": row.code} for row in department_rows]
        prompt = {
            "question": question,
            "history_filters": (history or {}).get("filters") or {},
            "caller": {
                "is_admin": caller.is_admin,
                "department_id": caller.department_id,
                "employee_id": caller.employee_id,
            },
            "departments": departments,
            "allowed_tools": list(TOOL_SCHEMAS),
            "fallback_route": fallback,
            "contract": {
                "intent": "one of department_score, carbon_transactions, compliance_issues, employee_participation, challenge_status, org_esg_summary, project_context, out_of_scope, clarify",
                "candidate_tools": "array of allowed tool names, empty when needs_clarification is true",
                "filters": "include department_id, employee_id when relevant, period/date_range from fallback unless explicitly changed",
                "needs_clarification": "boolean",
                "clarifying_question": "string or null",
                "rbac_scoped": "boolean",
            },
        }
        routed = self.llm.complete_json(
            self.system_prompt
            + " Return only JSON. Never invent a department id. For non-admin callers, force department_id to caller.department_id.",
            json.dumps(prompt, default=str),
        )
        return self._sanitize_llm_route(routed, fallback, caller)

    def _sanitize_llm_route(self, routed, fallback, caller):
        if fallback.get("intent") == "out_of_scope":
            fallback["llm_provider"] = None
            return fallback
        if fallback.get("intent") == "project_context":
            fallback["llm_provider"] = None
            return fallback
        allowed_intents = {"department_score", "carbon_transactions", "compliance_issues", "employee_participation", "challenge_status", "org_esg_summary", "project_context", "out_of_scope", "clarify"}
        intent = routed.get("intent") if routed.get("intent") in allowed_intents else fallback["intent"]
        if fallback.get("candidate_tools") and intent in {"project_context", "out_of_scope", "clarify"}:
            intent = fallback["intent"]
        tools = [tool for tool in routed.get("candidate_tools", []) if tool in TOOL_SCHEMAS]
        if intent in {"clarify", "project_context", "out_of_scope"} or routed.get("needs_clarification"):
            tools = []
        if intent != "clarify" and not tools:
            tools = fallback.get("candidate_tools", [])
        filters = deepcopy(fallback.get("filters") or {})
        filters.update({key: value for key, value in (routed.get("filters") or {}).items() if key in {
            "department_id", "employee_id", "period", "date_range", "metric", "status", "overdue_only", "challenge_id"
        }})
        if not caller.is_admin:
            filters["department_id"] = caller.department_id or 0
            if caller.employee_id:
                filters["employee_id"] = caller.employee_id
        elif filters.get("department_id"):
            filters["department_id"] = caller.enforce_department(filters.get("department_id"))
        filters.setdefault("period", fallback.get("filters", {}).get("period"))
        filters.setdefault("date_range", fallback.get("filters", {}).get("date_range"))
        return {
            "intent": intent,
            "filters": filters,
            "needs_clarification": bool(routed.get("needs_clarification") or intent == "clarify"),
            "clarifying_question": routed.get("clarifying_question") or fallback.get("clarifying_question"),
            "candidate_tools": tools,
            "rbac_scoped": bool(routed.get("rbac_scoped") or fallback.get("rbac_scoped")),
            "llm_provider": "groq",
        }

    def _is_vague(self, lowered):
        vague = {"how are we doing", "how am i doing", "status", "update", "what's up", "whats up"}
        return lowered.strip(" ?!.") in vague

    def _is_project_context_question(self, lowered):
        has_project_term = any(term in lowered for term in [
            "ecosphere", "esg", "environmental", "social", "governance", "carbon",
            "csr", "compliance", "audit", "policy", "challenge", "badge", "reward",
            "odoo", "dashboard", "report", "scoring", "module", "platform", "project",
        ])
        has_explainer_term = any(term in lowered for term in [
            "what is", "what does", "meaning", "mean", "explain", "how does",
            "how it works", "features", "built", "module", "modules", "about",
            "help", "use", "purpose",
        ])
        return has_project_term and has_explainer_term

    def _is_out_of_scope(self, lowered):
        out_of_scope_terms = [
            "weather", "news", "stock", "crypto", "joke", "poem", "song", "recipe",
            "movie", "sports", "cricket", "football", "dating", "leetcode", "dsa",
            "homework", "history", "geography", "politics", "translate", "summarize this article",
        ]
        if any(term in lowered for term in out_of_scope_terms):
            return True
        has_domain_term = any(term in lowered for term in [
            "ecosphere", "esg", "environmental", "social", "governance", "carbon",
            "csr", "compliance", "audit", "policy", "challenge", "badge", "reward",
            "odoo", "dashboard", "report", "score", "emission", "department",
        ])
        asks_general = any(term in lowered for term in ["who is", "what is", "where is", "when is", "write", "make", "code", "calculate"])
        return asks_general and not has_domain_term

    def _department_from_text(self, text):
        Department = self.env["esg.department"].sudo()
        lowered = text.lower()
        for department in Department.search([], order="name desc"):
            names = [department.name or "", department.code or ""]
            if any(name and name.lower() in lowered for name in names):
                return department
        for match in re.finditer(r"department\s+([A-Za-z0-9][A-Za-z0-9 &_-]{1,60})", text, re.I):
            candidate = match.group(1).strip(" ?.,!")
            department = Department.search(["|", ("name", "=ilike", candidate), ("code", "=ilike", candidate)], limit=1)
            if department:
                return department
        return Department.browse()

    def _period_from_text(self, lowered):
        today = fields.Date.context_today(self.env.user)
        quarter = ((today.month - 1) // 3) + 1
        start_month = 3 * (quarter - 1) + 1
        quarter_start = today.replace(month=start_month, day=1)
        if "last quarter" in lowered or "previous quarter" in lowered:
            end = quarter_start - timedelta(days=1)
            prior_quarter = ((end.month - 1) // 3) + 1
            prior_start = end.replace(month=3 * (prior_quarter - 1) + 1, day=1)
            return {"start": str(prior_start), "end": str(end), "label": "Q%s %s" % (prior_quarter, end.year)}
        if "last 90" in lowered or "past 90" in lowered:
            start = today - timedelta(days=90)
            return {"start": str(start), "end": str(today), "label": "last 90 days"}
        return {"start": str(quarter_start), "end": str(today), "label": "Q%s %s" % (quarter, today.year)}

    def _metric_from_text(self, lowered):
        if "environment" in lowered or "carbon score" in lowered:
            return "environmental"
        if "social" in lowered:
            return "social"
        if "governance" in lowered:
            return "governance"
        if "total" in lowered or "overall" in lowered:
            return "total"
        return None


class EcoSphereQueryTools:
    def __init__(self, env, caller):
        self.env = env
        self.caller = caller

    def get_department_score(self, department_id, period):
        department_id = self.caller.enforce_department(department_id)
        if not department_id:
            return {"records": [], "record_ids": [], "message": "No scoped department is available."}
        Score = self.env["esg.department.score"].sudo()
        Score.action_recalculate_all()
        start, end = self._range(period)
        domain = [("department_id", "=", department_id), ("score_date", ">=", start), ("score_date", "<=", end)]
        score = Score.search(domain, order="score_date desc, id desc", limit=1)
        if not score:
            score = Score.search([("department_id", "=", department_id), ("score_date", "<=", end)], order="score_date desc, id desc", limit=1)
        if not score:
            return {"records": [], "record_ids": [], "period": period}
        return {
            "records": [{
                "id": score.id,
                "department_id": score.department_id.id,
                "department": score.department_id.name,
                "period": period.get("label"),
                "score_date": str(score.score_date),
                "environmental": round(score.environmental_score, 1),
                "social": round(score.social_score, 1),
                "governance": round(score.governance_score, 1),
                "total": round(score.total_score, 1),
            }],
            "record_ids": [score.id],
            "period": period,
        }

    def get_carbon_transactions(self, department_id, date_range):
        department_id = self.caller.enforce_department(department_id)
        if not department_id:
            return {"records": [], "record_ids": [], "total_kgCO2e": 0.0}
        start, end = self._range(date_range)
        rows = self.env["esg.carbon.transaction"].sudo().search([
            ("department_id", "child_of", [department_id]),
            ("transaction_date", ">=", start),
            ("transaction_date", "<=", end),
        ], order="transaction_date desc, id desc", limit=50)
        records = [{
            "id": row.id,
            "source": row.source_reference or row.display_name,
            "kgCO2e": round(row.co2e_kg, 2),
            "date": str(row.transaction_date),
            "department": row.department_id.name,
        } for row in rows]
        return {"records": records, "record_ids": rows.ids, "transaction_count": len(records), "total_kgCO2e": round(sum(row.co2e_kg for row in rows), 2), "period": date_range}

    def get_compliance_issues(self, department_id, status=None, overdue_only=False):
        department_id = self.caller.enforce_department(department_id)
        if not department_id:
            return {"records": [], "record_ids": []}
        domain = [("department_id", "child_of", [department_id])]
        if status:
            domain.append(("state", "=", status))
        if overdue_only:
            domain.append(("is_overdue", "=", True))
        rows = self.env["esg.compliance.issue"].sudo().search(domain, order="is_overdue desc, due_date asc, id desc", limit=50)
        records = [{
            "id": row.id,
            "name": row.name,
            "severity": row.severity,
            "owner": row.owner_id.name,
            "due_date": str(row.due_date),
            "status": row.state,
            "overdue": bool(row.is_overdue),
            "department": row.department_id.name,
        } for row in rows]
        return {"records": records, "record_ids": rows.ids, "issue_count": len(records), "overdue_count": len([row for row in rows if row.is_overdue and row.state == "open"])}

    def get_employee_participation(self, employee_id):
        employee_id = int(employee_id or 0)
        if not self.caller.is_admin and employee_id != self.caller.employee_id:
            raise AccessError("You can only query your own employee participation.")
        rows = self.env["esg.csr.participation"].sudo().search([("employee_id", "=", employee_id)])
        approved = rows.filtered(lambda row: row.state == "approved")
        pending = rows.filtered(lambda row: row.state in {"draft", "submitted"})
        return {
            "records": [{
                "employee_id": employee_id,
                "employee": rows[:1].employee_id.name if rows else self.env["hr.employee"].sudo().browse(employee_id).display_name,
                "activities_completed": len(approved),
                "points_earned": int(sum(approved.mapped("points_earned"))),
                "pending_approval": len(pending),
            }],
            "record_ids": rows.ids,
        }

    def get_challenge_status(self, employee_id=None, challenge_id=None):
        employee_id = int(employee_id or self.caller.employee_id or 0)
        if employee_id and not self.caller.is_admin and employee_id != self.caller.employee_id:
            raise AccessError("You can only query your own challenge progress.")
        domain = []
        if employee_id:
            domain.append(("employee_id", "=", employee_id))
        if challenge_id:
            domain.append(("challenge_id", "=", int(challenge_id)))
        rows = self.env["esg.challenge.participation"].sudo().search(domain, order="create_date desc, id desc", limit=20)
        records = [{
            "id": row.id,
            "title": row.challenge_id.name,
            "progress": round(row.progress, 1),
            "xp_awarded": int(row.xp_awarded),
            "status": row.state,
        } for row in rows]
        return {"records": records, "record_ids": rows.ids, "challenge_count": len(records), "total_xp": int(sum(rows.mapped("xp_awarded")))}

    def get_org_esg_summary(self, period):
        Score = self.env["esg.department.score"].sudo()
        Score.action_recalculate_all()
        ids = self.caller.accessible_department_ids()
        if not ids:
            return {"records": [], "record_ids": []}
        latest = {}
        for score in Score.search([("department_id", "child_of", ids)], order="score_date desc, id desc"):
            latest.setdefault(score.department_id.id, score)
        rows = list(latest.values())
        average = lambda name: round(sum(getattr(row, name) for row in rows) / len(rows), 1) if rows else 0.0
        record = {
            "environmental_score": average("environmental_score"),
            "social_score": average("social_score"),
            "governance_score": average("governance_score"),
            "total_score": average("total_score"),
            "department_count": len(rows),
            "period": period.get("label"),
        }
        return {"records": [record] if rows else [], "record_ids": [row.id for row in rows], "period": period}

    def _range(self, value):
        value = value or {}
        return fields.Date.to_date(value.get("start")), fields.Date.to_date(value.get("end"))


class ExecutorAgent:
    system_prompt = "Execute exactly the Router-selected typed tools against Odoo ORM, with RBAC re-checks and no free-form SQL."

    def __init__(self, env):
        self.env = env

    def execute(self, router_output, caller):
        tools = EcoSphereQueryTools(self.env, caller)
        results = []
        errors = []
        for tool_name in router_output.get("candidate_tools", []):
            try:
                arguments = self._arguments_for(tool_name, router_output.get("filters") or {})
                raw_result = getattr(tools, tool_name)(**arguments)
                results.append({"tool": tool_name, "arguments": arguments, "raw_result": raw_result})
            except Exception as error:
                errors.append({"tool": tool_name, "message": str(error)})
        return {"tool_calls": results, "errors": errors}

    def _arguments_for(self, tool_name, filters):
        if tool_name == "get_department_score":
            return {"department_id": filters.get("department_id"), "period": filters.get("period")}
        if tool_name == "get_carbon_transactions":
            return {"department_id": filters.get("department_id"), "date_range": filters.get("date_range")}
        if tool_name == "get_compliance_issues":
            return {"department_id": filters.get("department_id"), "status": filters.get("status"), "overdue_only": bool(filters.get("overdue_only"))}
        if tool_name == "get_employee_participation":
            return {"employee_id": filters.get("employee_id")}
        if tool_name == "get_challenge_status":
            return {"employee_id": filters.get("employee_id"), "challenge_id": filters.get("challenge_id")}
        if tool_name == "get_org_esg_summary":
            return {"period": filters.get("period")}
        raise ValidationError("Unknown EcoSphere AI tool: %s" % tool_name)


class ResponderAgent:
    system_prompt = "Format only verified EcoSphere data into a concise answer with source citations; never touch the database."

    def __init__(self, llm=None):
        self.llm = llm

    def draft(self, router_output, executor_output):
        if router_output.get("needs_clarification"):
            return {"answer": router_output.get("clarifying_question"), "claims": [], "citations": [], "source": {}}
        if router_output.get("intent") == "out_of_scope":
            return {
                "answer": "I can only answer questions about EcoSphere, ESG records, carbon, CSR, compliance, reports, scoring, policies, challenges, badges, rewards, and this Odoo workspace.",
                "claims": [],
                "citations": [],
                "source": {"type": "domain_boundary"},
            }
        if router_output.get("intent") == "project_context":
            return self._project_context_answer(router_output)
        if executor_output.get("errors"):
            return {"answer": "I could not complete the data lookup: %s" % executor_output["errors"][0]["message"], "claims": [], "citations": [], "source": {}}
        if not executor_output.get("tool_calls"):
            return {"answer": "I could not map that question to a supported EcoSphere data tool.", "claims": [], "citations": [], "source": {}}
        call = executor_output["tool_calls"][0]
        deterministic = self._answer_for_call(call)
        return self._maybe_groq_answer(router_output, call, deterministic)

    def final(self, router_output, executor_output, validation):
        if router_output.get("needs_clarification"):
            return self.draft(router_output, executor_output)
        if validation.get("verified"):
            return self.draft(router_output, executor_output)
        fallback = "I could not confirm every number in that answer. "
        call = (executor_output.get("tool_calls") or [{}])[0]
        raw = call.get("raw_result") or {}
        if raw.get("records"):
            fallback += "Here is the verified source data I can cite: %s." % self._compact_records(raw["records"])
        else:
            fallback += "The data does not support a numeric answer for this question."
        return {"answer": fallback, "claims": [], "citations": self._citations(call), "source": self._source(call)}

    def _maybe_groq_answer(self, router_output, call, deterministic):
        if not self.llm or not self.llm.available() or not deterministic.get("claims"):
            return deterministic
        try:
            prompt = {
                "question_intent": router_output.get("intent"),
                "verified_raw_result": call.get("raw_result"),
                "required_citations": deterministic.get("citations"),
                "baseline_answer": deterministic.get("answer"),
                "rules": [
                    "Do not introduce any number that is absent from verified_raw_result.",
                    "Mention the source record/table and period when present.",
                    "If data is empty, say no data was found.",
                    "Keep the answer under 90 words.",
                    "Use plain text only, no Markdown.",
                    "Do not add bracket citations like [1]; citations are rendered separately by the UI.",
                ],
            }
            answer = self.llm.complete_text(self.system_prompt, json.dumps(prompt, default=str), max_tokens=300)
            if answer:
                answer = self._plain_text(answer)
                missing = [claim for claim in deterministic.get("claims", []) if not self._answer_mentions_value(answer, claim.get("value"))]
                if missing:
                    updated = deepcopy(deterministic)
                    updated["llm_error"] = "Groq answer omitted verified claim values: %s" % ", ".join(str(claim.get("label")) for claim in missing)
                    return updated
                updated = deepcopy(deterministic)
                updated["answer"] = answer
                updated["llm_provider"] = "groq"
                return updated
        except Exception as error:
            updated = deepcopy(deterministic)
            updated["llm_error"] = str(error)
            return updated
        return deterministic

    def _project_context_answer(self, router_output):
        question = router_output.get("question") or ""
        fallback = self._project_context_fallback(question)
        if not self.llm or not self.llm.available():
            return fallback
        try:
            answer = self.llm.complete_text(
                (
                    "You are EcoSphere AI inside the EcoSphere ESG management platform. "
                    "Answer only from the provided EcoSphere project context. "
                    "Do not answer unrelated general knowledge. Keep it concise and product-specific. "
                    "Use plain text only, no Markdown."
                ),
                json.dumps({"question": question, "project_context": PROJECT_CONTEXT}, default=str),
                max_tokens=350,
            )
            if answer:
                fallback["answer"] = self._plain_text(answer)
                fallback["llm_provider"] = "groq"
        except Exception as error:
            fallback["llm_error"] = str(error)
        return fallback

    def _project_context_fallback(self, question):
        lowered = (question or "").lower()
        if "meaning" in lowered or "mean" in lowered or "what is esg" in lowered or "what does esg" in lowered:
            answer = PROJECT_CONTEXT["esg_meaning"]
        elif "module" in lowered or "feature" in lowered or "built" in lowered:
            answer = "EcoSphere includes: %s" % " ".join(PROJECT_CONTEXT["built_modules"])
        else:
            answer = PROJECT_CONTEXT["purpose"]
        return {
            "answer": answer,
            "claims": [],
            "citations": [{"type": "project_context", "id": "ecosphere", "label": "EcoSphere project context", "note": "PRD and implemented modules"}],
            "source": {"type": "project_context", "record_ids": []},
        }

    def _answer_mentions_value(self, answer, value):
        if not isinstance(value, (int, float)):
            return True
        normalized = str(float(value)).rstrip("0").rstrip(".")
        variants = {str(value), str(float(value)), normalized}
        return any(variant and variant in answer for variant in variants)

    def _plain_text(self, answer):
        text = re.sub(r"[*_`#]+", "", answer or "")
        text = re.sub(r"\s*\n\s*[-•]\s*", "\n", text)
        return re.sub(r"[ \t]+", " ", text).strip()

    def _answer_for_call(self, call):
        tool = call["tool"]
        raw = call["raw_result"]
        records = raw.get("records") or []
        if not records:
            return {"answer": "No EcoSphere records were found for that scoped question.", "claims": [], "citations": [], "source": self._source(call)}
        if tool == "get_department_score":
            row = records[0]
            answer = (
                "%(department)s's ESG score for %(period)s is %(total)s/100 "
                "(Environmental %(environmental)s, Social %(social)s, Governance %(governance)s), "
                "from Department Score record %(id)s dated %(date)s."
            ) % {"department": row["department"], "period": row["period"], "total": row["total"], "environmental": row["environmental"], "social": row["social"], "governance": row["governance"], "id": row["id"], "date": row["score_date"]}
            claims = self._claims(row, ["total", "environmental", "social", "governance"])
        elif tool == "get_carbon_transactions":
            answer = "%s carbon transaction(s) total %s kg CO2e for %s. Latest records: %s." % (len(records), raw["total_kgCO2e"], raw.get("period", {}).get("label", "the selected period"), self._compact_records(records[:3]))
            claims = [{"label": "total_kgCO2e", "value": raw["total_kgCO2e"]}, {"label": "transaction_count", "value": len(records)}]
        elif tool == "get_compliance_issues":
            answer = "I found %s compliance issue(s), including %s overdue open issue(s). Records: %s." % (len(records), raw.get("overdue_count", 0), self._compact_records(records[:5]))
            claims = [{"label": "issue_count", "value": len(records)}, {"label": "overdue_count", "value": raw.get("overdue_count", 0)}]
        elif tool == "get_employee_participation":
            row = records[0]
            answer = "%(employee)s has %(activities_completed)s approved CSR activity record(s), %(points_earned)s points earned, and %(pending_approval)s participation(s) pending approval." % row
            claims = self._claims(row, ["activities_completed", "points_earned", "pending_approval"])
        elif tool == "get_challenge_status":
            answer = "I found %s challenge participation record(s) with %s total XP awarded. Records: %s." % (len(records), raw.get("total_xp", 0), self._compact_records(records[:5]))
            claims = [{"label": "challenge_count", "value": len(records)}, {"label": "total_xp", "value": raw.get("total_xp", 0)}]
        else:
            row = records[0]
            answer = "ESG summary for %(period)s across %(department_count)s department score record(s): total %(total_score)s/100, Environmental %(environmental_score)s, Social %(social_score)s, Governance %(governance_score)s." % row
            claims = self._claims(row, ["department_count", "total_score", "environmental_score", "social_score", "governance_score"])
        return {"answer": answer, "claims": claims, "citations": self._citations(call), "source": self._source(call)}

    def _claims(self, row, keys):
        return [{"label": key, "value": row[key]} for key in keys]

    def _citations(self, call):
        raw = call.get("raw_result") or {}
        return [{"type": call.get("tool"), "id": record_id, "label": "%s record %s" % (call.get("tool"), record_id), "note": "Arguments: %s" % call.get("arguments")} for record_id in raw.get("record_ids", [])[:5]]

    def _source(self, call):
        raw = call.get("raw_result") or {}
        return {"tool": call.get("tool"), "arguments": call.get("arguments"), "record_ids": raw.get("record_ids", [])}

    def _compact_records(self, records):
        pieces = []
        for row in records:
            if "name" in row:
                pieces.append("%s (%s)" % (row["name"], row.get("due_date") or row.get("status") or row.get("id")))
            elif "source" in row:
                pieces.append("%s: %s kg CO2e on %s" % (row["source"], row["kgCO2e"], row["date"]))
            elif "title" in row:
                pieces.append("%s: %s, %s XP" % (row["title"], row["status"], row["xp_awarded"]))
            else:
                pieces.append(str(row))
        return "; ".join(pieces)


class ValidatorAgent:
    system_prompt = "Independently verify every numeric draft claim against raw tool output and reject unsupported numbers."

    def validate(self, executor_output, draft):
        values = []
        for call in executor_output.get("tool_calls", []):
            values.extend(self._numeric_values(call.get("raw_result")))
        issues = []
        for claim in draft.get("claims", []):
            value = claim.get("value")
            if isinstance(value, (int, float)) and not self._contains_number(values, value):
                issues.append("Unsupported numeric claim %s=%s" % (claim.get("label"), value))
        for value in self._numeric_values(draft.get("answer")):
            if value == 100.0:
                continue
            if not self._contains_number(values, value):
                issues.append("Unsupported numeric answer value %s" % value)
        return {"verified": not issues, "corrected_answer": None if not issues else "", "issues": issues}

    def _numeric_values(self, value):
        if isinstance(value, bool) or value is None:
            return []
        if isinstance(value, (int, float)):
            return [float(value)]
        if isinstance(value, str):
            scrubbed = re.sub(r"\b\d{4}[-\u2011\u2010\u2012\u2013\u2014]\d{1,2}[-\u2011\u2010\u2012\u2013\u2014]\d{1,2}\b", " ", value)
            scrubbed = re.sub(r"\bQ[1-4]\s+\d{4}\b", " ", scrubbed, flags=re.I)
            return [float(match) for match in re.findall(r"(?<![A-Za-z])-?\d+(?:\.\d+)?", scrubbed)]
        if isinstance(value, dict):
            values = []
            for item in value.values():
                values.extend(self._numeric_values(item))
            return values
        if isinstance(value, (list, tuple)):
            values = []
            for item in value:
                values.extend(self._numeric_values(item))
            return values
        return []

    def _contains_number(self, values, expected):
        expected = float(expected)
        return any(abs(value - expected) <= 0.01 for value in values)


class EcoSphereAIQueryPipeline:
    def __init__(self, env, use_llm=True):
        self.env = env
        self.llm = GroqLLMClient(env) if use_llm else None
        self.router = RouterAgent(env, llm=self.llm)
        self.executor = ExecutorAgent(env)
        self.responder = ResponderAgent(llm=self.llm)
        self.validator = ValidatorAgent()

    def run(self, question, conversation_id=None, role=None, department_id=None, employee_id=None, history=None):
        caller = CallerContext(self.env, role=role, department_id=department_id, employee_id=employee_id)
        trace = []
        router_output = self.router.route(question, history or {}, caller)
        router_output["question"] = question
        trace.append({"agent": "router", "decision": router_output})
        if router_output.get("needs_clarification") or router_output.get("intent") in {"project_context", "out_of_scope"}:
            draft = self.responder.draft(router_output, {"tool_calls": [], "errors": []})
            trace.append({"agent": "responder", "decision": {
                "mode": router_output.get("intent"),
                "llm_provider": draft.get("llm_provider"),
                "llm_error": draft.get("llm_error"),
            }})
            return self._payload(draft, trace, conversation_id, router_output, {"tool_calls": [], "errors": []}, {"verified": True})
        executor_output = self.executor.execute(router_output, caller)
        trace.append({"agent": "executor", "decision": {"tool_calls": [{"tool": call["tool"], "arguments": call["arguments"]} for call in executor_output.get("tool_calls", [])], "errors": executor_output.get("errors", [])}})
        draft = self.responder.draft(router_output, executor_output)
        trace.append({"agent": "responder", "decision": {
            "draft_claims": draft.get("claims", []),
            "llm_provider": draft.get("llm_provider"),
            "llm_error": draft.get("llm_error"),
        }})
        validation = self.validator.validate(executor_output, draft)
        trace.append({"agent": "validator", "decision": validation})
        final = draft if validation.get("verified") else self.responder.final(router_output, executor_output, validation)
        trace.append({"agent": "responder", "decision": "final"})
        return self._payload(final, trace, conversation_id, router_output, executor_output, validation)

    def _payload(self, response, trace, conversation_id, router_output, executor_output, validation):
        first_call = (executor_output.get("tool_calls") or [{}])[0]
        raw_result = first_call.get("raw_result") or {}
        return {
            "answer": response.get("answer"),
            "reply": response.get("answer"),
            "source": response.get("source") or {},
            "citations": response.get("citations") or [],
            "agent_trace": trace,
            "data": raw_result,
            "conversation_id": conversation_id or "local",
            "filters": router_output.get("filters") or {},
            "guardrails": [
                "Router scopes department filters before tools run.",
                "Executor only calls typed Odoo ORM tools.",
                "Validator rejects numeric claims not found in raw tool output.",
            ],
            "verified": bool(validation.get("verified")),
            "llm_provider": "groq" if self.llm and self.llm.available() else "deterministic",
            "llm_status": self._llm_status(trace),
            "suggested_actions": self._suggested_actions(router_output.get("intent")),
        }

    def _llm_status(self, trace):
        if not self.llm or not self.llm.available():
            return {"provider": "deterministic", "used": False, "reason": "GROQ_API_KEY is not configured."}
        errors = []
        used = False
        for row in trace:
            decision = row.get("decision")
            if isinstance(decision, dict):
                if decision.get("llm_provider") == "groq":
                    used = True
                if decision.get("llm_error"):
                    errors.append(decision["llm_error"])
        return {"provider": "groq", "model": self.llm.model, "used": used and not errors, "errors": errors}

    def _suggested_actions(self, intent):
        targets = {
            "department_score": ("Open dashboard", "Overview"),
            "carbon_transactions": ("Open carbon ledger", "Carbon transactions"),
            "compliance_issues": ("Open compliance issues", "Compliance issues"),
            "employee_participation": ("Open Social", "Social"),
            "challenge_status": ("Open challenges", "Challenges"),
            "org_esg_summary": ("Open reports", "Reports"),
            "project_context": ("Open dashboard", "Overview"),
        }
        if intent == "out_of_scope":
            return []
        label, target = targets.get(intent, ("Open dashboard", "Overview"))
        return [{"label": label, "target": target}]
