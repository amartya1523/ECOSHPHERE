const DEFAULT_BASE = import.meta.env.VITE_ODOO_BASE || '/odoo';
const DEFAULT_ODOO_DB = import.meta.env.VITE_ODOO_DB || 'ecosphere_db';

let clientConfigPromise;

class SessionExpiredError extends Error {
  constructor() {
    super('Your session expired. Please sign in again.');
    this.name = 'SessionExpiredError';
  }
}

class NonJsonResponseError extends Error {
  constructor(message, responseText) {
    super(message);
    this.name = 'NonJsonResponseError';
    this.responseText = responseText;
  }
}

function notifySessionExpired() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('ecosphere:session-expired'));
  }
}

async function getClientConfig() {
  if (!clientConfigPromise) {
    clientConfigPromise = fetch('/ecosphere/frontend-config.json', {cache: 'no-store'})
      .then(async (response) => {
        if (!response.ok) return {};
        const text = await response.text();
        return text.trim() ? JSON.parse(text) : {};
      })
      .catch(() => ({}))
      .then((config) => ({
        base: config.odooBase || DEFAULT_BASE,
        db: config.odooDb || DEFAULT_ODOO_DB,
      }));
  }
  return clientConfigPromise;
}

async function readJson(response, fallbackMessage) {
  const text = await response.text();
  if (!text.trim()) {
    throw new Error(`${fallbackMessage} Backend returned an empty response. Make sure Docker/Odoo is running on port 8069.`);
  }
  try {
    return JSON.parse(text);
  } catch {
    if (/<!doctype html|<html[\s>]/i.test(text)) {
      if (/\/web\/login|session expired|odoo\.http\.SessionExpiredException/i.test(text)) {
        notifySessionExpired();
        throw new SessionExpiredError();
      }
      throw new NonJsonResponseError(`${fallbackMessage} The backend returned an HTML page instead of API data. Please refresh and try again.`, text);
    }
    throw new NonJsonResponseError(`${fallbackMessage} Backend did not return valid JSON. Please refresh and try again.`, text);
  }
}

function throwJsonRpcError(body, fallbackMessage) {
  if (body?.error) {
    const message = body.error.data?.message || body.error.message || fallbackMessage;
    if (/session expired/i.test(message) || body.error.data?.name === 'odoo.http.SessionExpiredException') {
      notifySessionExpired();
      throw new SessionExpiredError();
    }
    if (message === 'Access Denied') {
      throw new Error('Incorrect email or password.');
    }
    if (message === 'Database not found.') {
      throw new Error('EcoSphere database is not running. Start Docker/Odoo and use the ecosphere_db database.');
    }
    throw new Error(message);
  }
}

async function fetchJson(url, options, fallbackMessage) {
  const response = await fetch(url, options);
  return {response, body: await readJson(response, fallbackMessage)};
}

export async function signIn(login, password) {
  const {base, db} = await getClientConfig();
  const response = await fetch(`${base}/web/session/authenticate`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {db, login, password}}),
  });
  const body = await readJson(response, 'Could not sign in.');
  throwJsonRpcError(body, 'Incorrect email or password.');
  if (!response.ok || !body.result?.uid) throw new Error('Incorrect email or password.');
  return body.result;
}

export async function signUp(name, workspace_name, email, password) {
  const {base} = await getClientConfig();
  const response = await fetch(`${base}/ecosphere/api/signup`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {name, workspace_name, email, password}}),
  });
  const body = await readJson(response, 'Could not create your account.');
  throwJsonRpcError(body, 'Could not create your account.');
  if (!response.ok) throw new Error('Could not create your account.');
  return body.result;
}

export async function getDashboard() {
  const {base} = await getClientConfig();
  const response = await fetch(`${base}/ecosphere/api/dashboard`, {credentials: 'include'});
  const body = await readJson(response, 'Could not load live EcoSphere data.');
  if (!response.ok) throw new Error('Could not load live EcoSphere data.');
  return body;
}

async function rpc(path, params = {}) {
  const {base} = await getClientConfig();
  const options = {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params}),
  };
  let response;
  let body;
  try {
    ({response, body} = await fetchJson(`${base}${path}`, options, 'The EcoSphere service could not complete that request.'));
  } catch (error) {
    if (!(error instanceof NonJsonResponseError) || base === '' || base === '/') {
      throw error;
    }
    ({response, body} = await fetchJson(path, options, 'The EcoSphere service could not complete that request.'));
  }
  throwJsonRpcError(body, 'The EcoSphere service could not complete that request.');
  if (!response.ok) throw new Error('The EcoSphere service could not complete that request.');
  return body.result;
}

export const getResource = (slug, query) => rpc(`/ecosphere/api/resources/${slug}`, {query});
export const getRelationOptions = (slug, field, query) => rpc(`/ecosphere/api/resources/${slug}/options/${field}`, {query});
export const createResource = (slug, values) => rpc(`/ecosphere/api/resources/${slug}/create`, {values});
export const updateResource = (slug, id, values) => rpc(`/ecosphere/api/resources/${slug}/${id}/update`, {values});
export const deleteResource = (slug, id) => rpc(`/ecosphere/api/resources/${slug}/${id}/delete`);
export const runPolicyAction = (id, action) => rpc(`/ecosphere/api/policies/${id}/${action}`);
export const acknowledgePolicy = id => rpc(`/ecosphere/api/policy-acknowledgements/${id}/acknowledge`);
export const getPolicyWorkspace = filters => rpc('/ecosphere/api/policy-workspace', filters || {});
export const remindPolicyAcknowledgements = filters => rpc('/ecosphere/api/policy-acknowledgements/remind', filters || {});
export const exportPolicyAcknowledgements = filters => rpc('/ecosphere/api/policy-acknowledgements/export', filters || {});
export const getAuditWorkspace = filters => rpc('/ecosphere/api/audit-workspace', filters || {});
export const createAudit = values => rpc('/ecosphere/api/audits/create', {values});
export const updateAudit = (id, values) => rpc(`/ecosphere/api/audits/${id}/update`, {values});
export const runAuditAction = (id, action) => rpc(`/ecosphere/api/audits/${id}/${action}`);
export const createComplianceIssue = values => rpc('/ecosphere/api/compliance-issues/create', {values});
export const updateComplianceIssue = (id, values) => rpc(`/ecosphere/api/compliance-issues/${id}/update`, {values});
export const runComplianceIssueAction = (id, action) => rpc(`/ecosphere/api/compliance-issues/${id}/${action}`);
export const exportAuditWorkspace = filters => rpc('/ecosphere/api/audit-workspace/export', filters || {});
export const askEcoSphereAI = (question, conversation_id) => rpc('/ecosphere/api/ai/query', {question, conversation_id});
export const getTeam = () => rpc('/ecosphere/api/team');
export const createTeamMember = (name, email, password, department_id) => rpc('/ecosphere/api/team/create', {name, email, password, department_id});
export const getSettings = () => rpc('/ecosphere/api/settings');
export const saveProfileSettings = values => rpc('/ecosphere/api/settings/profile', values);
export const saveWorkspaceSettings = (name, configuration) => rpc('/ecosphere/api/settings/workspace', {name, configuration});
export const saveDepartment = values => rpc('/ecosphere/api/settings/departments/save', values);
export const archiveDepartment = id => rpc(`/ecosphere/api/settings/departments/${id}/archive`);
export const getGamification = () => rpc('/ecosphere/api/gamification');
export const createChallenge = (values) => rpc('/ecosphere/api/gamification/challenges/create', values);
export const joinChallenge = (id) => rpc(`/ecosphere/api/gamification/challenges/${id}/join`);
export const publishChallengeTemplate = (id, values) => rpc(`/ecosphere/api/gamification/templates/${id}/publish`, values);
export const playChallenge = (id, payload) => rpc(`/ecosphere/api/gamification/participations/${id}/play`, {payload});
export const reviewChallenge = (id, approved, note) => rpc(`/ecosphere/api/gamification/participations/${id}/review`, {approved, note});
export const getSocial = () => rpc('/ecosphere/api/social');
export const createSocialActivity = values => rpc('/ecosphere/api/social/activities/create', values);
export const updateSocialActivity = (id, values) => rpc(`/ecosphere/api/social/activities/${id}/update`, {values});
export const archiveSocialActivity = id => rpc(`/ecosphere/api/social/activities/${id}/archive`);
export const joinSocialActivity = id => rpc(`/ecosphere/api/social/activities/${id}/join`);
export const submitSocialParticipation = (id, proof, filename) => rpc(`/ecosphere/api/social/participations/${id}/submit`, {proof, filename});
export const reviewSocialParticipation = (id, approved, note) => rpc(`/ecosphere/api/social/participations/${id}/review`, {approved, note});
