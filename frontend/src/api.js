const BASE = import.meta.env.VITE_ODOO_BASE || '/odoo';
const ODOO_DB = import.meta.env.VITE_ODOO_DB || 'ecosphere-db';

async function readJson(response, fallbackMessage) {
  const text = await response.text();
  if (!text.trim()) {
    throw new Error(`${fallbackMessage} Backend returned an empty response. Make sure Docker/Odoo is running on port 8069.`);
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${fallbackMessage} Backend did not return JSON. Make sure the Vite proxy is reaching Odoo.`);
  }
}

function throwJsonRpcError(body, fallbackMessage) {
  if (body?.error) {
    const message = body.error.data?.message || body.error.message || fallbackMessage;
    if (message === 'Access Denied') {
      throw new Error('Incorrect email or password.');
    }
    if (message === 'Database not found.') {
      throw new Error('EcoSphere database is not running. Start Docker/Odoo and use the ecosphere-db database.');
    }
    throw new Error(message);
  }
}

export async function signIn(login, password) {
  const response = await fetch(`${BASE}/web/session/authenticate`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {db: ODOO_DB, login, password}}),
  });
  const body = await readJson(response, 'Could not sign in.');
  throwJsonRpcError(body, 'Incorrect email or password.');
  if (!response.ok || !body.result?.uid) throw new Error('Incorrect email or password.');
  return body.result;
}

export async function signUp(name, workspace_name, email, password) {
  const response = await fetch(`${BASE}/ecosphere/api/signup`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {name, workspace_name, email, password}}),
  });
  const body = await readJson(response, 'Could not create your account.');
  throwJsonRpcError(body, 'Could not create your account.');
  if (!response.ok) throw new Error('Could not create your account.');
  return body.result;
}

export async function getDashboard() {
  const response = await fetch(`${BASE}/ecosphere/api/dashboard`, {credentials: 'include'});
  const body = await readJson(response, 'Could not load live EcoSphere data.');
  if (!response.ok) throw new Error('Could not load live EcoSphere data.');
  return body;
}

async function rpc(path, params = {}) {
  const response = await fetch(`${BASE}${path}`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params}),
  });
  const body = await readJson(response, 'The EcoSphere service could not complete that request.');
  throwJsonRpcError(body, 'The EcoSphere service could not complete that request.');
  if (!response.ok) throw new Error('The EcoSphere service could not complete that request.');
  return body.result;
}

export const getResource = (slug, query) => rpc(`/ecosphere/api/resources/${slug}`, {query});
export const getRelationOptions = (slug, field, query) => rpc(`/ecosphere/api/resources/${slug}/options/${field}`, {query});
export const createResource = (slug, values) => rpc(`/ecosphere/api/resources/${slug}/create`, {values});
export const updateResource = (slug, id, values) => rpc(`/ecosphere/api/resources/${slug}/${id}/update`, {values});
export const deleteResource = (slug, id) => rpc(`/ecosphere/api/resources/${slug}/${id}/delete`);
export const getTeam = () => rpc('/ecosphere/api/team');
export const createTeamMember = (name, email, password, department_id) => rpc('/ecosphere/api/team/create', {name, email, password, department_id});
export const getGamification = () => rpc('/ecosphere/api/gamification');
export const createChallenge = (values) => rpc('/ecosphere/api/gamification/challenges/create', values);
export const joinChallenge = (id) => rpc(`/ecosphere/api/gamification/challenges/${id}/join`);
export const publishChallengeTemplate = (id, values) => rpc(`/ecosphere/api/gamification/templates/${id}/publish`, values);
export const playChallenge = (id, payload) => rpc(`/ecosphere/api/gamification/participations/${id}/play`, {payload});
export const reviewChallenge = (id, approved, note) => rpc(`/ecosphere/api/gamification/participations/${id}/review`, {approved, note});
