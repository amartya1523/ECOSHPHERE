import { useEffect, useRef, useState } from 'react';
import LandingPage from './LandingPage';
import { acknowledgePolicy, archiveDepartment, archiveSocialActivity, askEcoSphereAI, createAudit, createChallenge, createComplianceIssue, createResource, createSocialActivity, createTeamMember, deleteResource, exportAuditWorkspace, exportPolicyAcknowledgements, getAuditWorkspace, getDashboard, getGamification, getPolicyWorkspace, getRelationOptions, getResource, getSettings, getSocial, getTeam, joinChallenge, joinSocialActivity, playChallenge, publishChallengeTemplate, remindPolicyAcknowledgements, reviewChallenge, reviewSocialParticipation, runAuditAction, runComplianceIssueAction, runPolicyAction, saveDepartment, saveProfileSettings, saveWorkspaceSettings, signIn, signUp, submitSocialParticipation, updateAudit, updateComplianceIssue, updateResource, updateSocialActivity } from './api';
import { AnimatePresence, motion, useScroll, useSpring, useTransform } from 'framer-motion';
import {
  ArrowUpRight, Bell, Bot, Building2, ChevronDown, ChevronRight, CircleHelp, ClipboardCheck,
  CloudSun, FileBarChart, Gauge, Leaf, LogOut, Menu, MoreHorizontal, Plus, Search,
  SendHorizontal, Settings, ShieldCheck, Sparkles, Trophy, UserPlus, Users, X, Zap
} from 'lucide-react';

const nav = [
  { label: 'Overview', icon: Gauge },
  { label: 'Environmental', icon: Leaf, tone: 'green', children: ['Emission factors', 'Product ESG profiles', 'Carbon transactions', 'Environmental goals'] },
  { label: 'Social', icon: Users, tone: 'blue', children: ['CSR activities', 'Employee participation', 'Diversity dashboard'] },
  { label: 'Governance', icon: Building2, tone: 'violet', children: ['Policies', 'Policy acknowledgements', 'Audits', 'Compliance issues'] },
  { label: 'Gamification', icon: Trophy, tone: 'orange', children: ['Challenges', 'Participation', 'Badges & rewards', 'Leaderboard'] },
  { label: 'Reports', icon: FileBarChart, children: ['Environmental report', 'Social report', 'Governance report', 'ESG summary'] },
];

const modules = {
  Environmental: { slug: 'carbon-transactions', subtitle: 'Your environmental operations, live in the EcoSphere workspace.' },
  'Emission factors': { slug: 'emission-factors', pillar: 'environmental', subtitle: 'Maintain the calculation factors used across your carbon ledger.', stats: ['Active factors', 'Calculation unit', 'Effective dates'] },
  'Product ESG profiles': { slug: 'product-profiles', pillar: 'environmental', subtitle: 'Connect products to their emissions and circularity profile.', stats: ['Product coverage', 'Circularity', 'Linked factors'] },
  'Carbon transactions': { slug: 'carbon-transactions', pillar: 'environmental', subtitle: 'Log verified operational emissions in the central ledger.', stats: ['Ledger entries', 'CO₂e tracked', 'Departments'] },
  'Environmental goals': { slug: 'environmental-goals', pillar: 'environmental', subtitle: 'Set measurable targets and track their progress.', stats: ['Active goals', 'On track', 'Due this quarter'] },
  'CSR activities': { slug: 'csr-activities', pillar: 'social', subtitle: 'Plan social-impact initiatives for your teams.', stats: ['Live initiatives', 'People involved', 'Impact points'] },
  Social: { slug: 'csr-activities', subtitle: 'Your social impact programme, managed in one place.' },
  'Employee participation': { slug: 'employee-participation', subtitle: 'Capture participation and completion evidence.' },
  'Diversity dashboard': { slug: 'diversity-dashboard', subtitle: 'Record workforce diversity indicators by department.' },
  'Policies': { slug: 'policies', pillar: 'governance', subtitle: 'Maintain your current governance policies.', stats: ['Current policies', 'Acknowledgements', 'Review status'] },
  Governance: { slug: 'policies', subtitle: 'Governance records and compliance workflows, in one place.' },
  'Policy acknowledgements': { slug: 'policy-acknowledgements', subtitle: 'Track employee policy acknowledgement status.' },
  'Audits': { slug: 'audits', subtitle: 'Run and close governance audit cycles.' },
  'Compliance issues': { slug: 'compliance-issues', subtitle: 'Raise, assign, and resolve compliance issues.' },
  'Challenges': { slug: 'challenges', pillar: 'gamification', subtitle: 'Create sustainability challenges and manage their lifecycle.', stats: ['Live challenges', 'Participants', 'XP available'] },
  Gamification: { slug: 'challenges', subtitle: 'Motivate sustainable action through challenges and recognition.' },
  'Participation': { slug: 'challenge-participation', subtitle: 'Track challenge progress and approvals.' },
  'Badges & rewards': { slug: 'badges', subtitle: 'Create recognition badges. Use Rewards for redeemable benefits.' },
  'Leaderboard': { slug: 'rewards', subtitle: 'Manage the rewards catalogue used with your recognition programme.' },
  'Settings': { slug: 'departments', subtitle: 'Manage ESG departments. Select Categories to maintain classifications.' },
};

function Mark() { return <div className="mark"><span /><span /><span /></div>; }

function initialsFor(name) {
  return String(name || '').split(' ').map(part => part[0]).join('').slice(0, 2).toUpperCase() || '—';
}

function profileFromSession(session) {
  const name = session?.name || session?.partner_display_name || session?.username || '';
  const companies = session?.user_companies;
  const company = companies?.allowed_companies?.[companies?.current_company];
  if (!name) return null;
  return {
    name,
    email: session?.username || '',
    initials: initialsFor(name),
    role: 'EcoSphere member',
    workspace: company?.name || 'EcoSphere workspace',
  };
}

function Login({ onLogin }) {
  const demoAccounts={admin:{email:'admin@ecosphere.local',password:'Admin@EcoSphere2026',label:'Administrator'},employee:{email:'employee@ecosphere.local',password:'Employee@EcoSphere2026',label:'Employee'}};
  const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [accountKind,setAccountKind]=useState('admin'); const [credentials,setCredentials]=useState(demoAccounts.admin); const [createAdmin,setCreateAdmin]=useState(()=>window.location.pathname === '/signup'); useEffect(()=>{const path=createAdmin?'/signup':'/signin';if(['/signin','/signup'].includes(window.location.pathname)&&window.location.pathname!==path)window.history.replaceState({},'',path);},[createAdmin]);
  const selectAccount = (kind) => { setAccountKind(kind); setCredentials(demoAccounts[kind]); setError(''); };
  const submit = async (event) => { event.preventDefault(); setError(''); setLoading(true); try { const session = await signIn(credentials.email, credentials.password); onLogin(profileFromSession(session)); } catch (requestError) { setError(requestError.message); setLoading(false); } };
  const createEnterpriseAdmin = async (event) => { event.preventDefault(); const form = new FormData(event.currentTarget); const name = String(form.get('name') || '').trim(); const workspaceName = String(form.get('workspace_name') || '').trim(); const email = String(form.get('email') || '').trim(); const password = String(form.get('password') || ''); const confirmPassword = String(form.get('confirm_password') || ''); if (password !== confirmPassword) { setError('Passwords do not match.'); return; } setError(''); setLoading(true); try { await signUp(name, workspaceName, email, password); const session = await signIn(email, password); onLogin(profileFromSession(session)); } catch (requestError) { setError(requestError.message); setLoading(false); } };
  return <main className="login-page">
    <div className="aurora aurora-one" /><div className="aurora aurora-two" />
    <motion.header className="login-nav" initial={{ opacity: 0, y: -18 }} animate={{ opacity: 1, y: 0 }} transition={{ type: 'spring', stiffness: 220, damping: 24 }}>
      <div className="brand"><Mark /><span>EcoSphere</span></div><button className="help-link"><CircleHelp size={17}/> Need help?</button>
    </motion.header>
    <motion.section className="login-shell" initial={{ opacity: 0, y: 26, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: .08, type: 'spring', stiffness: 150, damping: 20 }}>
      <div className="login-copy"><div className="eyebrow"><Sparkles size={14}/> ESG intelligence, made human</div><h1>Progress feels better<br/><em>when everyone can see it.</em></h1><p>Bring carbon, culture and compliance into one calm, connected place.</p><div className="login-proof"><div className="avatar-stack"><i>AS</i><i>RP</i><i>MK</i></div><span>Trusted by conscious teams everywhere</span></div></div>
      {createAdmin ? <form className="login-card" onSubmit={createEnterpriseAdmin} noValidate><div className="card-top"><div className="mini-mark"><UserPlus size={18}/></div><div><h2>Create enterprise admin</h2><p>Your new account will be an administrator.</p></div></div><label>Full name<input name="name" placeholder="Your full name" autoComplete="name" minLength="2" required /></label><label>Workspace name<input name="workspace_name" placeholder="e.g. Northstar Co." autoComplete="organization" minLength="2" required /></label><label>Work email<input name="email" type="email" placeholder="you@company.com" autoComplete="email" required /></label><label>Password<input name="password" type="password" placeholder="At least 8 characters" autoComplete="new-password" minLength="8" required /></label><label>Confirm password<input name="confirm_password" type="password" placeholder="Repeat your password" autoComplete="new-password" minLength="8" required /></label>{error && <motion.p className="form-error" role="alert" initial={{opacity:0,y:-5}} animate={{opacity:1,y:0}}>{error}</motion.p>}<button className="primary-btn" disabled={loading}>{loading ? 'Creating administrator…' : <>Create enterprise admin <ArrowUpRight size={17}/></>}</button><button type="button" className="auth-switch" onClick={()=>{setCreateAdmin(false);setError('');}}>Already have an account? <strong>Sign in</strong></button><p className="admin-managed"><ShieldCheck size={13}/> Employee accounts can only be created later by an administrator from Team access.</p><div className="secure-note"><ShieldCheck size={12}/> Protected with enterprise-grade security</div></form> : <form className="login-card" onSubmit={submit} noValidate><div className="card-top"><div className="mini-mark"><Leaf size={18}/></div><div><h2>Welcome back</h2><p>Choose your workspace access</p></div></div><div className="account-picker"><button type="button" className={accountKind==='admin'?'selected':''} onClick={()=>selectAccount('admin')}><ShieldCheck size={17}/><span>Admin login<small>Manage enterprise & team</small></span></button><button type="button" className={accountKind==='employee'?'selected':''} onClick={()=>selectAccount('employee')}><Users size={17}/><span>Employee login<small>Access assigned workflows</small></span></button></div><label>Work email<input name="email" type="email" value={credentials.email} onChange={event=>{setAccountKind('custom');setCredentials({...credentials,email:event.target.value});}} placeholder="you@company.com" autoComplete="email" required /></label><label>Password<input name="password" type="password" value={credentials.password} onChange={event=>{setAccountKind('custom');setCredentials({...credentials,password:event.target.value});}} placeholder="Your password" autoComplete="current-password" minLength="8" required /></label>{error && <motion.p className="form-error" role="alert" initial={{opacity:0,y:-5}} animate={{opacity:1,y:0}}>{error}</motion.p>}<button className="primary-btn" disabled={loading}>{loading ? 'Opening workspace…' : <>Continue as {demoAccounts[accountKind]?.label || 'your account'} <ArrowUpRight size={17}/></>}</button>{accountKind !== 'employee' && <button type="button" className="auth-switch" onClick={()=>{setCreateAdmin(true);setError('');}}>New enterprise? <strong>Create new admin</strong></button>}<p className="admin-managed"><ShieldCheck size={13}/> New employee accounts are created by an administrator from Team access.</p><div className="secure-note"><ShieldCheck size={12}/> Protected with enterprise-grade security</div></form>}
    </motion.section>
    <motion.footer className="login-footer" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: .4 }}>© 2026 EcoSphere <span>•</span> Built for better business</motion.footer>
  </main>;
}

function Sidebar({ active, setActive, open, setOpen, collapsed, setCollapsed, user }) {
  const [expanded, setExpanded] = useState('Environmental');
  const initials = user?.initials || initialsFor(user?.name);
  return (
    <aside className={`sidebar ${open ? 'open' : ''} ${collapsed ? 'collapsed' : ''}`}>
      <div className="side-brand">
        {/* Logo — clicking it expands the sidebar when collapsed */}
        <div
          className="brand"
          onClick={() => collapsed && setCollapsed(false)}
          style={collapsed ? { cursor: 'pointer' } : {}}
          title={collapsed ? 'Expand sidebar' : undefined}
        >
          <Mark/>
          <span className="sidebar-text">EcoSphere</span>
        </div>
        {/* Collapse button — only visible when sidebar is expanded */}
        {!collapsed && (
          <div className="side-brand-actions">
            <button
              className="collapse-toggle"
              onClick={() => setCollapsed(true)}
              title="Collapse sidebar"
            >
              <ChevronRight size={16} className="rotate"/>
            </button>
            <button className="close-side" onClick={() => setOpen(false)}><X size={20}/></button>
          </div>
        )}
      </div>
      <div className="workspace">
        <div className="workspace-icon"><Leaf size={15}/></div>
        <div className="sidebar-text"><strong>{user?.workspace || 'EcoSphere workspace'}</strong><span>Connected to Odoo</span></div>
      </div>
      <nav>
        {nav.map(item => (
          <div key={item.label} className="nav-group">
            <button
              className={`nav-item ${active === item.label ? 'active' : ''} ${item.tone || ''}`}
              onClick={() => { setActive(item.label); if (!collapsed) setExpanded(expanded === item.label ? '' : item.label); }}
              title={collapsed ? item.label : undefined}
            >
              <item.icon size={18}/>
              <span className="sidebar-text">{item.label}</span>
              {item.children && !collapsed && <ChevronRight className={expanded === item.label ? 'rotate' : ''} size={15}/>}
            </button>
            <AnimatePresence initial={false}>
              {item.children && expanded === item.label && !collapsed && (
                <motion.div className="nav-children" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: .22 }}>
                  {item.children.map(child => <button key={child} onClick={() => setActive(child)} className={active === child ? 'sub-active' : ''}>{child}</button>)}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </nav>
      <div className="side-bottom">
        {user?.role === 'ESG Manager' && (
          <button className="nav-item" onClick={() => setActive('Team access')} title={collapsed ? 'Team access' : undefined}>
            <Users size={18}/><span className="sidebar-text">Team access</span>
          </button>
        )}
        <button className="nav-item" onClick={() => setActive('Settings')} title={collapsed ? 'Settings' : undefined}>
          <Settings size={18}/><span className="sidebar-text">Settings</span>
        </button>
        <div className="user-mini">
          <div className="profile-photo">{initials}</div>
          <div className="sidebar-text"><strong>{user?.name || 'Loading profile…'}</strong><span>{user?.role || 'EcoSphere member'}</span></div>
          {!collapsed && <MoreHorizontal size={17}/>}
        </div>
      </div>
    </aside>
  );
}

function ScoreCard({ item, index }) { return <motion.article className={`score-card ${item.color}`} initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .08 + index * .07, type: 'spring', stiffness: 180, damping: 21 }}><div className="score-head"><span>{item.label}</span><span className="up">{item.delta} <ArrowUpRight size={13}/></span></div><div className="score-main"><strong>{item.score}</strong><span>/100</span></div><div className="meter"><motion.i initial={{ width: 0 }} animate={{ width: `${item.score}%` }} transition={{ delay: .35 + index * .07, duration: .75, ease: [0.2, 0.8, 0.2, 1] }} /></div></motion.article> }

function TrendCard({ count, onOpen }) { return <section className="panel trend"><div className="panel-title"><div><span className="eyebrow green-text">ENVIRONMENTAL DATA</span><h3>Carbon ledger</h3></div></div><div className="real-metric"><strong>{count}</strong><span>saved carbon transaction{count === 1 ? '' : 's'}</span></div><p className="panel-copy">Add transactions to build your real emissions history. This dashboard will not invent trend data.</p><button className="text-button" onClick={onOpen}>Open carbon ledger <ArrowUpRight size={15}/></button></section> }

function PeopleCard({ counts, onOpen }) { return <section className="panel people"><div className="panel-title"><div><span className="eyebrow blue-text">SOCIAL DATA</span><h3>People & participation</h3></div></div><div className="real-list"><div><span>CSR activities</span><strong>{counts.csr_activities}</strong></div><div><span>Active challenges</span><strong>{counts.active_challenges}</strong></div></div><button className="text-button" onClick={onOpen}>Open social workspace <ArrowUpRight size={15}/></button></section> }

function RankingCard({ ranking }) { return <section className="panel ranking"><div className="panel-title"><div><span className="eyebrow violet-text">ORGANIZATION</span><h3>Department ESG ranking</h3></div></div>{ranking.length ? <div className="rank-list">{ranking.map((row,i)=><div className="rank-row" key={row.name}><span>{String(i+1).padStart(2,'0')}</span><strong>{row.name}</strong><div><i style={{background:'#663fd8',transform:`scaleX(${Math.min(row.score,100)/100})`}}/></div><b>{row.score}</b></div>)}</div> : <div className="panel-empty">No department scores have been calculated yet.</div>}</section> }

function plainText(value) { return String(value || '').replace(/<[^>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim(); }
function valueText(value) { return Array.isArray(value) ? value[1] : value === false || value == null ? '—' : plainText(value) || '—'; }
function labelize(value) { return String(value || '').replace(/_/g, ' '); }
function downloadCsv(result, fallback) { const url=URL.createObjectURL(new Blob([result.csv],{type:'text/csv;charset=utf-8'})); const link=document.createElement('a'); link.href=url; link.download=result.filename||fallback; link.click(); URL.revokeObjectURL(url); }
function readFilePayload(event, setFile, setError) { const selected=event.target.files?.[0]; if(!selected)return; if(selected.size>5*1024*1024){setError('Use a file up to 5 MB.');return;} const reader=new FileReader(); reader.onload=()=>setFile({name:selected.name,data:String(reader.result).split(',')[1]}); reader.readAsDataURL(selected); }
const issueStatuses=[['open','Open'],['under_review','Under Review'],['action_required','Action Required'],['resolved','Resolved'],['rejected','Rejected']];
const governanceTabs = ['Governance', 'Policies', 'Policy acknowledgements', 'Audits', 'Compliance issues'];

function TimelineList({ items }) {
 return <div className="governance-timeline">{(items||[]).map((item,index)=><div key={`${item.label}-${index}`}><b>{item.label}</b><span>{item.date||'No date'}</span><small>{item.detail||''}</small></div>)}</div>;
}

function GovernanceHelpButton() {
 const [open,setOpen]=useState(false);
 const [active,setActive]=useState('');
 useEffect(()=>{const change=event=>{setActive(event.detail);setOpen(false);};window.addEventListener('ecosphere:module-change',change);return()=>window.removeEventListener('ecosphere:module-change',change);},[]);
 if(!governanceTabs.includes(active))return null;
 return <><button className="governance-help-trigger" onClick={()=>setOpen(true)} title="Governance help"><CircleHelp size={18}/><span>Help</span></button>{open&&<div className="modal-scrim"><motion.section className="record-modal governance-help-modal" initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow violet-text">GOVERNANCE HELP</span><h2>What to select</h2></div><button className="icon-btn" onClick={()=>setOpen(false)}><X size={18}/></button></div><div className="help-grid"><article><h3>Policy lifecycle</h3><p><b>Draft</b> while writing. <b>Published</b> when employees can see assignment. <b>Active</b> when acknowledgement should be completed. <b>Archived</b> when replaced by a new version.</p></article><article><h3>Policy assignment</h3><p>Use <b>All employees</b> for company-wide rules, <b>Department</b> for team-specific SOPs, and <b>Specific employee</b> for role-based obligations.</p></article><article><h3>Issue severity</h3><p><b>Critical</b> for legal/safety risk, <b>High</b> for material compliance risk, <b>Medium</b> for process gaps, and <b>Low</b> for minor improvements.</p></article><article><h3>Issue status</h3><p><b>Open</b> is newly raised. <b>Under Review</b> means admin is checking. <b>Action Required</b> means owner must fix. <b>Resolved</b> is closed. <b>Rejected</b> is not valid or not actionable.</p></article><article><h3>Audits</h3><p>Create audits for scheduled governance checks. Convert findings into compliance issues so owners and due dates can be tracked.</p></article><article><h3>Role rules</h3><p>Admins can publish, assign, review, resolve, remind, export, and archive. Employees can acknowledge assigned policies and see only their own raised or assigned issues.</p></article></div><div className="modal-actions"><button className="primary-btn" onClick={()=>setOpen(false)}>Got it</button></div></motion.section></div>}</>;
}

function RecordForm({ slug, fields, record, onClose, onSaved }) {
 const formFields = fields.filter(field => !field.readonly && !['acknowledgement_progress','acknowledged_count','pending_count','acknowledgement_total','policy_version','acknowledged_on','department_id'].includes(field.name));
 const [values, setValues] = useState(() => Object.fromEntries(formFields.map(f => [f.name, record?.[f.name] && Array.isArray(record[f.name]) ? record[f.name][0] : (record?.[f.name] ?? (f.name === 'active' ? true : f.type === 'boolean' ? false : ''))])));
 const [options, setOptions] = useState({}); const [saving, setSaving] = useState(false); const [error, setError] = useState('');
 useEffect(() => { formFields.filter(f => f.type === 'many2one').forEach(async field => { try { const rows = await getRelationOptions(slug, field.name); setOptions(current => ({...current, [field.name]: rows})); } catch (e) { setError(e.message); } }); }, [fields, slug]);
 const submit = async e => { e.preventDefault(); setSaving(true); setError(''); try { if (record) await updateResource(slug, record.id, values); else await createResource(slug, values); onSaved(record ? 'Changes saved.' : 'Record created.'); } catch (e) { setError(e.message); setSaving(false); } };
 return <div className="modal-scrim" role="presentation"><motion.form className="record-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow">{record ? 'EDIT RECORD' : 'NEW RECORD'}</span><h2>{record ? 'Update details' : 'Add to workspace'}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="form-grid">{formFields.map(field => <label key={field.name}>{field.string}{field.required && <b> *</b>}{field.type === 'selection' ? <select required={field.required} value={values[field.name] ?? ''} onChange={e=>setValues({...values,[field.name]:e.target.value})}><option value="">Select…</option>{(field.selection || []).map(([v,l])=><option key={v} value={v}>{l}</option>)}</select> : field.type === 'many2one' ? <select required={field.required} value={values[field.name] ?? ''} onChange={e=>setValues({...values,[field.name]:e.target.value})}><option value="">Select…</option>{(options[field.name] || []).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select> : field.type === 'boolean' ? <span className="check-field"><input type="checkbox" checked={Boolean(values[field.name])} onChange={e=>setValues({...values,[field.name]:e.target.checked})}/><span>Enabled</span></span> : ['text','html'].includes(field.type) ? <textarea required={field.required} value={values[field.name] ?? ''} onChange={e=>setValues({...values,[field.name]:e.target.value})}/> : <input required={field.required} type={field.type === 'date' ? 'date' : ['float','integer','monetary'].includes(field.type) ? 'number' : 'text'} step={field.type === 'float' ? 'any' : undefined} value={values[field.name] ?? ''} onChange={e=>setValues({...values,[field.name]:e.target.value})}/>}</label>)}</div>{error && <p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving ? 'Saving…' : 'Save record'} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function PolicyForm({ policy, data, onClose, onSaved }) {
 const [saving,setSaving]=useState(false),[error,setError]=useState(''),[file,setFile]=useState(null);
 const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);setError('');const values={name:form.get('name'),category_id:form.get('category_id'),version:form.get('version'),effective_date:form.get('effective_date'),review_date:form.get('review_date'),reviewer_id:form.get('reviewer_id'),acknowledgement_required:form.get('acknowledgement_required')==='on',assignment_type:form.get('assignment_type'),assignment_department_id:form.get('assignment_department_id'),assignment_employee_id:form.get('assignment_employee_id'),content:form.get('content'),active:true};if(file){values.document=file.data;values.document_filename=file.name;}try{if(policy)await updateResource('policies',policy.id,values);else await createResource('policies',values);onSaved(policy?'Policy updated.':'Policy created.');}catch(err){setError(err.message);setSaving(false);}};
 return <div className="modal-scrim"><motion.form className="record-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow violet-text">POLICY DETAILS</span><h2>{policy?'Edit policy':'New policy'}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="form-grid"><label>Title *<input name="name" required defaultValue={policy?.name||''}/></label><label>Category<select name="category_id" defaultValue={policy?.category_id||''}><option value="">No category</option>{(data?.categories||[]).map(([id,name])=><option value={id} key={id}>{name}</option>)}</select></label><label>Version *<input name="version" required defaultValue={policy?.version||'v1.0'}/></label><label>Effective Date *<input name="effective_date" type="date" required defaultValue={policy?.effective_date||''}/></label><label>Next Review Date<input name="review_date" type="date" defaultValue={policy?.review_date||''}/></label><label>Reviewer<select name="reviewer_id" defaultValue={policy?.reviewer_id||''}><option value="">Select...</option>{(data?.employees||[]).map(([id,name])=><option value={id} key={id}>{name}</option>)}</select></label><label className="check-field"><input name="acknowledgement_required" type="checkbox" defaultChecked={policy?Boolean(policy.acknowledgement_required):true}/><span>Acknowledgement required</span></label><label>Assignment<select name="assignment_type" defaultValue={policy?.assignment_type||'all'}><option value="all">All Employees</option><option value="department">Department</option><option value="employee">Specific Employee</option></select></label><label>Assigned Department<select name="assignment_department_id" defaultValue={policy?.assignment_department_id||''}><option value="">Select...</option>{(data?.departments||[]).map(([id,name])=><option value={id} key={id}>{name}</option>)}</select></label><label>Assigned Employee<select name="assignment_employee_id" defaultValue={policy?.assignment_employee_id||''}><option value="">Select...</option>{(data?.employees||[]).map(([id,name])=><option value={id} key={id}>{name}</option>)}</select></label><label>Policy Document<input type="file" onChange={event=>readFilePayload(event,setFile,setError)}/><small>{file?.name||policy?.document_filename||'Optional PDF or supporting file'}</small></label><label className="full-form-field">Policy Content *<textarea name="content" required defaultValue={plainText(policy?.content)||''}/></label></div>{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving…':'Save policy'} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function PolicyDetail({ policy, isManager, onClose, onAction, onAcknowledge, onDrilldown }) {
 const myAck=policy.my_acknowledgement;
 return <div className="modal-scrim"><motion.section className="record-modal" initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow violet-text">POLICY DETAIL</span><h2>{policy.name}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="detail-hero"><span className={`workflow-pill ${policy.state}`}>{labelize(policy.state)}</span><span className={`workflow-pill ${policy.review_state}`}>{labelize(policy.review_state)}</span><span className="xp-chip">{policy.version}</span><span className="xp-chip">{policy.acknowledgement_required?'Acknowledgement required':'Optional'}</span></div><div className="detail-grid"><article><span>Category</span><strong>{policy.category||'Uncategorized'}</strong></article><article><span>Effective Date</span><strong>{policy.effective_date||'--'}</strong></article><article><span>Next Review</span><strong>{policy.review_date||'Not scheduled'}</strong></article><article><span>Reviewer</span><strong>{policy.reviewer||'Not assigned'}</strong></article><article><span>Assignment</span><strong>{policy.assignment_summary}</strong></article><article><span>{isManager?'Progress':'My Status'}</span><strong>{isManager?`${policy.acknowledged_count}/${policy.acknowledgement_total} acknowledged`:myAck?labelize(myAck.state):'Not required'}</strong></article></div><div className="detail-rules"><h3>Policy Content</h3><p>{policy.content_text||'No policy content added yet.'}</p>{policy.document_filename&&<p>Attachment: {policy.document_filename}</p>}</div>{isManager?<><div className="detail-rules"><h3>Acknowledgement Progress</h3><p>{policy.acknowledgement_progress}% complete. {policy.pending_count} pending acknowledgement{policy.pending_count===1?'':'s'}.</p><button className="text-button" onClick={()=>onDrilldown(policy)}>View acknowledgements <ArrowUpRight size={15}/></button></div><div className="detail-rules"><h3>Version History</h3>{policy.version_history.map(row=><p key={row.id}>{row.version} · {labelize(row.state)} · effective {row.effective_date||'No date'} · review {row.review_date||'unscheduled'}</p>)}</div><div className="detail-rules"><h3>Timeline</h3><TimelineList items={policy.timeline}/></div></>:<div className="detail-rules"><h3>Acknowledgement</h3>{myAck?.state==='acknowledged'?<p>Acknowledged on: {myAck.acknowledged_on||'recorded'}</p>:policy.acknowledgement_required?<button className="primary-btn" onClick={()=>onAcknowledge(myAck?.id)}>Acknowledge Policy <ArrowUpRight size={16}/></button>:<p>This policy does not require acknowledgement.</p>}</div>}<div className="modal-actions">{isManager&&<><button className="cancel-btn" disabled={policy.state!=='draft'} onClick={()=>onAction(policy,'publish')}>Publish</button><button className="cancel-btn" disabled={!['draft','published','effective'].includes(policy.state)} onClick={()=>onAction(policy,'activate')}>Activate</button><button className="cancel-btn" disabled={policy.state==='archived'} onClick={()=>onAction(policy,'mark_reviewed')}>Mark reviewed</button><button className="cancel-btn" disabled={policy.state==='archived'} onClick={()=>onAction(policy,'remind')}>Remind</button><button className="cancel-btn" disabled={policy.state==='archived'} onClick={()=>onAction(policy,'archive')}>Archive</button></>}<button className="primary-btn" onClick={onClose}>Close</button></div></motion.section></div>;
}

function PolicyWorkspace({ active, onNotify }) {
 const [data,setData]=useState(null);
 const [query,setQuery]=useState('');
 const [status,setStatus]=useState('all');
 const [ack,setAck]=useState(active==='Policy acknowledgements'?'pending':'all');
 const [policyFilter,setPolicyFilter]=useState('');
 const [departmentFilter,setDepartmentFilter]=useState('');
 const [selectedAcks,setSelectedAcks]=useState([]);
 const [modal,setModal]=useState(null);
 const [detail,setDetail]=useState(null);
 const [ackFocus,setAckFocus]=useState(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');
 const showAcknowledgements=active==='Policy acknowledgements';
 const load=async()=>{
  setBusy(true);
  try{
   setData(await getPolicyWorkspace({query,status,acknowledgement:ack,policy_id:policyFilter||undefined,department_id:departmentFilter||undefined}));
   setError('');
  }catch(err){
   setError(err.message);
  }finally{
   setBusy(false);
  }
 };
 useEffect(()=>{load();},[active,status,ack,policyFilter,departmentFilter]);
 useEffect(()=>{setSelectedAcks([]);setAckFocus(null);},[active,status,ack,policyFilter,departmentFilter]);
 const saved=async message=>{setModal(null);await load();onNotify(message);};
 const action=async(policy,name)=>{setBusy(true);try{const result=await runPolicyAction(policy.id,name);setDetail(null);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(false);}};
 const acknowledge=async id=>{if(!id)return;setBusy(true);try{const result=await acknowledgePolicy(id);setDetail(null);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(false);}};
 const remind=async ids=>{
  setBusy(true);
  try{
   const result=await remindPolicyAcknowledgements({
    acknowledgement_ids:ids?.length?ids:undefined,
    policy_id:ids?.length?undefined:(policyFilter||ackFocus?.id||undefined),
    department_id:ids?.length?undefined:(departmentFilter||undefined)
   });
   setSelectedAcks([]);
   await load();
   onNotify(result.message);
  }catch(err){
   setError(err.message);
  }finally{
   setBusy(false);
  }
 };
 const exportRows=async()=>{
  setBusy(true);
  try{
   const localCsv=ack==='overdue'?`Policy,Version,Employee,Department,Status,Acknowledged On\r\n${filteredAckRows.map(row=>[row.policy,row.version,row.employee,row.department||'',row.state,row.acknowledged_on||''].map(value=>`"${String(value).replace(/"/g,'""')}"`).join(',')).join('\r\n')}\r\n`:null;
   const result=localCsv?{filename:'policy-acknowledgements-needs-reminder.csv',csv:localCsv}:await exportPolicyAcknowledgements({policy_id:policyFilter||ackFocus?.id||undefined,department_id:departmentFilter||undefined,state:ack==='acknowledged'?'acknowledged':ack==='pending'?'pending':'all'});
   const url=URL.createObjectURL(new Blob([result.csv],{type:'text/csv;charset=utf-8'}));
   const link=document.createElement('a');
   link.href=url;
   link.download=result.filename||'policy-acknowledgements.csv';
   link.click();
   URL.revokeObjectURL(url);
   onNotify('Acknowledgement export prepared.');
  }catch(err){
   setError(err.message);
  }finally{
   setBusy(false);
  }
 };
 const rows=data?.policies||[],isManager=Boolean(data?.is_manager),metrics=data?.metrics||{};
 const ackRows=rows.flatMap(policy=>(policy.acknowledgements||[]).map(row=>({...row,policy:policy.name,version:policy.version,policy_id:policy.id})));
 const filteredAckRows=(ackFocus?ackRows.filter(row=>row.policy_id===ackFocus.id):ackRows).filter(row=>ack==='overdue'?row.needs_reminder:true);
 const pendingAckRows=filteredAckRows.filter(row=>row.state==='pending');
 const allPendingSelected=pendingAckRows.length>0&&pendingAckRows.every(row=>selectedAcks.includes(row.id));
 const toggleAck=id=>setSelectedAcks(current=>current.includes(id)?current.filter(rowId=>rowId!==id):[...current,id]);
 const toggleAll=()=>setSelectedAcks(allPendingSelected?[]:pendingAckRows.map(row=>row.id));
 return <section className="module-workspace module-governance">
  <div className="module-header">
   <div>
    <span className="eyebrow">GOVERNANCE WORKSPACE</span>
    <h1>{showAcknowledgements?(isManager?'Policy acknowledgements':'My acknowledgements'):(isManager?'Policies':'My policies')}</h1>
    <p>{isManager?'Maintain policies, assignment scope, acknowledgement progress, reminders, and lifecycle status.':'Read assigned policies and complete only your own acknowledgements.'}</p>
   </div>
   {isManager&&!showAcknowledgements&&<button className="primary-btn" onClick={()=>setModal({})}><Plus size={18}/> New Policy</button>}
  </div>
  <section className="module-stat-strip">
   <article><span>{isManager?'Active policies':'Assigned policies'}</span><strong>{isManager?metrics.active:metrics.total}</strong></article>
   <article><span>Pending acknowledgements</span><strong>{metrics.pending||0}</strong></article>
   <article><span>{isManager?'Need reminders':'Acknowledgement rate'}</span><strong>{isManager?metrics.needs_reminder||0:`${metrics.acknowledgement_rate||0}%`}</strong></article>
   {isManager&&<article><span>Reviews due</span><strong>{metrics.review_due||0}</strong></article>}
  </section>
  <div className="table-toolbar">
   <label className="table-search"><Search size={16}/><input value={query} placeholder="Search policies" onChange={event=>setQuery(event.target.value)} onKeyDown={event=>event.key==='Enter'&&load()}/></label>
   {isManager&&showAcknowledgements&&<select value={policyFilter} onChange={event=>setPolicyFilter(event.target.value)}><option value="">All policies</option>{(data?.policy_options||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select>}
   {isManager&&showAcknowledgements&&<select value={departmentFilter} onChange={event=>setDepartmentFilter(event.target.value)}><option value="">All departments</option>{(data?.departments||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select>}
   <button className="soft-btn" onClick={load}>{busy?'Refreshing...':'Refresh'}</button>
  </div>
  <div className="game-tabs">{['all','draft','published','active','archived'].filter(value=>isManager||!['draft','archived'].includes(value)).map(value=><button key={value} className={status===value?'selected':''} onClick={()=>setStatus(value)}>{value==='all'?'All statuses':value}</button>)}</div>
  <div className="game-tabs">{(isManager?['all','required','optional','pending','overdue']:['all','pending','acknowledged','overdue']).map(value=><button key={value} className={ack===value?'selected':''} onClick={()=>setAck(value)}>{value==='all'?'All acknowledgements':value==='overdue'?'Needs reminder':value}</button>)}</div>
  {isManager&&showAcknowledgements&&<div className="row-actions">
   <button disabled={!pendingAckRows.length||busy} onClick={()=>remind(selectedAcks.length?selectedAcks:ack==='overdue'?pendingAckRows.map(row=>row.id):[])}>{selectedAcks.length?`Remind selected (${selectedAcks.length})`:'Remind filtered pending'}</button>
   <button disabled={!filteredAckRows.length||busy} onClick={exportRows}>Export CSV</button>
  </div>}
  {error&&<p className="form-error">{error}</p>}
  {showAcknowledgements&&isManager?<section className="data-surface"><div className="data-table-wrap"><table><thead><tr><th><input type="checkbox" checked={allPendingSelected} disabled={!pendingAckRows.length} onChange={toggleAll}/></th><th>Employee</th><th>Department</th><th>Policy</th><th>Version</th><th>Status</th><th>Date</th><th>Reminder</th><th/></tr></thead><tbody>{filteredAckRows.map(row=><tr key={row.id}><td><input type="checkbox" checked={selectedAcks.includes(row.id)} disabled={row.state!=='pending'} onChange={()=>toggleAck(row.id)}/></td><td>{row.employee}</td><td>{row.department||'--'}</td><td>{row.policy}</td><td>{row.version}</td><td><span className={`workflow-pill ${row.state}`}>{row.state}</span></td><td>{row.acknowledged_on||'--'}</td><td>{row.needs_reminder?'Needs reminder':'--'}</td><td className="row-actions"><button onClick={()=>setDetail(rows.find(policy=>policy.id===row.policy_id))}>View policy</button></td></tr>)}{!filteredAckRows.length&&<tr><td colSpan="9"><div className="empty-state"><ClipboardCheck size={23}/><strong>No acknowledgement records.</strong><span>Records appear when an administrator publishes an acknowledgement-required policy.</span></div></td></tr>}</tbody></table></div></section>:<section className="data-surface"><div className="data-table-wrap"><table><thead>{isManager?<tr><th>Title</th><th>Category</th><th>Version</th><th>Effective Date</th><th>Review</th><th>Acknowledgement</th><th>Progress</th><th>Status</th><th>Assignment</th><th/></tr>:<tr><th>Policy</th><th>Version</th><th>Effective Date</th><th>Status</th><th>My acknowledgement</th><th/></tr>}</thead><tbody>{rows.map(row=><tr key={row.id}>{isManager?<><td>{row.name}</td><td>{row.category||'--'}</td><td>{row.version}</td><td>{row.effective_date||'--'}</td><td><span className={`workflow-pill ${row.review_state}`}>{row.review_date?labelize(row.review_state):'unscheduled'}</span></td><td>{row.acknowledgement_required?'Required':'Optional'}</td><td><button className="text-button" onClick={()=>setAckFocus(row)}>{row.acknowledgement_progress}% · {row.pending_count} pending</button></td><td><span className={`workflow-pill ${row.state}`}>{labelize(row.state)}</span></td><td>{row.assignment_summary}</td><td className="row-actions"><button onClick={()=>setDetail(row)}>View</button><button disabled={row.state==='archived'} onClick={()=>setModal(row)}>Edit</button><button disabled={row.state!=='draft'} onClick={()=>action(row,'publish')}>Publish</button><button disabled={!['draft','published','active'].includes(row.state)} onClick={()=>action(row,'activate')}>Activate</button><button disabled={row.state==='archived'} onClick={()=>action(row,'mark_reviewed')}>Reviewed</button><button disabled={row.state==='archived'} onClick={()=>action(row,'remind')}>Remind</button><button disabled={row.state==='archived'} onClick={()=>action(row,'archive')}>Archive</button></td></>:<><td>{row.name}</td><td>{row.version}</td><td>{row.effective_date||'--'}</td><td><span className={`workflow-pill ${row.state}`}>{labelize(row.state)}</span></td><td>{row.my_acknowledgement?.state==='acknowledged'?`Acknowledged ${row.my_acknowledgement.acknowledged_on||''}`:row.my_acknowledgement?.needs_reminder?'Needs acknowledgement':row.my_acknowledgement?.state||'not required'}</td><td className="row-actions"><button onClick={()=>setDetail(row)}>{row.my_acknowledgement?.state==='pending'?'Read & Acknowledge':'View'}</button></td></>}</tr>)}{!rows.length&&<tr><td colSpan={isManager?10:6}><div className="empty-state"><ClipboardCheck size={23}/><strong>{isManager?'No policies created yet.':'No policies require your acknowledgement.'}</strong><span>{isManager?'Create the first policy when your governance content is ready.':'Assigned policies will appear here when an administrator publishes them.'}</span></div></td></tr>}</tbody></table></div></section>}
  {ackFocus&&!showAcknowledgements&&isManager&&<section className="data-surface review-panel"><div className="panel-title"><div><span className="eyebrow violet-text">PENDING ACKNOWLEDGEMENTS</span><h3>{ackFocus.name}</h3></div><div className="row-actions"><button className="soft-btn" onClick={()=>remind([],ackFocus.id)}>Remind pending</button><button className="soft-btn" onClick={()=>setAckFocus(null)}>Clear</button></div></div><div className="data-table-wrap"><table><thead><tr><th>Employee</th><th>Department</th><th>Status</th><th>Reminder</th><th>Date</th></tr></thead><tbody>{(ackFocus.acknowledgements||[]).filter(row=>row.state==='pending').map(row=><tr key={row.id}><td>{row.employee}</td><td>{row.department||'--'}</td><td><span className={`workflow-pill ${row.state}`}>{row.state}</span></td><td>{row.needs_reminder?'Needs reminder':'--'}</td><td>{row.acknowledged_on||'--'}</td></tr>)}{!(ackFocus.acknowledgements||[]).some(row=>row.state==='pending')&&<tr><td colSpan="5">No pending acknowledgements for this policy.</td></tr>}</tbody></table></div></section>}
  {modal&&<PolicyForm policy={modal.id?modal:null} data={data} onClose={()=>setModal(null)} onSaved={saved}/>}
  {detail&&<PolicyDetail policy={detail} isManager={isManager} onClose={()=>setDetail(null)} onAction={action} onAcknowledge={acknowledge} onDrilldown={policy=>setAckFocus(policy)}/>}
 </section>;
}

function AuditForm({ audit, data, onClose, onSaved }) {
 const [saving,setSaving]=useState(false),[error,setError]=useState(''),[file,setFile]=useState(null);
 const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);setError('');const values={name:form.get('name'),department_id:form.get('department_id'),auditor_id:form.get('auditor_id'),audit_date:form.get('audit_date'),due_date:form.get('due_date'),findings:form.get('findings'),state:form.get('state')||'under_review'};if(file){values.evidence=file.data;values.evidence_filename=file.name;}try{if(audit)await updateAudit(audit.id,values);else await createAudit(values);onSaved(audit?'Audit updated.':'Audit created.');}catch(err){setError(err.message);setSaving(false);}};
 return <div className="modal-scrim"><motion.form className="record-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow violet-text">AUDIT DETAILS</span><h2>{audit?'Edit audit':'New audit'}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="form-grid"><label>Audit title *<input name="name" required defaultValue={audit?.name||''}/></label><label>Department *<select name="department_id" required defaultValue={audit?.department_id||''}><option value="">Select...</option>{(data?.departments||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label><label>Auditor *<select name="auditor_id" required defaultValue={audit?.auditor_id||''}><option value="">Select...</option>{(data?.employees||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label><label>Audit Date *<input name="audit_date" type="date" required defaultValue={audit?.audit_date||''}/></label><label>Target Closure Date<input name="due_date" type="date" defaultValue={audit?.due_date||''}/></label><label>Status<select name="state" defaultValue={audit?.state||'under_review'}><option value="under_review">Under Review</option><option value="completed">Completed</option></select></label><label>Evidence File<input type="file" onChange={event=>readFilePayload(event,setFile,setError)}/><small>{file?.name||audit?.evidence_filename||'Optional audit evidence'}</small></label><label className="full-form-field">Findings<textarea name="findings" defaultValue={audit?.findings_text||audit?.findings||''}/></label></div>{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving...':'Save audit'} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function IssueForm({ issue, audit, data, isManager, onClose, onSaved }) {
 const [saving,setSaving]=useState(false),[error,setError]=useState(''),[file,setFile]=useState(null);
 const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);setError('');const values={name:form.get('name'),audit_id:form.get('audit_id'),department_id:form.get('department_id'),severity:form.get('severity'),owner_id:form.get('owner_id'),due_date:form.get('due_date'),description:form.get('description'),state:form.get('state')||'open',resolution_note:form.get('resolution_note')};if(file){values.evidence=file.data;values.evidence_filename=file.name;}try{if(issue)await updateComplianceIssue(issue.id,values);else await createComplianceIssue(values);onSaved(issue?'Compliance issue updated.':'Compliance issue raised for review.');}catch(err){setError(err.message);setSaving(false);}};
 return <div className="modal-scrim"><motion.form className="record-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow violet-text">COMPLIANCE ISSUE</span><h2>{issue?'Edit issue':'Raise issue'}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="form-grid"><label>Issue title *<input name="name" required defaultValue={issue?.name||''}/></label><label>Audit<select name="audit_id" defaultValue={issue?.audit_id||audit?.id||''}><option value="">No audit link</option>{(data?.audit_options||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label><label>Department{isManager&&' *'}<select name="department_id" required={isManager} defaultValue={issue?.department_id||audit?.department_id||''}><option value="">Use my department</option>{(data?.departments||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label><label>Severity *<select name="severity" required defaultValue={issue?.severity||'medium'}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></label>{isManager&&<label>Owner *<select name="owner_id" required defaultValue={issue?.owner_id||''}><option value="">Select...</option>{(data?.employees||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>}<label>Due Date *<input name="due_date" type="date" required defaultValue={issue?.due_date||''}/></label>{isManager&&<label>Status<select name="state" defaultValue={issue?.state||'open'}>{issueStatuses.map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></label>}<label>Evidence File<input type="file" onChange={event=>readFilePayload(event,setFile,setError)}/><small>{file?.name||issue?.evidence_filename||'Optional evidence'}</small></label><label className="full-form-field">Description *<textarea name="description" required defaultValue={issue?.description_text||issue?.description||''}/></label>{isManager&&<label className="full-form-field">Resolution note<textarea name="resolution_note" defaultValue={issue?.resolution_note||''}/></label>}</div>{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving...':issue?'Save issue':'Raise issue'} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function AuditDetail({ audit, isManager, onClose, onAuditAction, onIssueAction, onIssueEdit, onIssueCreate }) {
 return <div className="modal-scrim"><motion.section className="record-modal" initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow violet-text">AUDIT DETAIL</span><h2>{audit.name}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="detail-hero"><span className={`workflow-pill ${audit.state}`}>{labelize(audit.state)}</span><span className="xp-chip">{audit.department||'No department'}</span><span className="xp-chip">{audit.audit_date||'No date'}</span>{audit.due_date&&<span className="xp-chip">Due {audit.due_date}</span>}</div><div className="detail-grid"><article><span>Auditor</span><strong>{audit.auditor||'Unassigned'}</strong></article><article><span>Open Issues</span><strong>{audit.open_issue_count}</strong></article><article><span>Critical Issues</span><strong>{audit.critical_issue_count}</strong></article><article><span>Overdue</span><strong>{audit.overdue_issue_count}</strong></article></div><div className="detail-rules"><h3>Findings</h3><p>{audit.findings_text||'No findings recorded yet.'}</p>{audit.evidence_filename&&<p>Evidence: {audit.evidence_filename}</p>}</div><div className="detail-rules"><h3>Related Issues</h3>{audit.issues.length?audit.issues.map(issue=><p key={issue.id}>{issue.name} · {issue.severity} · {labelize(issue.state)}{issue.is_overdue?' · overdue':''}</p>):<p>No related compliance issues.</p>}<button className="text-button" onClick={()=>onIssueCreate(audit)}>Raise related issue <ArrowUpRight size={15}/></button></div><div className="detail-rules"><h3>Timeline</h3><TimelineList items={audit.timeline}/></div><div className="modal-actions">{isManager&&<><button className="cancel-btn" disabled={audit.state==='completed'} onClick={()=>onAuditAction(audit,'complete')}>Complete</button><button className="cancel-btn" disabled={audit.state==='under_review'} onClick={()=>onAuditAction(audit,'reopen')}>Reopen</button></>}<button className="primary-btn" onClick={onClose}>Close</button></div></motion.section></div>;
}

function AuditWorkspace({ active, onNotify }) {
 const [data,setData]=useState(null),[query,setQuery]=useState(''),[status,setStatus]=useState('all'),[issueStatus,setIssueStatus]=useState('all'),[severity,setSeverity]=useState('all'),[departmentFilter,setDepartmentFilter]=useState(''),[auditFilter,setAuditFilter]=useState(''),[auditModal,setAuditModal]=useState(null),[issueModal,setIssueModal]=useState(null),[detail,setDetail]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const showIssues=active==='Compliance issues';
 const load=async()=>{setBusy(true);try{setData(await getAuditWorkspace({query,status,issue_status:issueStatus,severity,department_id:departmentFilter||undefined,audit_id:auditFilter||undefined}));setError('');}catch(err){setError(err.message);}finally{setBusy(false);}};
 useEffect(()=>{load();},[active,status,issueStatus,severity,departmentFilter,auditFilter]);
 const done=async message=>{setAuditModal(null);setIssueModal(null);setDetail(null);await load();onNotify(message);};
 const auditAction=async(audit,name)=>{setBusy(true);try{const result=await runAuditAction(audit.id,name);await done(result.message);}catch(err){setError(err.message);setBusy(false);}};
 const issueAction=async(issue,name)=>{setBusy(true);try{const result=await runComplianceIssueAction(issue.id,name);await done(result.message);}catch(err){setError(err.message);setBusy(false);}};
 const exportRows=async()=>{setBusy(true);try{const result=await exportAuditWorkspace({audit_id:auditFilter||undefined,department_id:departmentFilter||undefined,issue_status:issueStatus,severity});const url=URL.createObjectURL(new Blob([result.csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=result.filename||'audit-workspace.csv';link.click();URL.revokeObjectURL(url);onNotify('Audit export prepared.');}catch(err){setError(err.message);}finally{setBusy(false);}};
 const rows=data?.audits||[],isManager=Boolean(data?.is_manager),metrics=data?.metrics||{};
 const issueRows=(data?.issues||[]).filter(issue=>(issueStatus==='all'||issue.state===issueStatus)&&(severity==='all'||issue.severity===severity));
 return <section className="module-workspace module-governance"><div className="module-header"><div><span className="eyebrow">GOVERNANCE WORKSPACE</span><h1>{showIssues?(isManager?'Compliance issues':'My compliance issues'):(isManager?'Audits':'My audits')}</h1><p>{isManager?'Manage audit cycles, findings, issue ownership, and resolution status.':'View assigned audit work and raise compliance issues for administrator review.'}</p></div><div className="header-actions">{isManager&&!showIssues&&<button className="primary-btn" onClick={()=>setAuditModal({})}><Plus size={18}/> New Audit</button>}<button className="primary-btn" onClick={()=>setIssueModal({})}><Plus size={18}/> Raise Issue</button></div></div><section className="module-stat-strip"><article><span>{showIssues?'Active issues':'Audits in review'}</span><strong>{showIssues?metrics.open_issues||0:metrics.under_review||0}</strong></article><article><span>Overdue issues</span><strong>{metrics.overdue_issues||0}</strong></article><article><span>{showIssues?'High risk':'Completed audits'}</span><strong>{showIssues?metrics.high_risk_issues||0:metrics.completed||0}</strong></article><article><span>Resolution rate</span><strong>{metrics.resolution_rate||0}%</strong></article></section><div className="table-toolbar"><label className="table-search"><Search size={16}/><input value={query} placeholder={showIssues?'Search issues':'Search audits'} onChange={event=>setQuery(event.target.value)} onKeyDown={event=>event.key==='Enter'&&load()}/></label>{isManager&&<select value={departmentFilter} onChange={event=>setDepartmentFilter(event.target.value)}><option value="">All departments</option>{(data?.departments||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select>}{showIssues&&<select value={auditFilter} onChange={event=>setAuditFilter(event.target.value)}><option value="">All audits</option>{(data?.audit_options||[]).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select>}<button className="soft-btn" onClick={load}>{busy?'Refreshing...':'Refresh'}</button></div><div className="game-tabs">{['all','under_review','completed'].map(value=><button key={value} className={status===value?'selected':''} onClick={()=>setStatus(value)}>{value==='all'?'All audits':labelize(value)}</button>)}</div><div className="game-tabs">{['all',...issueStatuses.map(([value])=>value)].map(value=><button key={value} className={issueStatus===value?'selected':''} onClick={()=>setIssueStatus(value)}>{value==='all'?'All issues':labelize(value)}</button>)}{['low','medium','high','critical'].map(value=><button key={value} className={severity===value?'selected':''} onClick={()=>setSeverity(severity===value?'all':value)}>{value}</button>)}</div>{isManager&&<div className="row-actions"><button disabled={busy||(!rows.length&&!issueRows.length)} onClick={exportRows}>Export CSV</button></div>}{error&&<p className="form-error">{error}</p>}{showIssues?<section className="data-surface"><div className="data-table-wrap"><table><thead><tr><th>Issue</th><th>Audit</th><th>Department</th><th>Severity</th><th>Owner</th><th>Due Date</th><th>Status</th><th/></tr></thead><tbody>{issueRows.map(issue=><tr key={issue.id}><td>{issue.name}</td><td>{issue.audit||'--'}</td><td>{issue.department||'--'}</td><td>{issue.severity}</td><td>{issue.owner||'--'}</td><td>{issue.due_date||'--'}</td><td><span className={`workflow-pill ${issue.is_overdue?'overdue':issue.state}`}>{issue.is_overdue?'overdue':labelize(issue.state)}</span></td><td className="row-actions">{isManager&&<><button onClick={()=>setIssueModal(issue)}>Edit</button><button disabled={issue.state==='under_review'} onClick={()=>issueAction(issue,'review')}>Review</button><button disabled={issue.state==='action_required'} onClick={()=>issueAction(issue,'require_action')}>Action</button><button disabled={issue.state==='resolved'} onClick={()=>issueAction(issue,'resolve')}>Resolve</button><button disabled={issue.state==='rejected'} onClick={()=>issueAction(issue,'reject')}>Reject</button><button disabled={issue.state==='open'} onClick={()=>issueAction(issue,'reopen')}>Reopen</button><button disabled={['resolved','rejected'].includes(issue.state)} onClick={()=>issueAction(issue,'remind')}>Remind</button></>}<button disabled={!issue.audit_id} onClick={()=>setDetail(rows.find(audit=>audit.id===issue.audit_id))}>Audit</button></td></tr>)}{!issueRows.length&&<tr><td colSpan="8"><div className="empty-state"><ClipboardCheck size={23}/><strong>No compliance issues in this view.</strong><span>Issues raised from audits or employees will appear here.</span></div></td></tr>}</tbody></table></div></section>:<section className="data-surface"><div className="data-table-wrap"><table><thead><tr><th>Audit</th><th>Department</th><th>Auditor</th><th>Date</th><th>Target Closure</th><th>Findings</th><th>Open Issues</th><th>Status</th><th/></tr></thead><tbody>{rows.map(audit=><tr key={audit.id}><td>{audit.name}</td><td>{audit.department||'--'}</td><td>{audit.auditor||'--'}</td><td>{audit.audit_date||'--'}</td><td>{audit.due_date||'--'}</td><td>{audit.findings_text||'--'}</td><td><button className="text-button" onClick={()=>setDetail(audit)}>{audit.open_issue_count} open · {audit.overdue_issue_count} overdue</button></td><td><span className={`workflow-pill ${audit.state}`}>{labelize(audit.state)}</span></td><td className="row-actions"><button onClick={()=>setDetail(audit)}>View</button>{isManager&&<><button onClick={()=>setAuditModal(audit)}>Edit</button><button disabled={audit.state==='completed'} onClick={()=>auditAction(audit,'complete')}>Complete</button><button disabled={audit.state==='under_review'} onClick={()=>auditAction(audit,'reopen')}>Reopen</button></>}</td></tr>)}{!rows.length&&<tr><td colSpan="9"><div className="empty-state"><ClipboardCheck size={23}/><strong>{isManager?'No audits created yet.':'No audits assigned to you.'}</strong><span>{isManager?'Create an audit cycle when governance review is ready.':'Audits appear here when you are the auditor or part of the audited department.'}</span></div></td></tr>}</tbody></table></div></section>}{!showIssues&&issueRows.length>0&&<section className="data-surface review-panel"><div className="panel-title"><div><span className="eyebrow violet-text">COMPLIANCE ISSUES</span><h3>{isManager?'Open issue queue':'Your raised issues'}</h3></div></div><div className="data-table-wrap"><table><thead><tr><th>Issue</th><th>Audit</th><th>Severity</th><th>Due Date</th><th>Status</th></tr></thead><tbody>{issueRows.slice(0,5).map(issue=><tr key={issue.id}><td>{issue.name}</td><td>{issue.audit||'--'}</td><td>{issue.severity}</td><td>{issue.due_date||'--'}</td><td><span className={`workflow-pill ${issue.is_overdue?'overdue':issue.state}`}>{issue.is_overdue?'overdue':labelize(issue.state)}</span></td></tr>)}</tbody></table></div></section>}{auditModal&&<AuditForm audit={auditModal.id?auditModal:null} data={data} onClose={()=>setAuditModal(null)} onSaved={done}/>} {issueModal&&<IssueForm issue={issueModal.id?issueModal:null} audit={issueModal.audit_id?rows.find(audit=>audit.id===issueModal.audit_id):issueModal.id?null:detail} data={data} isManager={isManager} onClose={()=>setIssueModal(null)} onSaved={done}/>} {detail&&<AuditDetail audit={detail} isManager={isManager} onClose={()=>setDetail(null)} onAuditAction={auditAction} onIssueAction={issueAction} onIssueEdit={setIssueModal} onIssueCreate={setIssueModal}/>}</section>;
}

function GovernanceOverview({ onNavigate }) {
 const [data,setData]=useState(null),[error,setError]=useState('');
 const load=async()=>{try{const [policy,audit]=await Promise.all([getPolicyWorkspace({status:'all',acknowledgement:'all'}),getAuditWorkspace({status:'all',issue_status:'all',severity:'all'})]);setData({policy,audit});setError('');}catch(err){setError(err.message);}};
 useEffect(()=>{load();},[]);
 const policies=data?.policy?.policies||[],audits=data?.audit?.audits||[],issues=data?.audit?.issues||[],isManager=Boolean(data?.policy?.is_manager||data?.audit?.is_manager);
 const pendingPolicies=policies.filter(row=>row.my_acknowledgement?.state==='pending'||row.pending_count>0);
 const dueReviews=policies.filter(row=>['due_soon','overdue'].includes(row.review_state));
 const activeIssues=issues.filter(row=>['open','under_review','action_required'].includes(row.state));
 const myTasks=isManager?[
  ['Policy acknowledgements',`${data?.policy?.metrics?.pending||0} pending acknowledgements`,'Policy acknowledgements'],
  ['Policy reviews',`${data?.policy?.metrics?.review_due||0} due or overdue reviews`,'Policies'],
  ['Compliance issues',`${activeIssues.length} active issue${activeIssues.length===1?'':'s'}`,'Compliance issues'],
  ['Audits',`${data?.audit?.metrics?.under_review||0} audit${data?.audit?.metrics?.under_review===1?'':'s'} under review`,'Audits'],
 ]:[
  ['My acknowledgements',`${pendingPolicies.length} policy task${pendingPolicies.length===1?'':'s'} pending`,'Policy acknowledgements'],
  ['My issues',`${activeIssues.length} raised or assigned issue${activeIssues.length===1?'':'s'}`,'Compliance issues'],
  ['My audits',`${audits.length} audit${audits.length===1?'':'s'} visible`,'Audits'],
 ];
 return <section className="module-workspace module-governance governance-control-room"><div className="module-header"><div><span className="eyebrow">GOVERNANCE CONTROL</span><h1>{isManager?'Governance control room':'My governance workspace'}</h1><p>{isManager?'Review policy health, acknowledgement gaps, audit cycles, and compliance risks from one place.':'Complete assigned policies and track your own audit or issue work without seeing other employees data.'}</p></div><button className="soft-btn" onClick={load}>Refresh</button></div>{error&&<p className="form-error">{error}</p>}<section className="module-stat-strip"><article><span>Active policies</span><strong>{data?.policy?.metrics?.active||0}</strong></article><article><span>Pending acknowledgements</span><strong>{data?.policy?.metrics?.pending||0}</strong></article><article><span>Audits in review</span><strong>{data?.audit?.metrics?.under_review||0}</strong></article><article><span>Open compliance risk</span><strong>{data?.audit?.metrics?.open_issues||0}</strong></article></section><section className="governance-task-grid">{myTasks.map(([title,body,target])=><button className="data-surface governance-task-card" key={title} onClick={()=>onNavigate(target)}><span className="eyebrow violet-text">{title.toUpperCase()}</span><strong>{body}</strong><small>Open {target}</small><ArrowUpRight size={16}/></button>)}</section><section className="governance-overview-grid"><article className="data-surface governance-panel"><div className="panel-title"><div><span className="eyebrow violet-text">POLICY REVIEW</span><h3>Due review queue</h3></div></div>{dueReviews.slice(0,5).map(row=><button className="governance-mini-row" key={row.id} onClick={()=>onNavigate('Policies')}><strong>{row.name}</strong><span>{row.review_date||'No date'} · {labelize(row.review_state)}</span></button>)}{!dueReviews.length&&<p className="panel-empty">No policies are due for review.</p>}</article><article className="data-surface governance-panel"><div className="panel-title"><div><span className="eyebrow violet-text">RISK REGISTER</span><h3>Severity mix</h3></div></div>{['critical','high','medium','low'].map(level=><div className="risk-row" key={level}><span>{level}</span><strong>{data?.audit?.metrics?.severity_counts?.[level]||0}</strong></div>)}</article><article className="data-surface governance-panel"><div className="panel-title"><div><span className="eyebrow violet-text">ACTIVE ISSUES</span><h3>{activeIssues.length} requiring attention</h3></div></div>{activeIssues.slice(0,5).map(row=><button className="governance-mini-row" key={row.id} onClick={()=>onNavigate('Compliance issues')}><strong>{row.name}</strong><span>{row.owner||'Unassigned'} · {labelize(row.state)} · due {row.due_date||'unscheduled'}</span></button>)}{!activeIssues.length&&<p className="panel-empty">No active compliance issues.</p>}</article></section></section>;
}

function ModuleWorkspace({ label, onNotify }) {
 if(['Policies','Policy acknowledgements'].includes(label))return <PolicyWorkspace active={label} onNotify={onNotify}/>;
 if(['Audits','Compliance issues'].includes(label))return <AuditWorkspace active={label} onNotify={onNotify}/>;
 if(['CSR activities','Employee participation'].includes(label))return <SocialWorkspace active={label} onNotify={onNotify}/>;
 const config = modules[label] || modules['Carbon transactions']; const [data,setData]=useState(null); const [query,setQuery]=useState(''); const [modal,setModal]=useState(null); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
 const load = async () => { setBusy(true); try { setData(await getResource(config.slug, query || undefined)); setError(''); } catch(e) { setError(e.message); } finally { setBusy(false); } };
 useEffect(() => { load(); }, [config.slug]);
 const saveDone = message => { setModal(null); onNotify(message); load(); };
 const remove = async record => { if (!window.confirm(`Delete “${record.display_name || record.name || 'this record'}”? This cannot be undone.`)) return; try { await deleteResource(config.slug, record.id); onNotify('Record deleted.'); load(); } catch(e) { setError(e.message); } };
 const policyAction = async (record, action) => { setBusy(true); try { const result = await runPolicyAction(record.id, action); onNotify(result.message); await load(); } catch(e) { setError(e.message); } finally { setBusy(false); } };
 const acknowledge = async record => { setBusy(true); try { const result = await acknowledgePolicy(record.id); onNotify(result.message); await load(); } catch(e) { setError(e.message); } finally { setBusy(false); } };
 const fields = data?.fields || []; const rows = data?.records || []; const pillar = config.pillar || (label.includes('Policy') || label.includes('Audit') || label.includes('Compliance') ? 'governance' : label.includes('Challenge') || label.includes('Badge') || label.includes('Reward') ? 'gamification' : label.includes('CSR') || label.includes('Participation') || label.includes('Diversity') ? 'social' : 'environmental');
 return <section className={`module-workspace module-${pillar}`}><div className="module-header"><div><span className="eyebrow">{pillar.toUpperCase()} WORKSPACE</span><h1>{label}</h1><p>{config.subtitle}</p></div><button className="primary-btn" disabled={!data?.can_create} onClick={()=>setModal({})}><Plus size={18}/> Add record</button></div><div className="module-stat-strip"><article><span>Saved records</span><strong>{rows.length}</strong></article><article><span>Visible fields</span><strong>{fields.length}</strong></article><article><span>Access level</span><strong>{data?.can_write ? 'Editor' : 'Viewer'}</strong></article></div><div className="table-toolbar"><label className="table-search"><Search size={16}/><input value={query} placeholder={`Search ${label.toLowerCase()}`} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key === 'Enter' && load()}/></label><button className="soft-btn" onClick={load}>{busy ? 'Refreshing…' : 'Refresh'}</button></div>{error && <p className="form-error">{error}</p>}<div className="data-surface"><div className="data-table-wrap"><table><thead><tr>{fields.map(f=><th key={f.name}>{f.string}</th>)}<th aria-label="Actions" /></tr></thead><tbody>{busy && !data ? <tr><td colSpan={fields.length+1}>Loading EcoSphere data…</td></tr> : rows.length ? rows.map(row=><tr key={row.id}>{fields.map(f=><td key={f.name}>{f.type === 'boolean' ? (row[f.name] ? 'Yes' : 'No') : f.name === 'acknowledgement_progress' ? `${Math.round(Number(row[f.name])||0)}%` : valueText(row[f.name])}</td>)}<td className="row-actions">{config.slug === 'policies' && data?.is_manager ? <><button title="Edit" disabled={!data?.can_write || row.state === 'archived'} onClick={()=>setModal(row)}>Edit</button><button disabled={row.state !== 'draft'} onClick={()=>policyAction(row,'publish')}>Publish</button><button disabled={!['draft','published','effective'].includes(row.state)} onClick={()=>policyAction(row,'activate')}>Activate</button><button disabled={row.state === 'archived'} onClick={()=>policyAction(row,'remind')}>Remind</button><button disabled={row.state === 'archived'} onClick={()=>policyAction(row,'archive')}>Archive</button></> : config.slug === 'policy-acknowledgements' && !data?.is_manager ? <button disabled={row.state === 'acknowledged'} onClick={()=>acknowledge(row)}>Acknowledge</button> : <><button title="Edit" disabled={!data?.can_write} onClick={()=>setModal(row)}>Edit</button><button title="Delete" disabled={!data?.can_delete} onClick={()=>remove(row)}>Delete</button></>}</td></tr>) : <tr><td colSpan={fields.length+1}><div className="empty-state"><Leaf size={22}/><strong>No records yet</strong><span>{data?.is_manager ? `Create the first ${label.toLowerCase()} record.` : `No ${label.toLowerCase()} require your attention.`}</span></div></td></tr>}</tbody></table></div></div>{modal && <RecordForm slug={config.slug} fields={fields} record={modal.id ? modal : null} onClose={()=>setModal(null)} onSaved={saveDone}/>}</section>;
}

function GamificationWorkspace({ onNotify }) {
 const [data,setData]=useState(null); const [filter,setFilter]=useState('active'); const [creating,setCreating]=useState(false); const [saving,setSaving]=useState(false); const [error,setError]=useState(''); const [joining,setJoining]=useState(null);
 const load=async()=>{try{setData(await getGamification());setError('');}catch(err){setError(err.message);}}; useEffect(()=>{load();},[]);
 const create=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);try{await createChallenge({name:form.get('name'),description:form.get('description'),xp_value:form.get('xp_value'),difficulty:form.get('difficulty'),deadline:form.get('deadline'),state:form.get('state')});setCreating(false);await load();onNotify('Challenge added to your employee portal.');}catch(err){setError(err.message);}finally{setSaving(false);}};
 const join=async id=>{setJoining(id);try{const result=await joinChallenge(id);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setJoining(null);}};
 const rows=(data?.challenges || []).filter(row=>filter==='all' || row.state===filter); const plain=value=>String(value || '').replace(/<[^>]*>/g,'').trim();
 return <section className="module-workspace module-gamification gamification-workspace"><div className="module-header"><div><span className="eyebrow orange-text">GAMIFICATION WORKSPACE</span><h1>{data?.is_manager ? 'Challenges & recognition' : 'Your sustainability challenges'}</h1><p>{data?.is_manager ? 'Create live challenges and give your team meaningful ways to participate.' : 'Join active challenges, earn recognition, and follow your progress.'}</p></div>{data?.is_manager && <button className="primary-btn" onClick={()=>setCreating(true)}><Plus size={18}/> Create challenge</button>}</div><div className="game-tabs">{[['active','Active'],['draft','Draft'],['under_review','Under review'],['completed','Completed'],['all','All challenges']].filter(([key])=>data?.is_manager || key==='active').map(([key,label])=><button key={key} className={filter===key?'selected':''} onClick={()=>setFilter(key)}>{label}</button>)}</div>{error&&<p className="form-error">{error}</p>}<section className="challenge-grid">{rows.length?rows.map(challenge=><article className="challenge-card" key={challenge.id}><div className="challenge-top"><span className={`state-pill ${challenge.state}`}>{challenge.state.replace('_',' ')}</span><span className="xp-chip">{challenge.xp_value} XP</span></div><h3>{challenge.name}</h3><p>{plain(challenge.description) || 'No description added yet.'}</p><div className="challenge-meta"><span>{challenge.difficulty}</span><span>Due {challenge.deadline || '—'}</span><span>{challenge.participants} joined</span></div>{data?.is_manager ? <div className="manager-hint">Visible to employees when active</div> : challenge.participation ? <div className="joined-state"><span>{challenge.participation.progress}% progress</span><b>{challenge.participation.state.replace('_',' ')}</b></div> : <button className="challenge-join" disabled={!data?.can_join || joining===challenge.id} onClick={()=>join(challenge.id)}>{joining===challenge.id?'Joining…':data?.can_join?'Join challenge':'Ask admin for employee access'} <ArrowUpRight size={15}/></button>}</article>):<div className="empty-state game-empty"><Trophy size={24}/><strong>No challenges in this view</strong><span>{data?.is_manager?'Create the first challenge for your team.':'Your administrator has not published an active challenge yet.'}</span></div>}</section><section className="game-lower"><article className="data-surface badge-panel"><div className="panel-title"><div><span className="eyebrow orange-text">BADGE GALLERY</span><h3>{data?.is_manager?'Recognition badges':'Your badge progress'}</h3></div></div><div className="badge-grid">{(data?.badges||[]).length?(data.badges||[]).map(badge=><div className={`badge-tile ${badge.unlocked?'unlocked':''}`} key={badge.id}><Trophy size={16}/><div><strong>{badge.name}</strong><span>{badge.unlocked?'Unlocked':`${badge.minimum_xp} XP needed`}</span></div></div>):<p className="panel-empty">No badges have been configured yet.</p>}</div></article><article className="data-surface leaderboard-panel"><div className="panel-title"><div><span className="eyebrow orange-text">LEADERBOARD</span><h3>Team momentum</h3></div></div>{(data?.leaderboard||[]).length?<div className="leader-list">{data.leaderboard.map(row=><div key={`${row.rank}-${row.name}`}><b>#{row.rank}</b><strong>{row.name}</strong><span>{row.xp} XP</span></div>)}</div>:<p className="panel-empty">The leaderboard appears after challenge approvals.</p>}</article></section>{creating&&<div className="modal-scrim"><motion.form className="record-modal" onSubmit={create} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow orange-text">ADMIN PORTAL</span><h2>Create challenge</h2></div><button type="button" className="icon-btn" onClick={()=>setCreating(false)}><X size={18}/></button></div><div className="form-grid"><label>Challenge name<input name="name" required placeholder="e.g. Plastic-free week"/></label><label>XP reward<input name="xp_value" type="number" min="0" defaultValue="100" required/></label><label>Difficulty<select name="difficulty" defaultValue="medium"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label><label>Publish status<select name="state" defaultValue="active"><option value="active">Active — employees can join</option><option value="draft">Draft — only admins can see it</option></select></label><label>Deadline<input name="deadline" type="date" required/></label><label className="wide-field">Description<textarea name="description" required placeholder="Explain the action employees should take and the impact it creates."/></label></div><div className="modal-actions"><button type="button" className="cancel-btn" onClick={()=>setCreating(false)}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Publishing…':'Create challenge'} <ArrowUpRight size={16}/></button></div></motion.form></div>}</section>;
}

function SettingsWorkspace({ onNotify }) {
 const [data,setData]=useState(null); const [error,setError]=useState(''); const [saving,setSaving]=useState(false); const [department,setDepartment]=useState(null);
 const load=async()=>{try{setData(await getSettings());setError('');}catch(err){setError(err.message);}}; useEffect(()=>{load();},[]);
 const saveProfile=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);try{const response=await saveProfileSettings({name:form.get('name'),email_notifications:form.get('email_notifications')==='on',in_app_notifications:form.get('in_app_notifications')==='on'});setData(response);onNotify(response.message);}catch(err){setError(err.message);}finally{setSaving(false);}};
 const saveWorkspace=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);try{const configuration=Object.fromEntries(['environmental_weight','social_weight','governance_weight','auto_emission_calculation','require_csr_evidence','auto_award_badges','compliance_notifications','csr_notifications','challenge_notifications'].map(key=>[key,key.includes('weight')?form.get(key):form.get(key)==='on']));const response=await saveWorkspaceSettings(form.get('workspace_name'),configuration);setData(response);onNotify(response.message);}catch(err){setError(err.message);}finally{setSaving(false);}};
 const saveDept=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);try{const response=await saveDepartment({department_id:department?.id,name:form.get('name'),code:form.get('code')});setData(response);setDepartment(null);onNotify(response.message);}catch(err){setError(err.message);}finally{setSaving(false);}};
 const archive=async id=>{if(!window.confirm('Archive this department? Existing records remain available.'))return;try{const response=await archiveDepartment(id);setData(response);onNotify(response.message);}catch(err){setError(err.message);}};
 const profile=data?.profile; const config=data?.configuration;
 if(!data)return <section className="module-workspace"><div className="empty-state"><Settings size={24}/><strong>Loading settings…</strong></div></section>;
 return <section className="module-workspace settings-workspace"><div className="module-header"><div><span className="eyebrow">{data.is_manager?'WORKSPACE ADMINISTRATION':'PERSONAL SETTINGS'}</span><h1>{data.is_manager?'Settings & administration':'My settings'}</h1><p>{data.is_manager?'Configure your enterprise, departments, ESG controls, and notification policy.':'Manage your profile and how EcoSphere notifies you. Enterprise controls are managed by your administrator.'}</p></div></div>{error&&<p className="form-error">{error}</p>}<div className="settings-grid"><form className="settings-card" onSubmit={saveProfile}><span className="eyebrow green-text">MY PROFILE</span><h3>Personal preferences</h3><label>Full name<input name="name" defaultValue={profile.name} required minLength="2"/></label><label>Work email<input value={profile.email} readOnly aria-readonly="true"/></label><label className="settings-toggle"><input name="email_notifications" type="checkbox" defaultChecked={profile.email_notifications}/><span><b>Email notifications</b><small>Receive important workflow updates by email.</small></span></label><label className="settings-toggle"><input name="in_app_notifications" type="checkbox" defaultChecked={profile.in_app_notifications}/><span><b>In-app notifications</b><small>Show reminders and approvals inside EcoSphere.</small></span></label><button className="primary-btn" disabled={saving}>{saving?'Saving…':'Save my settings'} <ArrowUpRight size={16}/></button></form>{data.is_manager&&<form className="settings-card" onSubmit={saveWorkspace}><span className="eyebrow violet-text">ENTERPRISE</span><h3>Workspace configuration</h3><label>Workspace name<input name="workspace_name" defaultValue={data.workspace.name} required minLength="2"/></label><div className="weight-grid"><label>Environmental %<input name="environmental_weight" type="number" min="0" max="100" step="0.1" defaultValue={config.environmental_weight}/></label><label>Social %<input name="social_weight" type="number" min="0" max="100" step="0.1" defaultValue={config.social_weight}/></label><label>Governance %<input name="governance_weight" type="number" min="0" max="100" step="0.1" defaultValue={config.governance_weight}/></label></div><small className="settings-note">ESG weights must add up to 100%.</small>{[['auto_emission_calculation','Auto-calculate emissions'],['require_csr_evidence','Require proof for CSR activity approval'],['auto_award_badges','Auto-award achievement badges'],['compliance_notifications','Compliance issue notifications'],['csr_notifications','CSR review notifications'],['challenge_notifications','Challenge review notifications']].map(([key,label])=><label className="settings-toggle" key={key}><input name={key} type="checkbox" defaultChecked={config[key]}/><span><b>{label}</b></span></label>)}<button className="primary-btn" disabled={saving}>{saving?'Saving…':'Save workspace configuration'} <ArrowUpRight size={16}/></button></form>}</div>{data.is_manager&&<section className="data-surface settings-department-panel"><div className="panel-title"><div><span className="eyebrow">ORGANISATION STRUCTURE</span><h3>Departments</h3><p className="panel-copy">Departments belong only to {data.workspace.name}.</p></div><button className="primary-btn" onClick={()=>setDepartment({})}><Plus size={16}/> Add department</button></div>{data.departments.length?<div className="data-table-wrap"><table><thead><tr><th>Name</th><th>Code</th><th>Employees</th><th>Status</th><th/></tr></thead><tbody>{data.departments.map(row=><tr key={row.id}><td>{row.name}</td><td>{row.code}</td><td>{row.employees}</td><td>{row.active?'Active':'Archived'}</td><td className="row-actions"><button onClick={()=>setDepartment(row)}>Edit</button>{row.active&&<button onClick={()=>archive(row.id)}>Archive</button>}</td></tr>)}</tbody></table></div>:<div className="empty-state"><Building2 size={23}/><strong>No departments yet</strong><span>Create your first department for this enterprise.</span></div>}</section>}{department&&<div className="modal-scrim"><motion.form className="record-modal" onSubmit={saveDept} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow">ORGANISATION STRUCTURE</span><h2>{department.id?'Edit department':'Add department'}</h2></div><button className="icon-btn" type="button" onClick={()=>setDepartment(null)}><X size={18}/></button></div><div className="form-grid"><label>Department name<input name="name" defaultValue={department.name||''} required minLength="2" placeholder="e.g. Operations"/></label><label>Department code<input name="code" defaultValue={department.code||''} required minLength="2" placeholder="e.g. OPS"/></label></div><div className="modal-actions"><button className="cancel-btn" type="button" onClick={()=>setDepartment(null)}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving…':'Save department'} <ArrowUpRight size={16}/></button></div></motion.form></div>}</section>;
}

function ReportsWorkspace({ onNotify }) { return <section className="module-workspace"><div className="module-header"><div><span className="eyebrow">REPORTING CENTRE</span><h1>Reports</h1><p>Generate trusted ESG outputs from the records stored in your EcoSphere workspace.</p></div></div><div className="report-grid">{['Environmental report','Social report','Governance report','ESG summary'].map(name=><article key={name} className="report-card"><FileBarChart size={22}/><h3>{name}</h3><p>Use the connected Odoo reporting engine to prepare a formal, export-ready report.</p><button className="text-button" onClick={()=>onNotify(`${name} is prepared from your saved EcoSphere records.`)}>Prepare report <ArrowUpRight size={15}/></button></article>)}</div></section>; }

function AiAssistant({ onNavigate }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState(() => `chat-${Date.now()}`);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      reply: 'Ask me about scores, carbon, policies, compliance issues, reports, or challenge recommendations. I answer from saved EcoSphere records and show citations when data backs the answer.',
      citations: [],
      suggested_actions: [],
    },
  ]);
  const listRef = useRef(null);
  const examples = [
    'What is my total ESG score right now?',
    'What compliance issues are overdue?',
    'Recommend my next challenge and badge progress.',
    'Summarize our ESG report.',
  ];

  useEffect(() => {
    if (open) listRef.current?.scrollTo({top: listRef.current.scrollHeight, behavior: 'smooth'});
  }, [messages, open]);

  const send = async (value) => {
    const question = String(value || input).trim();
    if (!question || busy) return;
    setInput('');
    setMessages(current => [...current, {id: `u-${Date.now()}`, role: 'user', reply: question, citations: [], suggested_actions: []}]);
    setBusy(true);
    try {
      const answer = await askEcoSphereAI(question, conversationId);
      setConversationId(answer.conversation_id || conversationId);
      setMessages(current => [...current, {id: `a-${Date.now()}`, role: 'assistant', ...answer}]);
    } catch (error) {
      setMessages(current => [...current, {id: `e-${Date.now()}`, role: 'assistant', reply: error.message || 'EcoSphere AI could not answer right now.', citations: [], suggested_actions: []}]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`ai-assistant ${open ? 'open' : ''}`}>
      <button className="ai-fab" onClick={() => setOpen(value => !value)} title="EcoSphere AI assistant">
        {open ? <X size={19}/> : <Bot size={20}/>}
      </button>
      <AnimatePresence>
        {open && (
          <motion.section
            className="ai-panel"
            initial={{opacity: 0, y: 18, scale: .96}}
            animate={{opacity: 1, y: 0, scale: 1}}
            exit={{opacity: 0, y: 18, scale: .96}}
            transition={{type: 'spring', stiffness: 260, damping: 24}}
          >
            <div className="ai-head">
              <div className="mini-mark"><Bot size={18}/></div>
              <div><strong>EcoSphere AI</strong><span>Grounded in Odoo records</span></div>
            </div>
            <div className="ai-examples">
              {examples.map(example => <button key={example} onClick={() => send(example)} disabled={busy}>{example}</button>)}
            </div>
            <div className="ai-messages" ref={listRef}>
              {messages.map(message => (
                <article className={`ai-message ${message.role}`} key={message.id}>
                  <p>{message.reply}</p>
                  {!!message.citations?.length && (
                    <div className="ai-citations">
                      {message.citations.map((citation, index) => <span key={`${citation.type}-${citation.id}-${index}`} title={citation.note}>{citation.label}{citation.note ? ` · ${citation.note}` : ''}</span>)}
                    </div>
                  )}
                  {!!message.suggested_actions?.length && (
                    <div className="ai-actions">
                      {message.suggested_actions.map((action, index) => <button key={`${action.target}-${index}`} onClick={() => action.target && onNavigate(action.target)}>{action.label || action.target} <ArrowUpRight size={12}/></button>)}
                    </div>
                  )}
                </article>
              ))}
              {busy && <article className="ai-message assistant"><p>Checking the relevant EcoSphere records...</p></article>}
            </div>
            <form className="ai-compose" onSubmit={event => { event.preventDefault(); send(); }}>
              <input value={input} onChange={event => setInput(event.target.value)} placeholder="Ask about ESG data" />
              <button disabled={busy || !input.trim()} title="Send"><SendHorizontal size={17}/></button>
            </form>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  );
}

function TeamAccess({ onNotify }) {
 const [team,setTeam]=useState([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [saving,setSaving]=useState(false);
 const load=async()=>{setLoading(true);try{const data=await getTeam();setTeam(data.members);setError('');}catch(e){setError(e.message);}finally{setLoading(false);}}; useEffect(()=>{load();},[]);
 const submit=async e=>{e.preventDefault();const formElement=e.currentTarget;const form=new FormData(formElement);setSaving(true);setError('');try{await createTeamMember(form.get('name'),form.get('email'),form.get('password'));formElement.reset();await load();onNotify('Employee account created. Share the credentials securely.');}catch(err){setError(err.message);}finally{setSaving(false);}};
 return <section className="module-workspace"><div className="module-header"><div><span className="eyebrow">ADMINISTRATION</span><h1>Team access</h1><p>Create employee logins and manage who can access your EcoSphere enterprise.</p></div></div><div className="team-layout"><form className="team-create" onSubmit={submit}><h3>Create employee account</h3><p>Employees receive an email and password from an administrator. Public sign-up is disabled.</p><label>Full name<input name="name" required placeholder="Employee name"/></label><label>Work email<input name="email" type="email" required placeholder="employee@company.com"/></label><label>Temporary password<input name="password" type="password" minLength="8" required placeholder="At least 8 characters"/></label>{error&&<p className="form-error">{error}</p>}<button className="primary-btn" disabled={saving}>{saving?'Creating…':'Create employee account'} <ArrowUpRight size={16}/></button></form><section className="data-surface team-list"><div className="panel-title"><div><span className="eyebrow">ENTERPRISE MEMBERS</span><h3>{loading?'Loading members…':`${team.length} member${team.length===1?'':'s'}`}</h3></div><button className="soft-btn" onClick={load}>Refresh</button></div>{team.map(member=><div className="team-row" key={member.id}><div className="person-avatar">{member.name.split(' ').map(p=>p[0]).join('').slice(0,2)}</div><div><strong>{member.name}</strong><span>{member.email}</span></div><b className={member.role==='Administrator'?'role-admin':''}>{member.role}</b></div>)}</section></div></section>;
}

function SocialActivityForm({ activity, data, onClose, onSaved }) {const [saving,setSaving]=useState(false);const [error,setError]=useState('');const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);setError('');const values={name:form.get('name'),description:form.get('description'),activity_date:form.get('activity_date'),department_name:form.get('department_name'),category_id:form.get('category_id'),points:form.get('points'),capacity:form.get('capacity'),evidence_required:form.get('evidence_required')==='on',active:form.get('active')==='on'};try{if(activity)await updateSocialActivity(activity.id,values);else await createSocialActivity(values);onSaved(activity?'CSR activity updated.':'CSR activity created.');}catch(err){setError(err.message);setSaving(false);}};return <div className="modal-scrim"><motion.form className="record-modal social-form" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow blue-text">SOCIAL IMPACT</span><h2>{activity?'Edit CSR activity':'Create CSR activity'}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="form-grid"><label>Activity name<input name="name" required defaultValue={activity?.name||''} placeholder="e.g. Community tree plantation"/></label><label>Activity date<input name="activity_date" type="date" required defaultValue={activity?.activity_date||''}/></label><label>Responsible department<input name="department_name" list="social-departments" required defaultValue={activity?.department||''} placeholder="e.g. Operations"/><datalist id="social-departments">{(data.departments||[]).map(([,name])=><option value={name} key={name}/>)}</datalist><small>Choose an existing department or enter a new one.</small></label><label>CSR category<select name="category_id" defaultValue={activity?.category_id||''}><option value="">No category</option>{(data.categories||[]).map(([id,name])=><option value={id} key={id}>{name}</option>)}</select></label><label>Points after approval<input name="points" type="number" min="0" defaultValue={activity?.points||0}/></label><label>Participation capacity<input name="capacity" type="number" min="0" defaultValue={activity?.capacity||0}/></label><label className="check-field"><input name="evidence_required" type="checkbox" defaultChecked={Boolean(activity?.evidence_required)}/><span>Require photo or PDF proof</span></label><label className="check-field"><input name="active" type="checkbox" defaultChecked={activity?Boolean(activity.active):true}/><span>Publish to employees now</span></label><label className="full-form-field">Employee instructions<textarea name="description" required defaultValue={String(activity?.description||'').replace(/<[^>]*>/g,'')} placeholder="Explain where to go, what to complete, and what proof is required."/></label></div>{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving…':'Save activity'} <ArrowUpRight size={16}/></button></div></motion.form></div>}

function SocialProofModal({ activity, onClose, onSaved }) {const [file,setFile]=useState(null);const [error,setError]=useState('');const [saving,setSaving]=useState(false);const pick=event=>{const selected=event.target.files?.[0];if(!selected)return;if(!['image/jpeg','image/png','application/pdf'].includes(selected.type)||selected.size>5*1024*1024){setError('Use a JPG, PNG, or PDF file up to 5 MB.');return;}const reader=new FileReader();reader.onload=()=>setFile({name:selected.name,data:String(reader.result).split(',')[1]});reader.readAsDataURL(selected);};const submit=async event=>{event.preventDefault();if(activity.evidence_required&&!file){setError('This activity requires proof before it can be submitted.');return;}setSaving(true);try{await submitSocialParticipation(activity.participation.id,file?.data,file?.name);onSaved('Completion submitted for administrator review.');}catch(err){setError(err.message);setSaving(false);}};return <div className="modal-scrim"><motion.form className="record-modal proof-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow blue-text">COMPLETE ACTIVITY</span><h2>{activity.name}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><p className="panel-copy">{activity.evidence_required?'Upload one clear JPG, PNG, or PDF proof. Your administrator reviews it before points are awarded.':'Confirm that you completed this activity. Your administrator will review the submission.'}</p>{activity.evidence_required&&<label className="social-file"><input type="file" accept="image/jpeg,image/png,application/pdf" onChange={pick}/><span>{file?`${file.name} ready to submit`:'Choose proof file'}</span></label>}{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Submitting…':'Submit completion'} <ArrowUpRight size={16}/></button></div></motion.form></div>}


const SOCIAL_ACTIVITY_TEMPLATES = [
 {id:'tree-plantation',label:'Environment',name:'Community tree plantation',points:120,evidence:true,description:'Plant a native tree with the community. Upload one clear photo showing the employee and the planted tree. Do not submit images of people without their permission.'},
 {id:'blood-donation',label:'Wellbeing',name:'Blood donation drive',points:150,evidence:true,description:'Join an approved voluntary blood-donation drive. Upload only an attendance confirmation; never upload medical records or health information.'},
 {id:'beach-cleanup',label:'Community',name:'Beach cleanup',points:100,evidence:true,description:'Take part in a scheduled cleanup. Submit a photo of the collected waste at the designated collection point.'},
 {id:'esg-workshop',label:'Learning',name:'ESG learning workshop',points:75,evidence:false,description:'Attend the scheduled ESG workshop and complete the facilitator attendance check.'},
 {id:'food-drive',label:'Community',name:'Community food drive',points:110,evidence:true,description:'Volunteer at the enterprise food drive. Submit a photo of your volunteering activity, with consent from anyone identifiable in the image.'},
];

function SocialTemplateGallery({onSelect}) {return <section className="social-template-gallery"><div className="template-gallery-heading"><div><span className="eyebrow blue-text">PREDEFINED CSR TEMPLATES</span><h2>Start with a proven activity</h2></div><p>Select a template, set the date and department, then publish it to employees.</p></div><div className="template-card-grid">{SOCIAL_ACTIVITY_TEMPLATES.map(template=><button className="social-template-card" type="button" key={template.id} onClick={()=>onSelect(template)}><span>{template.label}</span><strong>{template.name}</strong><small>{template.points} points · {template.evidence?'proof required':'attendance confirmed'}</small><ArrowUpRight size={16}/></button>)}</div></section>}

function SocialTemplatePublishModal({template,onClose,onSaved}) {const [saving,setSaving]=useState(false);const [error,setError]=useState('');const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);setError('');try{await createSocialActivity({name:template.name,description:template.description,activity_date:form.get('activity_date'),department_name:form.get('department_name'),points:template.points,capacity:form.get('capacity')||0,evidence_required:template.evidence,active:form.get('active')==='on'});onSaved(`${template.name} published to employees.`);}catch(err){setError(err.message);setSaving(false);}};return <div className="modal-scrim"><motion.form className="record-modal social-form template-publish-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow blue-text">CSR TEMPLATE</span><h2>{template.name}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><p className="panel-copy">{template.description}</p><div className="template-publish-meta"><span>{template.points} points after approval</span><span>{template.evidence?'Photo or PDF proof required':'Administrator attendance review'}</span></div><div className="form-grid"><label>Activity date<input name="activity_date" type="date" required/></label><label>Responsible department<input name="department_name" required placeholder="e.g. People operations"/><small>A new department is created if needed.</small></label><label>Participation capacity<input name="capacity" type="number" min="0" defaultValue="0"/><small>Use 0 for unlimited participation.</small></label><label className="check-field"><input name="active" type="checkbox" defaultChecked/><span>Publish to employees now</span></label></div>{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button className="cancel-btn" type="button" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Publishing…':'Publish activity'} <ArrowUpRight size={16}/></button></div></motion.form></div>}

function SocialWorkspace({ active, onNotify }) {
 const [data,setData]=useState(null),[modal,setModal]=useState(null),[proof,setProof]=useState(null),[template,setTemplate]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(null);
 const tab=active==='Employee participation'?'participation':active==='Diversity dashboard'?'diversity':'activities';
 const load=async()=>{try{setData(await getSocial());setError('');}catch(err){setError(err.message);}};
 useEffect(()=>{load();},[]);
 const complete=async message=>{setModal(null);setProof(null);setTemplate(null);await load();onNotify(message);};
 const join=async id=>{setBusy(id);try{const result=await joinSocialActivity(id);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(null);}};
 const review=async(id,approved)=>{setBusy(id);try{const result=await reviewSocialParticipation(id,approved,approved?'Approved by administrator.':'Please correct the submitted evidence and resubmit.');await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(null);}};
 const archive=async id=>{if(!window.confirm('Archive this activity? Employees will no longer see it.'))return;setBusy(id);try{const result=await archiveSocialActivity(id);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(null);}};
 if(tab==='diversity')return <ModuleWorkspace label="Diversity dashboard" onNotify={onNotify}/>;
 const entries=tab==='participation'?(data?.is_manager?data?.submissions:data?.my_participations):data?.activities||[];
 return <section className="module-workspace module-social social-workspace"><div className="module-header"><div><span className="eyebrow blue-text">SOCIAL IMPACT WORKSPACE</span><h1>{tab==='activities'?(data?.is_manager?'CSR activity studio':'Community activities'):(data?.is_manager?'Participation approval queue':'My participation')}</h1><p>{tab==='activities'?(data?.is_manager?'Publish a ready-made CSR template or create an activity for your enterprise.':'Join published CSR activities and submit your completion when ready.'):(data?.is_manager?'Review proof, record a decision, and award social-impact points fairly.':'Track your activity submissions and read the administrator decision.')}</p></div>{data?.is_manager&&tab==='activities'&&<button className="primary-btn" onClick={()=>setModal({})}><Plus size={16}/> Create custom activity</button>}</div>
 {data?.is_manager&&tab==='activities'&&<SocialTemplateGallery onSelect={setTemplate}/>}<section className="module-stat-strip social-stat-strip"><article><span>Published activities</span><strong>{data?.metrics?.activities||0}</strong></article><article><span>{data?.is_manager?'Submissions awaiting review':'My joined activities'}</span><strong>{data?.is_manager?(data?.submissions||[]).filter(row=>row.state==='submitted').length:data?.metrics?.joined||0}</strong></article><article><span>{data?.is_manager?'Approved outcomes':'Approved points'}</span><strong>{data?.is_manager?(data?.submissions||[]).filter(row=>row.state==='approved').length:`${data?.metrics?.approved_points||0} XP`}</strong></article></section>{error&&<p className="form-error">{error}</p>}
 {tab==='activities'?<section className="social-activity-grid">{entries.map(activity=><article className="social-activity-card" key={activity.id}><div className="challenge-top"><span className={`state-pill ${activity.active?'active':'draft'}`}>{activity.active?'Published':'Archived'}</span><span className="xp-chip">{activity.points} pts</span></div><h3>{activity.name}</h3><p>{String(activity.description||'').replace(/<[^>]*>/g,'')||'No instructions added yet.'}</p><div className="social-activity-meta"><span>{activity.activity_date}</span><span>{activity.department}</span><span>{activity.evidence_required?'Proof required':'No proof required'}</span><span>{activity.capacity?`${activity.participants}/${activity.capacity} joined`:`${activity.participants} joined`}</span></div>{data?.is_manager?<div className="social-card-actions"><button className="soft-btn" onClick={()=>setModal(activity)}>Edit</button>{activity.active&&<button className="danger-btn" disabled={busy===activity.id} onClick={()=>archive(activity.id)}>Archive</button>}</div>:activity.participation?<button className="challenge-join" disabled={activity.participation.state==='submitted'||activity.participation.state==='approved'} onClick={()=>setProof(activity)}>{activity.participation.state==='approved'?'Points awarded':activity.participation.state==='submitted'?'Awaiting review':activity.evidence_required?'Upload proof':'Submit completion'} <ArrowUpRight size={15}/></button>:<button className="challenge-join" disabled={!data?.can_participate||busy===activity.id} onClick={()=>join(activity.id)}>{busy===activity.id?'Joining…':'Join activity'} <ArrowUpRight size={15}/></button>}</article>)}{!entries.length&&<div className="empty-state"><Users size={24}/><strong>No activities yet</strong><span>{data?.is_manager?'Choose a predefined template or create a custom activity for your team.':'Your administrator has not published a CSR activity yet.'}</span></div>}</section>:<section className="data-surface social-review-surface"><div className="data-table-wrap"><table><thead><tr><th>{data?.is_manager?'Employee':'Activity'}</th><th>{data?.is_manager?'Activity':'Submission'}</th><th>Status</th><th>Points</th><th>Proof</th><th>Decision</th><th/></tr></thead><tbody>{entries.map(row=>{const own=!data?.is_manager;const activity=own?row:null;const state=own?activity.participation.state:row.state;return <tr key={own?activity.id:row.id}><td>{own?activity.name:row.employee}</td><td>{own?activity.participation.completion_date||'—':row.activity}</td><td><span className={`workflow-pill ${state}`}>{String(state).replace('_',' ')}</span></td><td>{own?activity.points:row.points}</td><td>{own?activity.participation.proof_filename||'—':row.proof_filename||'—'}</td><td>{own?activity.participation.approval_note||'—':row.note||'—'}</td><td>{data?.is_manager&&row.state==='submitted'&&<div className="row-actions"><button disabled={busy===row.id} onClick={()=>review(row.id,true)}>Approve</button><button disabled={busy===row.id} onClick={()=>review(row.id,false)}>Reject</button></div>}</td></tr>})}{!entries.length&&<tr><td colSpan="7"><div className="empty-state"><ClipboardCheck size={23}/><strong>No participation records</strong><span>Records will appear here as employees join and submit activities.</span></div></td></tr>}</tbody></table></div></section>}
 {modal&&<SocialActivityForm activity={modal.id?modal:null} data={data} onClose={()=>setModal(null)} onSaved={complete}/>} {proof&&<SocialProofModal activity={proof} onClose={()=>setProof(null)} onSaved={complete}/>} {template&&<SocialTemplatePublishModal template={template} onClose={()=>setTemplate(null)} onSaved={complete}/>}</section>
}

const pillarConfigs={
 Environmental:{eyebrow:'ENVIRONMENTAL OPERATIONS',title:'Environmental command center',subtitle:'Monitor the carbon ledger, calculation inputs, product coverage, and reduction targets from one operational view.',items:[['Carbon transactions','carbon-transactions','Carbon ledger'],['Emission factors','emission-factors','Calculation library'],['Product ESG profiles','product-profiles','Product footprint'],['Environmental goals','environmental-goals','Target tracking']]},
 Social:{eyebrow:'SOCIAL IMPACT',title:'Social impact hub',subtitle:'Plan employee-led social initiatives and keep participation evidence and diversity records in one calm programme view.',items:[['CSR activities','csr-activities','Initiatives'],['Employee participation','employee-participation','Participation evidence'],['Diversity dashboard','diversity-dashboard','Workforce insight']]},
 Governance:{eyebrow:'GOVERNANCE CONTROL',title:'Governance control room',subtitle:'Keep policies, acknowledgements, audit cycles, and compliance risks visible before they become blockers.',items:[['Policies','policies','Policy register'],['Policy acknowledgements','policy-acknowledgements','Employee acceptance'],['Audits','audits','Assurance cycles'],['Compliance issues','compliance-issues','Risk register']]},
};

function PillarWorkspace({ pillar, onNavigate }) {
 if(pillar==='Social')return <SocialWorkspace active="Social" onNotify={()=>{}}/>;
 const config=pillarConfigs[pillar];const [sets,setSets]=useState([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');
 const load=async()=>{setLoading(true);try{const rows=await Promise.all(config.items.map(([,slug])=>getResource(slug)));setSets(rows);setError('');}catch(err){setError(err.message);}finally{setLoading(false);}};useEffect(()=>{load();},[pillar]);
 const total=sets.reduce((sum,row)=>sum+(row?.records?.length||0),0);const captions={Environmental:['Ledger entries','Active operational records','Carbon data is saved through the ledger.'],Social:['Impact records','Social programme records','Participation and diversity are tracked separately.'],Governance:['Control records','Governance work items','Open issues should be reviewed regularly.']}[pillar];
 return <section className={`module-workspace pillar-workspace pillar-${pillar.toLowerCase()}`}><div className="module-header"><div><span className="eyebrow">{config.eyebrow}</span><h1>{config.title}</h1><p>{config.subtitle}</p></div><button className="soft-btn" onClick={load}>{loading?'Refreshing…':'Refresh live data'}</button></div><section className="pillar-hero"><article><span className="eyebrow">{captions[0].toUpperCase()}</span><strong>{total}</strong><p>{captions[1]}</p></article><article><span className="eyebrow">WORKSPACE HEALTH</span><strong>{error?'Needs attention':'Live'}</strong><p>{error||captions[2]}</p></article><article><span className="eyebrow">NEXT STEP</span><strong>{loading?'Loading…':total?'Review records':'Add data'}</strong><p>{total?'Open an operational area below to act on live data.':'Start with the most relevant record type below.'}</p></article></section>{error&&<p className="form-error">{error}</p>}<section className="pillar-grid">{config.items.map(([label,,purpose],index)=>{const rows=sets[index]?.records||[];const fields=sets[index]?.fields||[];const preview=rows.slice(0,2);return <article className="data-surface pillar-card" key={label}><div className="panel-title"><div><span className="eyebrow">{purpose.toUpperCase()}</span><h3>{label}</h3></div><span className="count-chip">{rows.length}</span></div><p>{loading?'Loading saved records…':rows.length?`${rows.length} saved record${rows.length===1?'':'s'} in this operational area.`:'No saved records yet. Add the first one when your data is ready.'}</p>{preview.length?<div className="pillar-preview">{preview.map(row=><span key={row.id}>{row.display_name||row.name||fields.map(field=>valueText(row[field.name])).find(value=>value!=='—')||'Saved record'}</span>)}</div>:<div className="pillar-empty">No preview available</div>}<button className="text-button" onClick={()=>onNavigate(label)}>Open {label} <ArrowUpRight size={15}/></button></article>})}</section></section>;
}

function Dashboard({ onLogout, sessionUser }) {
  const [active,setActive] = useState('Overview');
  const [menu,setMenu] = useState(false);
  const [collapsed,setCollapsed] = useState(false);
  const [live,setLive] = useState(null);
  const [notice,setNotice] = useState('');
  const [showSearch,setShowSearch] = useState(false);
  const [searchQuery,setSearchQuery] = useState('');
  const [showNotifs,setShowNotifs] = useState(false);
  const [showProfile,setShowProfile] = useState(false);
  const searchRef = useRef(null);
  const { scrollY } = useScroll();
  const glowY = useSpring(useTransform(scrollY,[0,700],[0,150]),{stiffness:90,damping:25});

  useEffect(() => { getDashboard().then(setLive).catch(() => setLive(null)); }, []);
  useEffect(() => { window.dispatchEvent(new CustomEvent('ecosphere:module-change', { detail: active })); }, [active]);

  // ⌘K / Ctrl+K opens search
  useEffect(() => {
    const handler = e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setShowSearch(true); setShowNotifs(false); setShowProfile(false); }
      if (e.key === 'Escape') { setShowSearch(false); setShowNotifs(false); setShowProfile(false); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Focus search input when modal opens
  useEffect(() => { if (showSearch) setTimeout(() => searchRef.current?.focus(), 60); }, [showSearch]);

  // Close dropdowns on outside click
  useEffect(() => {
    if (!showNotifs && !showProfile) return;
    const handler = e => {
      if (!e.target.closest('.topbar-dropdown-wrap')) { setShowNotifs(false); setShowProfile(false); }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showNotifs, showProfile]);

  const shownKpis = [
    {label:'Environmental',score:live?.kpis?.environmental ?? 0,delta:'Calculated',color:'green'},
    {label:'Social',score:live?.kpis?.social ?? 0,delta:'Calculated',color:'blue'},
    {label:'Governance',score:live?.kpis?.governance ?? 0,delta:'Calculated',color:'violet'},
    {label:'Overall ESG',score:live?.kpis?.overall ?? 0,delta:'Calculated',color:'ink'},
  ];
  const counts = live?.counts || {carbon_transactions:0, environmental_goals:0, csr_activities:0, active_challenges:0, open_issues:0};
  const notify = message => { setNotice(message); window.setTimeout(() => setNotice(''), 3600); };
  const currentUser = live?.user || sessionUser;

  // Quick-navigate destinations shown in search
  const allDestinations = [
    {label:'Overview', icon:'📊', section:'Overview'},
    {label:'Carbon transactions', icon:'🌿', section:'Carbon transactions'},
    {label:'Emission factors', icon:'⚗️', section:'Emission factors'},
    {label:'Product ESG profiles', icon:'📦', section:'Product ESG profiles'},
    {label:'Environmental goals', icon:'🎯', section:'Environmental goals'},
    {label:'CSR activities', icon:'🤝', section:'CSR activities'},
    {label:'Employee participation', icon:'👥', section:'Employee participation'},
    {label:'Diversity dashboard', icon:'🌈', section:'Diversity dashboard'},
    {label:'Policies', icon:'📋', section:'Policies'},
    {label:'Policy acknowledgements', icon:'✅', section:'Policy acknowledgements'},
    {label:'Audits', icon:'🔍', section:'Audits'},
    {label:'Compliance issues', icon:'⚠️', section:'Compliance issues'},
    {label:'Challenges', icon:'🏆', section:'Challenges'},
    {label:'Participation', icon:'🎮', section:'Participation'},
    {label:'Badges & rewards', icon:'🎖️', section:'Badges & rewards'},
    {label:'Leaderboard', icon:'📈', section:'Leaderboard'},
    {label:'Reports', icon:'📄', section:'Reports'},
    {label:'Team access', icon:'👤', section:'Team access'},
    {label:'Settings', icon:'⚙️', section:'Settings'},
  ];
  const filteredSearch = searchQuery.trim()
    ? allDestinations.filter(d => d.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : allDestinations.slice(0, 8);

  const navigateTo = dest => { setActive(dest); setShowSearch(false); setSearchQuery(''); };

  // Dummy notifications (real-time would come from backend)
  const notifications = [
    {id:1, icon:'🏆', title:'Challenge approved', body:'Your "Plant a tree" submission earned 150 XP.', time:'2 min ago', unread:true},
    {id:2, icon:'📋', title:'Policy acknowledgement due', body:'3 employees have not signed the updated Data Policy.', time:'1 hour ago', unread:true},
    {id:3, icon:'⚠️', title:'Compliance issue raised', body:'A new issue was filed in the Governance module.', time:'3 hours ago', unread:false},
    {id:4, icon:'🌿', title:'Carbon ledger updated', body:'12 new transactions added by the admin team.', time:'Yesterday', unread:false},
  ];
  const unreadCount = notifications.filter(n => n.unread).length;

  const overview = <><motion.div className="welcome" initial={{opacity:0,y:16}} animate={{opacity:1,y:0}}><div><span className="eyebrow">LIVE ESG DASHBOARD</span><h1>Welcome, {currentUser?.name || '…'}.</h1><p>All values below are calculated from saved EcoSphere records.</p></div><button className="primary-btn" onClick={()=>setActive('Carbon transactions')}><Plus size={18}/> Log carbon data</button></motion.div><section className="score-grid">{shownKpis.map((k,i)=><ScoreCard item={k} index={i} key={k.label}/>)}</section><section className="bento primary-bento"><TrendCard count={counts.carbon_transactions} onOpen={()=>setActive('Carbon transactions')}/><PeopleCard counts={counts} onOpen={()=>setActive('CSR activities')}/></section><section className="bento lower-bento"><RankingCard ranking={live?.ranking || []}/><section className="panel next-card"><span className="eyebrow orange-text">GOVERNANCE</span><h3>{counts.open_issues} open compliance issue{counts.open_issues === 1 ? '' : 's'}</h3><p>This is the current count from your saved compliance records.</p><div><span className="date-chip"><ClipboardCheck size={17}/></span><button className="round-action" onClick={()=>setActive('Compliance issues')}><ArrowUpRight size={18}/></button></div></section></section></>;

  const sideW = collapsed ? 64 : 252;
  return (
    <div className="app-shell">
      <Sidebar active={active} setActive={setActive} open={menu} setOpen={setMenu} collapsed={collapsed} setCollapsed={setCollapsed} user={currentUser}/>
      <main className="workspace-main" style={{marginLeft:sideW,width:`calc(100% - ${sideW}px)`}}>
        <motion.div className="dashboard-glow" style={{y:glowY}}/>
        <header className="topbar">
          <button className="mobile-menu" onClick={()=>setMenu(true)}><Menu size={21}/></button>
          <div className="crumb"><span>EcoSphere</span><ChevronRight size={14}/><strong>{active}</strong></div>
          <div className="top-actions">
            {/* Search */}
            <button className="search" onClick={()=>{setShowSearch(true);setShowNotifs(false);setShowProfile(false);}}>
              <Search size={17}/><span>Search workspace</span><kbd>⌘ K</kbd>
            </button>

            {/* Notifications */}
            <div className="topbar-dropdown-wrap">
              <button className="icon-btn notification" onClick={()=>{setShowNotifs(v=>!v);setShowProfile(false);}}>
                <Bell size={19}/>
                {unreadCount > 0 && <i>{unreadCount}</i>}
              </button>
              <AnimatePresence>
                {showNotifs && (
                  <motion.div
                    className="topbar-dropdown notif-dropdown"
                    initial={{opacity:0,y:-8,scale:.97}}
                    animate={{opacity:1,y:0,scale:1}}
                    exit={{opacity:0,y:-8,scale:.97}}
                    transition={{type:'spring',bounce:0,duration:0.28}}
                  >
                    <div className="td-header">
                      <strong>Notifications</strong>
                      {unreadCount > 0 && <span className="td-badge">{unreadCount} new</span>}
                    </div>
                    <div className="td-list">
                      {notifications.map(n => (
                        <div key={n.id} className={`td-notif-row ${n.unread ? 'unread' : ''}`}>
                          <span className="td-notif-icon">{n.icon}</span>
                          <div className="td-notif-body">
                            <strong>{n.title}</strong>
                            <span>{n.body}</span>
                            <small>{n.time}</small>
                          </div>
                          {n.unread && <div className="td-unread-dot"/>}
                        </div>
                      ))}
                    </div>
                    <div className="td-footer">
                      <button onClick={()=>{notify('All notifications marked as read.');setShowNotifs(false);}}>Mark all as read</button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Avatar / Profile */}
            <div className="topbar-dropdown-wrap">
              <button className="top-avatar" onClick={()=>{setShowProfile(v=>!v);setShowNotifs(false);}}>
                {currentUser?.initials || '—'}
              </button>
              <AnimatePresence>
                {showProfile && (
                  <motion.div
                    className="topbar-dropdown profile-dropdown"
                    initial={{opacity:0,y:-8,scale:.97}}
                    animate={{opacity:1,y:0,scale:1}}
                    exit={{opacity:0,y:-8,scale:.97}}
                    transition={{type:'spring',bounce:0,duration:0.28}}
                  >
                    <div className="td-profile-head">
                      <div className="td-avatar-lg">{currentUser?.initials || '—'}</div>
                      <div>
                        <strong>{currentUser?.name || 'EcoSphere user'}</strong>
                        <span>{currentUser?.email || ''}</span>
                        <span className="td-role-pill">{currentUser?.role || 'Member'}</span>
                      </div>
                    </div>
                    <div className="td-divider"/>
                    <div className="td-menu">
                      <button onClick={()=>{setActive('Overview');setShowProfile(false);}}>
                        <Gauge size={15}/> Dashboard
                      </button>
                      <button onClick={()=>{setActive('Settings');setShowProfile(false);}}>
                        <Settings size={15}/> Settings
                      </button>
                      {currentUser?.role === 'ESG Manager' && (
                        <button onClick={()=>{setActive('Team access');setShowProfile(false);}}>
                          <Users size={15}/> Team access
                        </button>
                      )}
                    </div>
                    <div className="td-divider"/>
                    <div className="td-menu">
                      <button className="td-signout" onClick={()=>{setShowProfile(false);onLogout();}}>
                        <LogOut size={15}/> Sign out
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <button className="logout" onClick={onLogout} title="Sign out"><LogOut size={17}/></button>
          </div>
        </header>

        {/* Global search modal */}
        <AnimatePresence>
          {showSearch && (
            <motion.div
              className="search-scrim"
              initial={{opacity:0}}
              animate={{opacity:1}}
              exit={{opacity:0}}
              transition={{duration:0.18}}
              onClick={e=>{ if(e.target===e.currentTarget){setShowSearch(false);setSearchQuery('');} }}
            >
              <motion.div
                className="search-modal"
                initial={{opacity:0,y:-20,scale:.97}}
                animate={{opacity:1,y:0,scale:1}}
                exit={{opacity:0,y:-20,scale:.97}}
                transition={{type:'spring',bounce:0,duration:0.32}}
              >
                <div className="search-input-row">
                  <Search size={18} className="search-icon"/>
                  <input
                    ref={searchRef}
                    className="search-input"
                    placeholder="Search workspace…"
                    value={searchQuery}
                    onChange={e=>setSearchQuery(e.target.value)}
                    onKeyDown={e=>{ if(e.key==='Enter' && filteredSearch.length) navigateTo(filteredSearch[0].section); }}
                  />
                  <kbd className="search-esc" onClick={()=>{setShowSearch(false);setSearchQuery('');}}>Esc</kbd>
                </div>
                <div className="search-results">
                  {filteredSearch.length ? filteredSearch.map((d,i) => (
                    <button key={d.label} className="search-result-row" onClick={()=>navigateTo(d.section)}>
                      <span className="sr-icon">{d.icon}</span>
                      <span className="sr-label">{d.label}</span>
                      <span className="sr-hint">Go to workspace</span>
                    </button>
                  )) : (
                    <div className="search-empty">No workspace matches "{searchQuery}"</div>
                  )}
                </div>
                <div className="search-footer">
                  <span>↑↓ navigate</span><span>↵ open</span><span>Esc close</span>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="content">
          {active === 'Overview' ? overview
            : active === 'Reports' ? <ReportsWorkspace onNotify={notify}/>
            : active === 'Team access' ? <TeamAccess onNotify={notify}/>
            : active === 'Settings' ? <SettingsWorkspace onNotify={notify}/>
            : active === 'Governance' ? <GovernanceOverview onNavigate={setActive}/>
            : ['Environmental','Social'].includes(active) ? <PillarWorkspace pillar={active} onNavigate={setActive}/>
            : ['Gamification','Challenges','Participation','Badges & rewards','Leaderboard'].includes(active) ? <PlayableGamificationWorkspace onNotify={notify} active={active}/>
            : <ModuleWorkspace label={active} onNotify={notify}/>}
        </div>
        <AiAssistant onNavigate={setActive}/>
        {notice && <motion.div className="toast" initial={{opacity:0,y:14}} animate={{opacity:1,y:0}} exit={{opacity:1,y:0}}>{notice}</motion.div>}
      </main>
    </div>
  );
}



function ChallengePlayer({ challenge, onClose, onComplete }) {
 const [answers,setAnswers]=useState({}); const [items,setItems]=useState([]); const [file,setFile]=useState(null); const [error,setError]=useState(''); const [saving,setSaving]=useState(false); const config=challenge.game_config||{};
 const submit=async event=>{event.preventDefault();setSaving(true);try{let payload={};if(['quiz','scenario'].includes(challenge.challenge_type))payload={answers};else if(challenge.challenge_type==='checklist')payload={completed_items:items};else if(challenge.challenge_type==='photo'){if(!file)throw new Error('Choose a clear JPG or PNG photo first.');payload={proof:file.data,filename:file.name};}const result=await onComplete(challenge.participation.id,payload);if(result)onClose();}catch(err){setError(err.message);}finally{setSaving(false);}};
 const readFile=event=>{const selected=event.target.files?.[0];if(!selected)return;if(!['image/jpeg','image/png'].includes(selected.type)||selected.size>5*1024*1024){setError('Use a JPG or PNG photo up to 5 MB.');return;}const reader=new FileReader();reader.onload=()=>setFile({name:selected.name,data:String(reader.result).split(',')[1]});reader.readAsDataURL(selected);};
 return <div className="modal-scrim"><motion.form className="record-modal game-player" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow orange-text">PLAY CHALLENGE</span><h2>{challenge.name}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div>{['quiz','scenario'].includes(challenge.challenge_type)&&<div className="game-questions">{(config.questions||[]).map((question,index)=><fieldset key={index}><legend>{index+1}. {question.prompt}</legend>{(question.options||[]).map((option,optionIndex)=><label key={optionIndex} className="choice"><input required name={`q-${index}`} type="radio" onChange={()=>setAnswers({...answers,[index]:optionIndex})}/>{option}</label>)}</fieldset>)}</div>}{challenge.challenge_type==='checklist'&&<div className="game-questions">{(config.items||[]).map((item,index)=><label className="choice" key={index}><input type="checkbox" onChange={event=>setItems(event.target.checked?[...items,index]:items.filter(value=>value!==index))}/>{item}</label>)}</div>}{challenge.challenge_type==='photo'&&<div className="photo-proof"><p>Upload one clear photo that visibly includes a real living plant. AI verification is used when configured; otherwise an administrator reviews it.</p><input type="file" accept="image/jpeg,image/png" onChange={readFile}/>{file&&<strong>{file.name} ready for review</strong>}</div>}{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button className="cancel-btn" type="button" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Submitting…':challenge.challenge_type==='photo'?'Submit photo':'Finish challenge'} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function ParticipationWorkspace({ data, onNotify }) {
 const rows=data?.is_manager?(data.activity||[]):(data?.challenges||[]).filter(row=>row.participation).map(row=>({employee:'You',challenge:row.name,state:row.participation.state,progress:row.participation.progress,xp:row.participation.state==='approved'?row.xp_value:0,eligibility:row.participation.eligibility_status}));
 return <section className="module-workspace module-gamification participation-workspace"><div className="module-header"><div><span className="eyebrow orange-text">PARTICIPATION WORKFLOW</span><h1>{data?.is_manager?'Participation review':'My challenge progress'}</h1><p>{data?.is_manager?'Track every employee attempt, evidence status, eligibility decision, and approved XP in one auditable queue.':'Follow your active challenge attempts and see when your progress is approved.'}</p></div></div><section className="module-stat-strip"><article><span>Attempts</span><strong>{rows.length}</strong></article><article><span>Awaiting review</span><strong>{rows.filter(row=>row.state==='under_review').length}</strong></article><article><span>Approved XP</span><strong>{rows.reduce((total,row)=>total+(Number(row.xp)||0),0)}</strong></article></section><section className="data-surface participation-surface"><div className="panel-title"><div><span className="eyebrow orange-text">LIVE PARTICIPATION</span><h3>{data?.is_manager?'Employee activity':'Your activity'}</h3></div></div>{rows.length?<div className="data-table-wrap"><table><thead><tr><th>Employee</th><th>Challenge</th><th>Status</th><th>Progress</th><th>Eligibility</th><th>Approved XP</th></tr></thead><tbody>{rows.map((row,index)=><tr key={`${row.employee}-${row.challenge}-${index}`}><td>{row.employee}</td><td>{row.challenge}</td><td><span className={`workflow-pill ${row.state}`}>{String(row.state).replace('_',' ')}</span></td><td>{row.progress}%</td><td><span className={`workflow-pill ${row.eligibility}`}>{String(row.eligibility||'pending').replace('_',' ')}</span></td><td>{row.xp} XP</td></tr>)}</tbody></table></div>:<div className="empty-state"><ClipboardCheck size={25}/><strong>No participation yet</strong><span>{data?.is_manager?'Published challenges will appear here as employees join them.':'Join an active challenge from Challenges to start your progress.'}</span></div>}</section></section>;
}

function CatalogueModal({ kind, onClose, onSaved }) {
 const [saving,setSaving]=useState(false);const [error,setError]=useState('');const isBadge=kind==='badge';
 const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setSaving(true);setError('');try{const values=isBadge?{name:form.get('name'),description:form.get('description'),minimum_xp:form.get('minimum_xp'),minimum_challenges:form.get('minimum_challenges')}:{name:form.get('name'),description:form.get('description'),points_required:form.get('points_required'),stock:form.get('stock'),active:true};await createResource(isBadge?'badges':'rewards',values);onSaved(`${isBadge?'Badge':'Reward'} added to the recognition catalogue.`);}catch(err){setError(err.message);setSaving(false);}};
 return <div className="modal-scrim"><motion.form className="record-modal catalogue-modal" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow orange-text">RECOGNITION SETUP</span><h2>Add {isBadge?'badge':'reward'}</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><p className="panel-copy">{isBadge?'EcoSphere awards this automatically when an employee reaches the rule below.':'Employees can see this benefit once it is active in your catalogue.'}</p><div className="form-grid"><label>Name<input name="name" required placeholder={isBadge?'e.g. Climate Champion':'e.g. Reusable bottle voucher'}/></label><label>{isBadge?'Minimum approved XP':'XP needed to redeem'}<input name={isBadge?'minimum_xp':'points_required'} type="number" min="0" required defaultValue="100"/></label>{isBadge?<label>Minimum completed challenges<input name="minimum_challenges" type="number" min="0" required defaultValue="1"/></label>:<label>Available stock<input name="stock" type="number" min="0" required defaultValue="10"/></label>}<label className="full-form-field">Description<textarea name="description" placeholder="Explain what the employee earns and why."/></label></div>{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving…':`Add ${isBadge?'badge':'reward'}`} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function RewardsWorkspace({ data, onRefresh, onNotify }) {
 const badges=data?.badges||[]; const rewards=data?.rewards||[];const [modal,setModal]=useState(null);
 const saved=message=>{setModal(null);onRefresh();onNotify(message);};
 return <section className="module-workspace module-gamification rewards-workspace"><div className="module-header"><div><span className="eyebrow orange-text">RECOGNITION CATALOGUE</span><h1>Badges & rewards</h1><p>{data?.is_manager?'Create the achievement rules and benefits available in this enterprise. Badges are automatically awarded from verified XP.':'See your recognition progress and the rewards available as you earn approved XP.'}</p></div>{data?.is_manager&&<div className="header-actions"><button className="soft-btn" onClick={()=>setModal('reward')}><Plus size={15}/> Add reward</button><button className="primary-btn" onClick={()=>setModal('badge')}><Trophy size={16}/> Add badge</button></div>}</div><section className="rewards-layout"><article className="data-surface rewards-section"><div className="panel-title"><div><span className="eyebrow orange-text">BADGES</span><h3>{data?.is_manager?'Recognition milestones':'Your badge journey'}</h3></div></div><div className="reward-grid">{badges.map(badge=><article className={`reward-card ${badge.unlocked?'earned':''}`} key={badge.id}><Trophy size={20}/><div><strong>{badge.name}</strong><p>{badge.description||'Recognition badge'}</p></div><span>{badge.unlocked?'Earned':`${badge.minimum_xp} XP`}</span></article>)}{!badges.length&&<div className="panel-empty">No badges have been configured by the administrator.</div>}</div></article><article className="data-surface rewards-section"><div className="panel-title"><div><span className="eyebrow orange-text">REWARDS</span><h3>Redeemable rewards</h3></div></div><div className="reward-grid">{rewards.map(reward=><article className="reward-card" key={reward.id}><Zap size={20}/><div><strong>{reward.name}</strong><p>{reward.description||'Enterprise reward'}</p></div><span>{reward.points_required} XP</span><small>{reward.stock > 0 ? `${reward.stock} available` : 'Currently unavailable'}</small></article>)}{!rewards.length&&<div className="panel-empty">No rewards are currently available.</div>}</div></article></section>{modal&&<CatalogueModal kind={modal} onClose={()=>setModal(null)} onSaved={saved}/>}</section>;
}

function ChallengeBuilder({ onClose, onSaved }) {
 const [type,setType]=useState('quiz');const [questions,setQuestions]=useState([{prompt:'',options:['',''],answer:0}]);const [items,setItems]=useState(['']);const [saving,setSaving]=useState(false);const [error,setError]=useState('');
 const setQuestion=(index,changes)=>setQuestions(current=>current.map((question,position)=>position===index?{...question,...changes}:question));
 const setOption=(questionIndex,optionIndex,value)=>setQuestion(questionIndex,{options:questions[questionIndex].options.map((option,position)=>position===optionIndex?value:option)});
 const submit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);let game_config={};if(['quiz','scenario'].includes(type))game_config={pass_score:Number(form.get('pass_score')),questions};if(type==='checklist')game_config={items};setSaving(true);setError('');try{await createChallenge({name:form.get('name'),description:form.get('description'),xp_value:Number(form.get('xp_value')),difficulty:form.get('difficulty'),deadline:form.get('deadline'),state:form.get('state'),challenge_type:type,game_config});onSaved('Custom challenge saved. Employees can see it when you publish it as active.');}catch(err){setError(err.message);setSaving(false);}};
 return <div className="modal-scrim"><motion.form className="record-modal challenge-builder" onSubmit={submit} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}} transition={{type:'spring',stiffness:260,damping:25}}><div className="modal-heading"><div><span className="eyebrow orange-text">CUSTOM CHALLENGE</span><h2>Build a playable challenge</h2></div><button type="button" className="icon-btn" onClick={onClose}><X size={18}/></button></div><div className="form-grid"><label>Challenge name<input name="name" required placeholder="e.g. Waste Wise Quiz"/></label><label>Challenge type<select value={type} onChange={event=>setType(event.target.value)}><option value="quiz">Knowledge quiz</option><option value="scenario">Decision scenario</option><option value="checklist">Action checklist</option><option value="photo">Photo evidence</option><option value="action">Manager-reviewed action</option></select></label><label>XP reward<input name="xp_value" required type="number" min="1" defaultValue="100"/></label><label>Difficulty<select name="difficulty" defaultValue="medium"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label><label>Deadline<input name="deadline" type="date" required/></label><label>Visibility<select name="state" defaultValue="active"><option value="active">Active — employees can play</option><option value="draft">Draft — administrator only</option></select></label><label className="full-form-field">Employee instructions<textarea name="description" required placeholder="Explain exactly what employees need to do to earn XP."/></label></div>{['quiz','scenario'].includes(type)&&<section className="builder-section"><div className="builder-heading"><div><span className="eyebrow orange-text">QUESTION SET</span><h3>{type==='quiz'?'Quiz questions':'Scenario choices'}</h3></div><label>Pass score<input name="pass_score" type="number" min="1" max="100" defaultValue="80"/>%</label></div>{questions.map((question,questionIndex)=><article className="question-editor" key={questionIndex}><div className="question-editor-head"><strong>Question {questionIndex+1}</strong>{questions.length>1&&<button type="button" className="text-button" onClick={()=>setQuestions(current=>current.filter((_,index)=>index!==questionIndex))}>Remove</button>}</div><input value={question.prompt} onChange={event=>setQuestion(questionIndex,{prompt:event.target.value})} placeholder="Write the question" required/>{question.options.map((option,optionIndex)=><label className="option-editor" key={optionIndex}><input type="radio" checked={Number(question.answer)===optionIndex} onChange={()=>setQuestion(questionIndex,{answer:optionIndex})} name={`correct-${questionIndex}`} aria-label={`Correct answer ${optionIndex+1}`}/><input value={option} onChange={event=>setOption(questionIndex,optionIndex,event.target.value)} placeholder={`Option ${optionIndex+1}`} required/>{question.options.length>2&&<button type="button" className="remove-option" onClick={()=>setQuestion(questionIndex,{options:question.options.filter((_,index)=>index!==optionIndex),answer:Math.min(Number(question.answer),question.options.length-2)})}><X size={13}/></button>}</label>)}{question.options.length<6&&<button type="button" className="text-button" onClick={()=>setQuestion(questionIndex,{options:[...question.options,'']})}><Plus size={14}/> Add option</button>}</article>)}{questions.length<12&&<button type="button" className="soft-btn" onClick={()=>setQuestions(current=>[...current,{prompt:'',options:['',''],answer:0}])}><Plus size={14}/> Add question</button>}</section>}{type==='checklist'&&<section className="builder-section"><div className="builder-heading"><div><span className="eyebrow orange-text">ACTION LIST</span><h3>Required checklist actions</h3></div></div>{items.map((item,index)=><label className="checklist-editor" key={index}><span>{index+1}</span><input value={item} required onChange={event=>setItems(current=>current.map((value,position)=>position===index?event.target.value:value))} placeholder="Describe a required action"/>{items.length>1&&<button type="button" className="remove-option" onClick={()=>setItems(current=>current.filter((_,position)=>position!==index))}><X size={13}/></button>}</label>)}{items.length<12&&<button type="button" className="soft-btn" onClick={()=>setItems(current=>[...current,''])}><Plus size={14}/> Add action</button>}</section>}{type==='photo'&&<div className="builder-note"><Leaf size={16}/><span>Employees must upload a clear JPG or PNG. The required subject is reviewed by secure vision when configured, otherwise by an administrator.</span></div>}{type==='action'&&<div className="builder-note"><ClipboardCheck size={16}/><span>Employees submit their completion for administrator review before XP is awarded.</span></div>}{error&&<p className="form-error">{error}</p>}<div className="modal-actions"><button type="button" className="cancel-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving…':'Save challenge'} <ArrowUpRight size={16}/></button></div></motion.form></div>;
}

function LeaderboardWorkspace({ data }) {
 const rows=data?.leaderboard||[]; const participantCount=(data?.activity||[]).filter(row=>row.state==='approved').length;
 return <section className="module-workspace module-gamification leaderboard-workspace"><div className="module-header"><div><span className="eyebrow orange-text">TEAM MOMENTUM</span><h1>Leaderboard</h1><p>Rankings are calculated only from approved challenge XP, so every position reflects a verified contribution.</p></div></div><section className="leaderboard-hero"><div><span className="eyebrow">APPROVED PERFORMANCE</span><strong>{rows.length}</strong><p>ranked employee{rows.length===1?'':'s'}</p></div><div><span className="eyebrow">VERIFIED COMPLETIONS</span><strong>{participantCount}</strong><p>approved attempts</p></div><div><span className="eyebrow">TOP SCORE</span><strong>{rows[0]?.xp||0}</strong><p>approved XP</p></div></section><section className="data-surface leaderboard-surface"><div className="panel-title"><div><span className="eyebrow orange-text">RANKINGS</span><h3>Enterprise leaderboard</h3></div></div>{rows.length?<ol className="leaderboard-rankings">{rows.map(row=><li key={`${row.rank}-${row.name}`}><b>#{row.rank}</b><div className="ranking-avatar">{row.name.split(' ').map(part=>part[0]).join('').slice(0,2)}</div><strong>{row.name}</strong><span>{row.xp} XP</span></li>)}</ol>:<div className="empty-state"><Trophy size={25}/><strong>No ranking yet</strong><span>Approved challenge completions will create the enterprise leaderboard.</span></div>}</section></section>;
}

function PlayableGamificationWorkspace({ onNotify, active }) {
 const [data,setData]=useState(null);const [filter,setFilter]=useState('active');const [playing,setPlaying]=useState(null);const [template,setTemplate]=useState(null);const [creator,setCreator]=useState(false);const [error,setError]=useState('');const [busy,setBusy]=useState(null);const [subView,setSubView]=useState(active);const plain=value=>String(value||'').replace(/<[^>]*>/g,'').trim();
 const load=async()=>{try{setData(await getGamification());setError('');}catch(err){setError(err.message);}};useEffect(()=>{load();},[]);
 useEffect(()=>{const refresh=()=>load();window.addEventListener('ecosphere:gamification-changed',refresh);return()=>window.removeEventListener('ecosphere:gamification-changed',refresh);},[]);
 useEffect(()=>{setSubView(active);},[active]);
 useEffect(()=>{const showDetails=event=>{const card=event.target.closest('.challenge-card');if(!card||event.target.closest('button'))return;const name=card.querySelector('h3')?.textContent;const challenge=(data?.challenges||[]).find(row=>row.name===name);if(challenge)window.dispatchEvent(new CustomEvent('ecosphere:challenge-details',{detail:challenge}));};document.addEventListener('click',showDetails);return()=>document.removeEventListener('click',showDetails);},[data]);
 const join=async id=>{setBusy(id);try{const result=await joinChallenge(id);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(null);}};
 const complete=async(id,payload)=>{setBusy(id);try{const result=await playChallenge(id,payload);await load();onNotify(result.message);return true;}catch(err){setError(err.message);return false;}finally{setBusy(null);}};
 const publish=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);setBusy('publish');try{const result=await publishChallengeTemplate(template.id,{name:form.get('name'),deadline:form.get('deadline'),state:form.get('state')});setTemplate(null);await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(null);}};
 const review=async(id,approved)=>{setBusy(id);try{const result=await reviewChallenge(id,approved,approved?'Evidence verified by administrator.':'Not eligible for promotion: no real plant or valid required evidence was visible.');await load();onNotify(result.message);}catch(err){setError(err.message);}finally{setBusy(null);}};
 const rows=(data?.challenges||[]).filter(row=>filter==='all'||row.state===filter);
 if(subView==='Participation')return <ParticipationWorkspace data={data} onNotify={onNotify}/>;
 if(subView==='Badges & rewards')return <RewardsWorkspace data={data} onRefresh={load} onNotify={onNotify}/>;
 if(subView==='Leaderboard')return <LeaderboardWorkspace data={data}/>;
 return <section className="module-workspace module-gamification gamification-workspace"><div className="module-header"><div><span className="eyebrow orange-text">GAMIFICATION WORKSPACE</span><h1>{data?.is_manager?'Challenge studio':'Play for positive impact'}</h1><p>{data?.is_manager?'Choose a professional template, publish it, and review verified outcomes.':'Play active sustainability challenges and earn approved XP.'}</p></div></div>{data?.is_manager&&<section className="template-library"><div className="panel-title"><div><span className="eyebrow orange-text">CHALLENGE TEMPLATES</span><h3>Publish a ready-to-play challenge</h3></div></div><div className="template-grid">{(data?.templates||[]).map(row=><button key={row.id} onClick={()=>setTemplate(row)}><span>{row.challenge_type}</span><strong>{row.name}</strong><small>{row.xp_value} XP · {row.difficulty}</small></button>)}</div></section>}<div className="game-tabs">{[['active','Active'],['draft','Draft'],['all','All challenges']].filter(([key])=>data?.is_manager||key==='active').map(([key,label])=><button className={filter===key?'selected':''} onClick={()=>setFilter(key)} key={key}>{label}</button>)}</div>{error&&<p className="form-error">{error}</p>}<section className="challenge-grid">{rows.map(row=><article className="challenge-card" key={row.id}><div className="challenge-top"><span className={`state-pill ${row.state}`}>{row.challenge_type.replace('_',' ')}</span><span className="xp-chip">{row.xp_value} XP</span></div><h3>{row.name}</h3><p>{plain(row.description)}</p><div className="challenge-meta"><span>{row.difficulty}</span><span>Due {row.deadline}</span><span>{row.participants} joined</span></div>{data?.is_manager?<div className="manager-hint">{row.state==='active'?'Live in employee portal':'Draft — not visible to employees'}</div>:row.participation?<button className="challenge-join" disabled={busy===row.participation.id||row.participation.state==='approved'||row.participation.state==='under_review'} onClick={()=>setPlaying(row)}>{row.participation.state==='approved'?'XP awarded':row.participation.state==='under_review'?'Awaiting review':row.challenge_type==='photo'?'Upload plant photo':'Play challenge'} <ArrowUpRight size={15}/></button>:<button className="challenge-join" disabled={busy===row.id||!data?.can_join} onClick={()=>join(row.id)}>{busy===row.id?'Joining…':'Participate'} <ArrowUpRight size={15}/></button>}</article>)}{!rows.length&&<div className="empty-state game-empty"><Trophy size={24}/><strong>No challenges here yet</strong><span>{data?.is_manager?'Publish one of the templates above.':'Ask your administrator to publish a challenge.'}</span></div>}</section>{data?.is_manager&&<section className="review-panel data-surface"><div className="panel-title"><div><span className="eyebrow orange-text">EVIDENCE REVIEW</span><h3>Plant photo submissions</h3></div></div>{(data?.reviews||[]).length?(data.reviews||[]).map(row=><div className="review-row" key={row.id}>{row.proof&&<img src={`data:image/jpeg;base64,${row.proof}`} alt="Submitted challenge evidence"/>}<div><strong>{row.employee}</strong><span>{row.challenge}</span><p>{row.reason||'Awaiting eligibility review.'}</p></div><button className="soft-btn" disabled={busy===row.id} onClick={()=>review(row.id,true)}>Approve XP</button><button className="danger-btn" disabled={busy===row.id} onClick={()=>review(row.id,false)}>Not eligible</button></div>):<p className="panel-empty">No evidence is awaiting review.</p>}</section>}<section className="game-lower"><article className="data-surface badge-panel"><div className="panel-title"><div><span className="eyebrow orange-text">BADGE GALLERY</span><h3>{data?.is_manager?'Recognition badges':'Your badge progress'}</h3></div></div><div className="badge-grid">{(data?.badges||[]).map(badge=><div className={`badge-tile ${badge.unlocked?'unlocked':''}`} key={badge.id}><Trophy size={16}/><div><strong>{badge.name}</strong><span>{badge.unlocked?'Unlocked':`${badge.minimum_xp} XP needed`}</span></div></div>)}</div></article><article className="data-surface leaderboard-panel"><div className="panel-title"><div><span className="eyebrow orange-text">LEADERBOARD</span><h3>Team momentum</h3></div></div>{(data?.leaderboard||[]).map(row=><div className="leader-list" key={`${row.rank}-${row.name}`}><div><b>#{row.rank}</b><strong>{row.name}</strong><span>{row.xp} XP</span></div></div>)}</article></section>{playing&&<ChallengePlayer challenge={playing} onClose={()=>setPlaying(null)} onComplete={complete}/>} {template&&<div className="modal-scrim"><motion.form className="record-modal" onSubmit={publish} initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow orange-text">TEMPLATE</span><h2>Publish {template.name}</h2></div><button type="button" className="icon-btn" onClick={()=>setTemplate(null)}><X size={18}/></button></div><div className="form-grid"><label>Challenge name<input name="name" defaultValue={template.name} required/></label><label>Deadline<input name="deadline" type="date" required/></label><label>Visibility<select name="state" defaultValue="active"><option value="active">Active — employees can play</option><option value="draft">Draft — admin only</option></select></label><p className="panel-copy">{plain(template.description)} · {template.xp_value} XP</p></div><div className="modal-actions"><button className="cancel-btn" type="button" onClick={()=>setTemplate(null)}>Cancel</button><button className="primary-btn" disabled={busy==='publish'}>{busy==='publish'?'Publishing…':'Publish challenge'} <ArrowUpRight size={16}/></button></div></motion.form></div>}</section>;
}

function ChallengeDetailOverlay(){const [challenge,setChallenge]=useState(null);useEffect(()=>{const open=event=>setChallenge(event.detail);window.addEventListener('ecosphere:challenge-details',open);return()=>window.removeEventListener('ecosphere:challenge-details',open);},[]);if(!challenge)return null;const config=challenge.game_config||{};const type={quiz:'Knowledge quiz',scenario:'Decision scenario',checklist:'Action checklist',photo:'Verified photo evidence',action:'Action submission'}[challenge.challenge_type]||'Challenge';const howItWorks=challenge.challenge_type==='photo'?'Upload a clear JPG or PNG photo that visibly includes a real living plant. If secure vision is configured, EcoSphere checks eligibility; otherwise an administrator reviews the photo before XP is awarded.':challenge.challenge_type==='checklist'?'Complete every listed action, then submit the checklist. XP is granted only after all actions are complete.':['quiz','scenario'].includes(challenge.challenge_type)?`Answer all ${(config.questions||[]).length} questions. You need ${config.pass_score||80}% or higher to earn XP.`:'Join the challenge, submit the requested action, and wait for administrator approval.';return <div className="modal-scrim"><motion.section className="record-modal challenge-detail" initial={{opacity:0,scale:.96,y:16}} animate={{opacity:1,scale:1,y:0}}><div className="modal-heading"><div><span className="eyebrow orange-text">CHALLENGE GUIDE</span><h2>{challenge.name}</h2></div><button className="icon-btn" onClick={()=>setChallenge(null)}><X size={18}/></button></div><div className="detail-hero"><span className="xp-chip">{challenge.xp_value} XP</span><span className={`state-pill ${challenge.state}`}>{type}</span></div><p className="detail-description">{String(challenge.description||'').replace(/<[^>]*>/g,'').trim()}</p><div className="detail-grid"><article><span>How it works</span><strong>{howItWorks}</strong></article><article><span>Deadline</span><strong>{challenge.deadline||'No deadline set'}</strong></article><article><span>Difficulty</span><strong>{challenge.difficulty}</strong></article><article><span>Reward</span><strong>{challenge.xp_value} approved XP</strong></article></div>{challenge.challenge_type==='checklist'&&<div className="detail-rules"><h3>Required actions</h3>{(config.items||[]).map((item,index)=><p key={index}>{index+1}. {item}</p>)}</div>}{['quiz','scenario'].includes(challenge.challenge_type)&&<div className="detail-rules"><h3>Before you play</h3><p>You will answer {(config.questions||[]).length} questions. Correct answers are revealed only after submission to keep the challenge fair.</p></div>}{challenge.challenge_type==='photo'&&<div className="detail-rules"><h3>Eligibility rules</h3><p>The image must be clear, original, and visibly contain a real living plant. If no plant is detected or an administrator cannot verify it, the submission is marked <strong>Not eligible for promotion</strong> and earns no XP.</p></div>}<div className="modal-actions"><button className="primary-btn" onClick={()=>setChallenge(null)}>Got it <ArrowUpRight size={16}/></button></div></motion.section></div>}

function GamificationAdminQuickActions(){const [active,setActive]=useState('');const [manager,setManager]=useState(false);const [creator,setCreator]=useState(false);const [notice,setNotice]=useState('');useEffect(()=>{const change=event=>setActive(event.detail);window.addEventListener('ecosphere:module-change',change);return()=>window.removeEventListener('ecosphere:module-change',change);},[]);useEffect(()=>{if(!['Gamification','Challenges'].includes(active))return;getGamification().then(data=>setManager(Boolean(data.is_manager))).catch(()=>setManager(false));},[active]);if(!manager||!['Gamification','Challenges'].includes(active))return null;const saved=message=>{setCreator(false);window.dispatchEvent(new CustomEvent('ecosphere:gamification-changed'));setNotice(message);window.setTimeout(()=>setNotice(''),3600);};return <><button className="gamification-quick-add primary-btn" onClick={()=>setCreator(true)}><Plus size={16}/> Create challenge</button>{creator&&<ChallengeBuilder onClose={()=>setCreator(false)} onSaved={saved}/>} {notice&&<div className="toast">{notice}</div>}</>}

function ChallengeAdminSetupPanel(){const [challenge,setChallenge]=useState(null);useEffect(()=>{const open=event=>{const config=event.detail?.game_config||{};if((config.questions||[]).some(question=>Object.prototype.hasOwnProperty.call(question,'answer'))||(config.items||[]).length)setChallenge(event.detail);else setChallenge(null);};const close=event=>{if(event.target.closest('.challenge-detail button'))setChallenge(null);};window.addEventListener('ecosphere:challenge-details',open);document.addEventListener('click',close);return()=>{window.removeEventListener('ecosphere:challenge-details',open);document.removeEventListener('click',close);};},[]);if(!challenge)return null;const config=challenge.game_config||{};return <aside className="challenge-setup-panel"><span className="eyebrow orange-text">ADMIN SETUP</span><h3>Saved playable rules</h3>{(config.questions||[]).map((question,index)=><article key={index}><strong>{index+1}. {question.prompt}</strong>{(question.options||[]).map((option,optionIndex)=><span className={Number(question.answer)===optionIndex?'correct':''} key={optionIndex}>{String.fromCharCode(65+optionIndex)}. {option}{Number(question.answer)===optionIndex?' · Correct':''}</span>)}</article>)}{(config.items||[]).map((item,index)=><article key={index}><strong>{index+1}. {item}</strong></article>)}{config.pass_score&&<p>Pass score: <b>{config.pass_score}%</b></p>}</aside>}

function ChallengeRosterPanel(){const [challenge,setChallenge]=useState(null);useEffect(()=>{const open=event=>setChallenge(event.detail);const close=event=>{if(event.target.closest('.challenge-detail button'))setChallenge(null);};window.addEventListener('ecosphere:challenge-details',open);document.addEventListener('click',close);return()=>{window.removeEventListener('ecosphere:challenge-details',open);document.removeEventListener('click',close);};},[]);if(!challenge||!Array.isArray(challenge.participant_details))return null;const rows=challenge.participant_details;return <aside className="challenge-roster"><div><span className="eyebrow orange-text">ADMIN PARTICIPATION</span><h3>{rows.length} employee{rows.length===1?'':'s'} tried this</h3></div>{rows.length?rows.map((row,index)=><article key={`${row.employee}-${index}`}><div><strong>{row.employee}</strong><span>{row.state.replace('_',' ')} · {row.progress}% progress</span>{row.reason&&<small>{row.reason}</small>}</div><b>{row.xp} XP</b><em className={row.eligibility}>{row.eligibility.replace('_',' ')}</em></article>):<p>No employee has joined this published challenge yet.</p>}</aside>}

export default function App() {
  const viewForPath = () => {
    if (window.location.pathname === '/dashboard') return 'app';
    if (window.location.pathname === '/signin' || window.location.pathname === '/signup') return 'login';
    return 'landing';
  };
  const [view, setView] = useState(viewForPath);
  const [sessionUser, setSessionUser] = useState(() => {
    try {
      return JSON.parse(window.localStorage.getItem('ecosphere:session-user')) || null;
    } catch {
      return null;
    }
  });
  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setView(viewForPath());
  };
  const openDashboard = profile => {
    if (profile) {
      setSessionUser(profile);
      window.localStorage.setItem('ecosphere:session-user', JSON.stringify(profile));
    }
    navigate('/dashboard');
  };
  const logout = () => {
    window.localStorage.removeItem('ecosphere:session-user');
    setSessionUser(null);
    navigate('/');
  };
  useEffect(() => {
    const handleNavigation = () => setView(viewForPath());
    const expireSession = () => {
      window.localStorage.removeItem('ecosphere:session-user');
      setSessionUser(null);
      window.history.pushState({}, '', '/signin');
      setView('login');
    };
    window.addEventListener('popstate', handleNavigation);
    window.addEventListener('ecosphere:session-expired', expireSession);
    return () => {
      window.removeEventListener('popstate', handleNavigation);
      window.removeEventListener('ecosphere:session-expired', expireSession);
    };
  }, []);
  return (
    <AnimatePresence mode="wait">
      {view === 'landing' && (
        <motion.div
          key="landing"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.985 }}
          transition={{ duration: 0.35 }}
        >
          <LandingPage onStart={() => navigate('/signin')} />
        </motion.div>
      )}
      {view === 'login' && (
        <motion.div
          key="login"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.985 }}
          transition={{ type: 'spring', bounce: 0, duration: 0.45 }}
        >
          <Login onLogin={openDashboard} />
        </motion.div>
      )}
      {view === 'app' && (
        <motion.div
          key="app"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <Dashboard onLogout={logout} sessionUser={sessionUser} />
          <GamificationAdminQuickActions />
          <ChallengeDetailOverlay />
          <ChallengeAdminSetupPanel />
          <ChallengeRosterPanel />
          <GovernanceHelpButton />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
