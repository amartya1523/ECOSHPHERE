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

export async function signUp(name, email, password) {
  const response = await fetch(`${BASE}/ecosphere/api/signup`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {name, email, password}}),
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
