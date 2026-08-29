import { useEffect, useState } from 'react';
import { getDashboard, signIn, signUp } from './api';
import { AnimatePresence, motion, useScroll, useSpring, useTransform } from 'framer-motion';
import {
  ArrowUpRight, Bell, Building2, ChevronDown, ChevronRight, CircleHelp, ClipboardCheck,
  CloudSun, FileBarChart, Gauge, Leaf, LogOut, Menu, MoreHorizontal, Plus, Search,
  Settings, ShieldCheck, Sparkles, Trophy, UserPlus, Users, X, Zap
} from 'lucide-react';

const nav = [
  { label: 'Overview', icon: Gauge },
  { label: 'Environmental', icon: Leaf, tone: 'green', children: ['Emission factors', 'Product ESG profiles', 'Carbon transactions', 'Environmental goals'] },
  { label: 'Social', icon: Users, tone: 'blue', children: ['CSR activities', 'Employee participation', 'Diversity dashboard'] },
  { label: 'Governance', icon: Building2, tone: 'violet', children: ['Policies', 'Policy acknowledgements', 'Audits', 'Compliance issues'] },
  { label: 'Gamification', icon: Trophy, tone: 'orange', children: ['Challenges', 'Participation', 'Badges & rewards', 'Leaderboard'] },
  { label: 'Reports', icon: FileBarChart, children: ['Environmental report', 'Social report', 'Governance report', 'ESG summary'] },
];

const kpis = [
  { label: 'Environmental', score: 82, delta: '+4.2%', color: 'green' },
  { label: 'Social', score: 74, delta: '+2.8%', color: 'blue' },
  { label: 'Governance', score: 88, delta: '+1.6%', color: 'violet' },
  { label: 'Overall ESG', score: 81, delta: '+3.1%', color: 'ink' },
];

function Mark() { return <div className="mark"><span /><span /><span /></div>; }

function Login({ onLogin }) {
  const [mode, setMode] = useState('signin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const isCreate = mode === 'create';
  const changeMode = (nextMode) => { setMode(nextMode); setError(''); setLoading(false); };
  const submit = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (isCreate && form.get('password') !== form.get('confirmPassword')) { setError('Passwords do not match. Please try again.'); return; }
    if (isCreate && !form.get('terms')) { setError('Please accept the terms before continuing.'); return; }
    setError(''); setLoading(true);
    try {
      if (isCreate) await signUp(form.get('name'), form.get('email'), form.get('password'));
      await signIn(form.get('email'), form.get('password'));
      onLogin();
    } catch (requestError) { setError(requestError.message); setLoading(false); }
  };
  return <main className="login-page">
    <div className="aurora aurora-one" /><div className="aurora aurora-two" />
    <motion.header className="login-nav" initial={{ opacity: 0, y: -18 }} animate={{ opacity: 1, y: 0 }} transition={{ type: 'spring', stiffness: 220, damping: 24 }}>
      <div className="brand"><Mark /><span>EcoSphere</span></div><button className="help-link"><CircleHelp size={17}/> Need help?</button>
    </motion.header>
    <motion.section className="login-shell" initial={{ opacity: 0, y: 26, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: .08, type: 'spring', stiffness: 150, damping: 20 }}>
      <div className="login-copy"><div className="eyebrow"><Sparkles size={14}/> ESG intelligence, made human</div><h1>Progress feels better<br/><em>when everyone can see it.</em></h1><p>Bring carbon, culture and compliance into one calm, connected place.</p><div className="login-proof"><div className="avatar-stack"><i>AS</i><i>RP</i><i>MK</i></div><span>Trusted by conscious teams everywhere</span></div></div>
      <form className="login-card" onSubmit={submit} noValidate><AnimatePresence mode="wait"><motion.div key={mode} initial={{opacity:0,x:12}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-12}} transition={{type:'spring',stiffness:240,damping:25}}><div className="card-top"><div className="mini-mark">{isCreate ? <UserPlus size={18}/> : <Leaf size={18}/>}</div><div><h2>{isCreate ? 'Create your account' : 'Welcome back'}</h2><p>{isCreate ? 'Start your sustainability workspace' : 'Sign in to your workspace'}</p></div></div>{isCreate && <label>Full name<input name="name" type="text" placeholder="Your full name" autoComplete="name" required /></label>}<label>Work email<input name="email" type="email" defaultValue={isCreate ? '' : 'you@company.com'} placeholder="you@company.com" autoComplete="email" required /></label><label>Password{!isCreate && <a href="#recover">Forgot password?</a>}<input name="password" type="password" defaultValue={isCreate ? '' : '••••••••••'} placeholder={isCreate ? 'At least 8 characters' : ''} autoComplete={isCreate ? 'new-password' : 'current-password'} minLength="8" required /></label>{isCreate && <><label>Confirm password<input name="confirmPassword" type="password" placeholder="Repeat your password" autoComplete="new-password" minLength="8" required /></label><label className="terms"><input name="terms" type="checkbox"/><span>I agree to the <a href="#terms">Terms</a> and <a href="#privacy">Privacy Policy</a>.</span></label></>}{error && <motion.p className="form-error" role="alert" initial={{opacity:0,y:-5}} animate={{opacity:1,y:0}}>{error}</motion.p>}<button className="primary-btn" disabled={loading}>{loading ? (isCreate ? 'Creating account…' : 'Opening workspace…') : <>{isCreate ? 'Create account' : 'Continue'} <ArrowUpRight size={17}/></>}</button><button type="button" className="auth-switch" onClick={() => changeMode(isCreate ? 'signin' : 'create')}>{isCreate ? 'Already have an account? ' : 'New to EcoSphere? '}<strong>{isCreate ? 'Sign in' : 'Create account'}</strong></button></motion.div></AnimatePresence><div className="secure-note"><ShieldCheck size={12}/> Protected with enterprise-grade security</div></form>
    </motion.section>
    <motion.footer className="login-footer" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: .4 }}>© 2026 EcoSphere <span>•</span> Built for better business</motion.footer>
  </main>;
}

function Sidebar({ active, setActive, open, setOpen }) {
  const [expanded, setExpanded] = useState('Environmental');
  return <aside className={`sidebar ${open ? 'open' : ''}`}><div className="side-brand"><div className="brand"><Mark/><span>EcoSphere</span></div><button className="close-side" onClick={() => setOpen(false)}><X size={20}/></button></div><div className="workspace"><div className="workspace-icon">N</div><div><strong>Northstar Co.</strong><span>Enterprise plan</span></div><ChevronDown size={16}/></div><nav>{nav.map(item => <div key={item.label} className="nav-group"><button className={`nav-item ${active === item.label ? 'active' : ''} ${item.tone || ''}`} onClick={() => { setActive(item.label); setExpanded(expanded === item.label ? '' : item.label); }}><item.icon size={18}/><span>{item.label}</span>{item.children && <ChevronRight className={expanded === item.label ? 'rotate' : ''} size={15}/>}</button><AnimatePresence initial={false}>{item.children && expanded === item.label && <motion.div className="nav-children" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: .22 }}>{item.children.map(child => <button key={child} onClick={() => setActive(child)} className={active === child ? 'sub-active' : ''}>{child}</button>)}</motion.div>}</AnimatePresence></div>)}</nav><div className="side-bottom"><button className="nav-item"><Settings size={18}/><span>Settings</span></button><div className="user-mini"><div className="profile-photo">AV</div><div><strong>Amartya Singh</strong><span>ESG Administrator</span></div><MoreHorizontal size={17}/></div></div></aside>;
}

function ScoreCard({ item, index }) { return <motion.article className={`score-card ${item.color}`} initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .08 + index * .07, type: 'spring', stiffness: 180, damping: 21 }}><div className="score-head"><span>{item.label}</span><span className="up">{item.delta} <ArrowUpRight size={13}/></span></div><div className="score-main"><strong>{item.score}</strong><span>/100</span></div><div className="meter"><motion.i initial={{ width: 0 }} animate={{ width: `${item.score}%` }} transition={{ delay: .35 + index * .07, duration: .75, ease: [0.2, 0.8, 0.2, 1] }} /></div></motion.article> }

function TrendCard() { const dots = [63, 48, 54, 38, 44, 29, 40, 25, 32, 18, 26, 12]; return <section className="panel trend"><div className="panel-title"><div><span className="eyebrow green-text">ENVIRONMENTAL</span><h3>Emissions trend</h3></div><button className="soft-btn">12 months <ChevronDown size={15}/></button></div><div className="chart"><svg viewBox="0 0 560 190" preserveAspectRatio="none"><defs><linearGradient id="fade" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#31a45a" stopOpacity=".24"/><stop offset="1" stopColor="#31a45a" stopOpacity="0"/></linearGradient></defs><path d="M0,51 C25,44 35,82 58,77 S82,45 102,65 S127,41 152,58 S182,32 205,48 S230,82 255,74 S281,108 306,93 S332,114 358,101 S382,120 409,106 S434,132 458,110 S488,95 515,114 S540,91 560,86 L560,190 L0,190Z" fill="url(#fade)"/><motion.path initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.4, ease: 'easeInOut' }} d="M0,51 C25,44 35,82 58,77 S82,45 102,65 S127,41 152,58 S182,32 205,48 S230,82 255,74 S281,108 306,93 S332,114 358,101 S382,120 409,106 S434,132 458,110 S488,95 515,114 S540,91 560,86" fill="none" stroke="#23974d" strokeWidth="4" strokeLinecap="round"/></svg><div className="chart-labels">{['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug'].map((m,i)=><span key={m} style={{top:`${dots[i]}%`}}>{m}</span>)}</div></div><div className="trend-footer"><span><i className="legend-dot"/> Carbon intensity</span><strong>−18.4% <small>vs. last year</small></strong></div></section> }

function PeopleCard() { return <section className="panel people"><div className="panel-title"><div><span className="eyebrow blue-text">SOCIAL PULSE</span><h3>People are making it happen</h3></div><button className="icon-btn"><MoreHorizontal size={20}/></button></div><div className="people-list">{[['AS','Anika Shah','Completed Plastic-Free Week','+180 XP','#ddf6e4'],['RK','Rohit Kumar','Joined Beach Cleanup','+70 XP','#e4efff'],['SM','Sana Mirza','Acknowledged Code of Ethics','+20 XP','#eee7ff']].map((p,i)=><motion.div className="person-row" key={p[1]} initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: .35 + i*.08 }}><div className="person-avatar" style={{background:p[4]}}>{p[0]}</div><div><strong>{p[1]}</strong><span>{p[2]}</span></div><b>{p[3]}</b></motion.div>)}</div><button className="text-button">View activity <ArrowUpRight size={15}/></button></section> }

function RankingCard() { return <section className="panel ranking"><div className="panel-title"><div><span className="eyebrow violet-text">ORGANIZATION</span><h3>Department momentum</h3></div><button className="soft-btn">This quarter <ChevronDown size={15}/></button></div><div className="rank-list">{[['Operations',92,'#663fd8'],['Product',86,'#4773de'],['People',79,'#3ca4c9'],['Finance',74,'#61ac75']].map((r,i)=><div className="rank-row" key={r[0]}><span>0{i+1}</span><strong>{r[0]}</strong><div><motion.i initial={{scaleX:0}} animate={{scaleX:r[1]/100}} transition={{delay:.3+i*.08}} style={{background:r[2]}}/></div><b>{r[1]}</b></div>)}</div></section> }

function Dashboard({ onLogout }) {
 const [active,setActive] = useState('Overview'); const [menu,setMenu]=useState(false); const [live,setLive]=useState(null); const { scrollY }=useScroll(); const glowY=useSpring(useTransform(scrollY,[0,700],[0,150]),{stiffness:90,damping:25});
 useEffect(() => { getDashboard().then(setLive).catch(() => setLive(null)); }, []);
 const shownKpis = live ? [{label:'Environmental',score:live.kpis.environmental,delta:'Live',color:'green'},{label:'Social',score:live.kpis.social,delta:'Live',color:'blue'},{label:'Governance',score:live.kpis.governance,delta:'Live',color:'violet'},{label:'Overall ESG',score:live.kpis.overall,delta:'Live',color:'ink'}] : kpis;
 return <div className="app-shell"><Sidebar active={active} setActive={setActive} open={menu} setOpen={setMenu}/><main className="workspace-main"><motion.div className="dashboard-glow" style={{y:glowY}}/><header className="topbar"><button className="mobile-menu" onClick={()=>setMenu(true)}><Menu size={21}/></button><div className="crumb"><span>EcoSphere</span><ChevronRight size={14}/><strong>{active}</strong></div><div className="top-actions"><button className="search"><Search size={17}/><span>Search anything</span><kbd>⌘ K</kbd></button><button className="icon-btn notification"><Bell size={19}/><i/></button><button className="top-avatar">AV</button><button className="logout" onClick={onLogout} title="Sign out"><LogOut size={17}/></button></div></header><div className="content"><motion.div className="welcome" initial={{opacity:0,y:16}} animate={{opacity:1,y:0}}><div><span className="eyebrow">LIVE ODOO DASHBOARD</span><h1>Good morning, {live?.user?.name || "there"}. </h1><p>Here’s how your organization is moving the needle.</p></div><button className="primary-btn"><Plus size={18}/> Log carbon data</button></motion.div><section className="score-grid">{shownKpis.map((k,i)=><ScoreCard item={k} index={i} key={k.label}/>)}</section><section className="bento primary-bento"><TrendCard/><PeopleCard/></section><section className="bento lower-bento"><RankingCard/><section className="panel impact-card"><div className="impact-orbit orbit-1"/><div className="impact-orbit orbit-2"/><CloudSun size={30}/><span className="eyebrow">THIS MONTH</span><h3>1.8t <em>CO₂e avoided</em></h3><p>That’s the equivalent of planting 29 trees.</p><button className="text-button">Explore impact <ArrowUpRight size={15}/></button></section><section className="panel next-card"><span className="eyebrow orange-text">UP NEXT</span><h3>Quarterly ESG review</h3><p>Review your goals and invite your team before September 05.</p><div><span className="date-chip">05<br/><small>SEP</small></span><button className="round-action"><ArrowUpRight size={18}/></button></div></section></section></div></main></div>
}

export default function App(){ const [signedIn,setSignedIn]=useState(false); return <AnimatePresence mode="wait">{signedIn ? <motion.div key="app" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}><Dashboard onLogout={()=>setSignedIn(false)}/></motion.div> : <motion.div key="login" exit={{opacity:0,scale:.985}}><Login onLogin={()=>setSignedIn(true)}/></motion.div>}</AnimatePresence> }
