import { useLayoutEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowDown, ArrowRight, ArrowUpRight, BarChart3, Check, CircleDot, FileCheck2, Globe2, Leaf, Menu, ShieldCheck, Sparkles, Users, X, Zap } from 'lucide-react';
import './LandingPage.css';

gsap.registerPlugin(ScrollTrigger);

const pillars = [
  { number:'01', eyebrow:'Environmental intelligence', title:'Measure every\nmaterial impact.', body:'Build a decision-ready emissions ledger across operations, products, suppliers and targets — with the evidence attached.', metric:'Scope 1—3', metricLabel:'connected carbon accounting', icon:Leaf, className:'eco-pillar-green', tags:['Emission factors','Product profiles','Climate goals'] },
  { number:'02', eyebrow:'Social performance', title:'Turn participation\ninto progress.', body:'Move beyond annual snapshots. Plan initiatives, verify participation and make workforce impact visible across every department.', metric:'One view', metricLabel:'people, programmes and proof', icon:Users, className:'eco-pillar-coral', tags:['CSR programmes','Diversity signals','Employee action'] },
  { number:'03', eyebrow:'Governance controls', title:'Keep every claim\naudit-ready.', body:'Connect policies, acknowledgements, audits and issues so accountability stays visible from first action to final disclosure.', metric:'Always on', metricLabel:'controls and ownership', icon:ShieldCheck, className:'eco-pillar-violet', tags:['Policy controls','Audit trails','Issue resolution'] },
];

const standards = [
  { name:'GHG', detail:'Scope 1 · 2 · 3', tone:'lime' },
  { name:'GRI', detail:'Impact reporting', tone:'cream' },
  { name:'ISSB', detail:'S1 · S2 ready', tone:'blue' },
  { name:'ESG', detail:'Connected evidence', tone:'coral' },
];

function Mark({ light=false }) {
  return <span className={`eco-mark ${light ? 'is-light' : ''}`} aria-hidden="true"><i/><i/><i/></span>;
}

function MagneticButton({ children, className='', onClick }) {
  const ref=useRef(null);
  const move=(event)=>{ if(window.matchMedia('(pointer: coarse)').matches)return; const rect=ref.current.getBoundingClientRect(); gsap.to(ref.current,{x:(event.clientX-rect.left-rect.width/2)*.13,y:(event.clientY-rect.top-rect.height/2)*.13,duration:.35,ease:'power3.out'}); };
  const reset=()=>gsap.to(ref.current,{x:0,y:0,duration:.55,ease:'elastic.out(1, .35)'});
  return <button ref={ref} className={className} onMouseMove={move} onMouseLeave={reset} onClick={onClick}>{children}</button>;
}

export default function LandingPage({ onStart }) {
  const root=useRef(null);
  const [menuOpen,setMenuOpen]=useState(false);

  useLayoutEffect(()=>{
    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return undefined;
    const ctx=gsap.context(()=>{
      const intro=gsap.timeline({defaults:{ease:'power4.out'}});
      intro.from('.eco-nav',{y:-50,opacity:0,duration:.8})
        .from('.eco-hero-kicker',{y:24,opacity:0,duration:.65},'-=.35')
        .from('.eco-hero-line span',{yPercent:115,rotate:3,stagger:.08,duration:1.05},'-=.45')
        .from('.eco-hero-bottom > *',{y:24,opacity:0,stagger:.09,duration:.65},'-=.55')
        .from('.eco-hero-visual',{clipPath:'inset(0 50% 0 50% round 38px)',scale:.92,duration:1.2},'-=.75');
      gsap.to('.eco-hero-visual img',{yPercent:12,ease:'none',scrollTrigger:{trigger:'.eco-hero',start:'top top',end:'bottom top',scrub:true}});
      gsap.utils.toArray('.eco-reveal').forEach(element=>gsap.from(element,{y:70,opacity:0,duration:1,ease:'power3.out',scrollTrigger:{trigger:element,start:'top 84%'}}));
      gsap.to('.eco-marquee-track',{xPercent:-18,ease:'none',scrollTrigger:{trigger:'.eco-manifesto',start:'top bottom',end:'bottom top',scrub:1}});
      const cards=gsap.utils.toArray('.eco-pillar-card');
      const mm=gsap.matchMedia();
      mm.add('(min-width: 900px)',()=>gsap.to(cards,{xPercent:-100*(cards.length-1),ease:'none',scrollTrigger:{trigger:'.eco-pillars-pin',pin:true,scrub:1,snap:1/(cards.length-1),end:()=>`+=${window.innerWidth*2.2}`}}));
      gsap.from('.eco-dashboard-shell',{clipPath:'circle(8% at 50% 52%)',scale:.86,scrollTrigger:{trigger:'.eco-platform',start:'top 70%',end:'center 52%',scrub:1}});
      gsap.utils.toArray('.eco-float-metric').forEach((item,index)=>gsap.to(item,{y:index%2?-38:42,rotate:index%2?2:-2,ease:'none',scrollTrigger:{trigger:'.eco-platform',start:'top bottom',end:'bottom top',scrub:1.4}}));
      gsap.from('.eco-proof-word',{yPercent:110,rotate:5,stagger:.1,duration:1,ease:'power4.out',scrollTrigger:{trigger:'.eco-proof',start:'top 62%'}});
      return ()=>mm.revert();
    },root);
    return ()=>ctx.revert();
  },[]);

  const goTo=(id)=>{setMenuOpen(false);document.querySelector(id)?.scrollIntoView({behavior:'smooth'});};

  return <main className="eco-root" ref={root}>
    <header className="eco-nav">
      <button className="eco-brand" onClick={()=>goTo('#top')} aria-label="EcoSphere home"><Mark/><strong>ECOSPHERE</strong></button>
      <nav className={menuOpen?'is-open':''} aria-label="Primary navigation">
        <button onClick={()=>goTo('#platform')}>Platform</button><button onClick={()=>goTo('#pillars')}>Solutions</button><button onClick={()=>goTo('#standards')}>Standards</button><button onClick={()=>goTo('#about')}>Why EcoSphere</button>
      </nav>
      <MagneticButton className="eco-nav-cta" onClick={onStart}>Enter workspace <ArrowUpRight size={16}/></MagneticButton>
      <button className="eco-menu" onClick={()=>setMenuOpen(!menuOpen)} aria-label="Toggle menu">{menuOpen?<X/>:<Menu/>}</button>
    </header>

    <section className="eco-hero" id="top">
      <div className="eco-hero-kicker"><Sparkles size={15}/> The operating system for accountable impact</div>
      <h1 aria-label="All impact. One signal."><span className="eco-hero-line"><span>ALL IMPACT.</span></span><span className="eco-hero-line eco-hero-line-accent"><span>ONE SIGNAL.</span></span></h1>
      <div className="eco-hero-bottom">
        <p>Carbon, people and governance data — connected to the decisions that move your business forward.</p>
        <MagneticButton className="eco-round-cta" onClick={()=>goTo('#platform')}><span>See it live</span><ArrowDown size={20}/></MagneticButton>
        <div className="eco-hero-note"><CircleDot size={15}/> Evidence in. Confidence out.</div>
      </div>
      <div className="eco-hero-visual"><img src="/images/ecosphere-landscape.png" alt="Regenerative landscape layered with environmental data signals"/><div className="eco-image-label eco-image-label-left"><span>LIVE</span> Material impact map</div><div className="eco-image-label eco-image-label-right">12 regions connected <Globe2 size={15}/></div></div>
    </section>

    <section className="eco-manifesto" id="about">
      <div className="eco-orbit" aria-hidden="true"><Leaf/><span>TRACE · ACT · REPORT ·</span></div>
      <div className="eco-manifesto-copy"><p className="eco-reveal">Sustainability data is everywhere.</p><h2 className="eco-reveal">CLARITY<br/><em>ISN'T.</em></h2><div className="eco-manifesto-answer eco-reveal"><span>So we built one connected system</span><h3>FROM RAW DATA<br/>TO REAL ACTION.</h3></div></div>
      <div className="eco-marquee"><div className="eco-marquee-track">MEASURE WHAT MATTERS — PROVE WHAT CHANGED — MEASURE WHAT MATTERS — PROVE WHAT CHANGED —</div></div>
    </section>

    <section className="eco-pillars" id="pillars">
      <div className="eco-section-intro eco-reveal"><span>Three pillars. No blind spots.</span><h2>ONE PLATFORM.<br/>THE WHOLE PICTURE.</h2><p>Every record stays linked to its owner, evidence and next action.</p></div>
      <div className="eco-pillars-pin"><div className="eco-pillars-track">{pillars.map(pillar=>{const Icon=pillar.icon;return <article className={`eco-pillar-card ${pillar.className}`} key={pillar.number}>
        <div className="eco-pillar-top"><span>{pillar.number} / 03</span><Icon size={28}/></div>
        <div className="eco-pillar-copy"><span>{pillar.eyebrow}</span><h3>{pillar.title.split('\n').map(line=><span key={line}>{line}</span>)}</h3><p>{pillar.body}</p><div className="eco-tags">{pillar.tags.map(tag=><i key={tag}><Check size={13}/>{tag}</i>)}</div></div>
        <div className="eco-pillar-metric"><strong>{pillar.metric}</strong><span>{pillar.metricLabel}</span></div><div className="eco-card-orbit" aria-hidden="true"><i/><i/><i/></div>
      </article>;})}</div></div>
    </section>

    <section className="eco-platform" id="platform">
      <div className="eco-platform-heading eco-reveal"><span>Connected ESG workspace</span><h2>YOUR IMPACT.<br/><em>IN MOTION.</em></h2></div>
      <div className="eco-dashboard-stage">
        <aside className="eco-float-metric eco-float-one"><span>Emissions intensity</span><strong>↓ 18.6%</strong><small>against baseline</small></aside><aside className="eco-float-metric eco-float-two"><span>Policy coverage</span><strong>96%</strong><small>team acknowledged</small></aside><aside className="eco-float-metric eco-float-three"><span>Active workforce</span><strong>1,284</strong><small>people participating</small></aside>
        <div className="eco-dashboard-shell"><div className="eco-dash-sidebar"><Mark light/>{[BarChart3,Leaf,Users,ShieldCheck,FileCheck2].map((Icon,index)=><span className={index===1?'active':''} key={index}><Icon size={18}/></span>)}</div><div className="eco-dash-main">
          <div className="eco-dash-head"><div><span>ORGANIZATION OVERVIEW</span><strong>Good morning, Maya.</strong></div><button>Export report <ArrowUpRight size={14}/></button></div>
          <div className="eco-dash-scores"><article><span>Environmental</span><strong>82</strong><i><b style={{width:'82%'}}/></i></article><article><span>Social</span><strong>74</strong><i><b style={{width:'74%'}}/></i></article><article><span>Governance</span><strong>91</strong><i><b style={{width:'91%'}}/></i></article></div>
          <div className="eco-dash-grid"><article className="eco-chart-card"><span>EMISSIONS TREND</span><strong>2,418 <small>tCO₂e</small></strong><div className="eco-line-chart"><svg viewBox="0 0 500 140" preserveAspectRatio="none"><path d="M0,110 C55,85 75,98 120,72 C168,44 203,83 250,52 C303,19 328,60 375,31 C418,7 459,23 500,5"/><path className="area" d="M0,110 C55,85 75,98 120,72 C168,44 203,83 250,52 C303,19 328,60 375,31 C418,7 459,23 500,5 L500,140 L0,140 Z"/></svg></div></article><article className="eco-action-card"><span>NEXT BEST ACTION</span><Zap size={25}/><strong>Review supplier data gaps</strong><p>8 records need evidence before reporting.</p><button>Open queue <ArrowRight size={14}/></button></article></div>
        </div></div>
      </div>
    </section>

    <section className="eco-standards" id="standards">
      <div className="eco-standards-head eco-reveal"><span>Built around the language teams already report in</span><h2>STRUCTURE FOR TODAY.<br/>READY FOR WHAT'S NEXT.</h2></div>
      <div className="eco-standard-grid">{standards.map(standard=><article className={`eco-standard eco-${standard.tone} eco-reveal`} key={standard.name}><ArrowUpRight size={19}/><strong>{standard.name}</strong><span>{standard.detail}</span></article>)}</div>
      <p className="eco-standards-note">Framework-ready workflows; your final disclosures remain subject to your organisation's reporting scope, controls and assurance.</p>
    </section>

    <section className="eco-proof">
      <div className="eco-proof-kicker"><span>Not another dashboard.</span><span>A system for follow-through.</span></div>
      <h2><span className="eco-proof-line"><span className="eco-proof-word">CAPTURE.</span></span><span className="eco-proof-line eco-proof-accent"><span className="eco-proof-word">CONNECT.</span></span><span className="eco-proof-line"><span className="eco-proof-word">CHANGE.</span></span></h2>
      <div className="eco-proof-flow">{[['01','Capture','Bring operational data, evidence and ownership into one reliable record.'],['02','Connect','Link environmental, social and governance signals across teams.'],['03','Change','Turn live insights into assigned actions, verified progress and reports.']].map(([number,title,body])=><article key={number}><span>{number}</span><h3>{title}</h3><p>{body}</p></article>)}</div>
    </section>

    <footer className="eco-footer"><div className="eco-footer-top"><p>Ready to make impact<br/>part of how work gets done?</p><MagneticButton className="eco-footer-cta" onClick={onStart}>ENTER ECOSPHERE <ArrowUpRight/></MagneticButton></div><div className="eco-footer-word">ECO<span>SPHERE</span></div><div className="eco-footer-bottom"><div className="eco-brand"><Mark light/><strong>ECOSPHERE</strong></div><span>© 2026 · Built for accountable business</span><div><button onClick={()=>goTo('#top')}>Back to top ↑</button><button onClick={onStart}>Sign in</button></div></div></footer>
  </main>;
}
