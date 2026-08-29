const BASE = '/odoo';

export async function signIn(login, password) {
  const response = await fetch(`${BASE}/web/session/authenticate`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {db: 'ecosphere_db', login, password}}),
  });
  const body = await response.json();
  if (!response.ok || body.error || !body.result?.uid) throw new Error(body.error?.data?.message || 'Incorrect email or password.');
  return body.result;
}

export async function signUp(name, workspace_name, email, password) {
  const response = await fetch(`${BASE}/ecosphere/api/signup`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {name, workspace_name, email, password}}),
  });
  const body = await response.json();
  if (!response.ok || body.error) throw new Error(body.error?.data?.message || 'Could not create your account.');
  return body.result;
}

export async function getDashboard() {
  const response = await fetch(`${BASE}/ecosphere/api/dashboard`, {credentials: 'include'});
  if (!response.ok) throw new Error('Could not load live EcoSphere data.');
  return response.json();
}

async function rpc(path, params = {}) {
  const response = await fetch(`${BASE}${path}`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params}),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || body.error) throw new Error(body.error?.data?.message || body.error?.message || 'The EcoSphere service could not complete that request.');
  return body.result;
}

export const getResource = (slug, query) => rpc(`/ecosphere/api/resources/${slug}`, {query});
export const getRelationOptions = (slug, field, query) => rpc(`/ecosphere/api/resources/${slug}/options/${field}`, {query});
export const createResource = (slug, values) => rpc(`/ecosphere/api/resources/${slug}/create`, {values});
export const updateResource = (slug, id, values) => rpc(`/ecosphere/api/resources/${slug}/${id}/update`, {values});
export const deleteResource = (slug, id) => rpc(`/ecosphere/api/resources/${slug}/${id}/delete`);
export const getTeam = () => rpc('/ecosphere/api/team');
export const createTeamMember = (name, email, password, department_id) => rpc('/ecosphere/api/team/create', {name, email, password, department_id});
