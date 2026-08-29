import { useEffect, useRef, useState } from 'react';
import {
  motion,
  useScroll,
  useTransform,
  useSpring,
  useInView,
  useMotionValue,
  animate,
} from 'framer-motion';
import { ArrowUpRight, Leaf, BarChart3, ShieldCheck, Zap, Users, Globe, Star } from 'lucide-react';

/* ─── helpers ─────────────────────────────────────────────── */

function Mark() {
  return (
    <div className="mark">
      <span /><span /><span />
    </div>
  );
}

/* Animated counter that counts up when visible */
function AnimatedCount({ to, suffix = '' }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-60px' });
  const count = useMotionValue(0);
  const [display, setDisplay] = useState('0');

  useEffect(() => {
    if (!inView) return;
    const ctrl = animate(count, to, {
      duration: 2,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: v => {
        if (to >= 1000) {
          setDisplay((v / 1000).toFixed(1) + 'k');
        } else if (to < 10) {
          setDisplay(v.toFixed(1));
        } else {
          setDisplay(Math.round(v).toString());
        }
      },
    });
    return ctrl.stop;
  }, [inView, count, to]);

  return <span ref={ref}>{display}{suffix}</span>;
}

/* ─── Feature data ────────────────────────────────────────── */

const features = [
  {
    icon: BarChart3,
    color: '#2a7a4b',
    bg: 'linear-gradient(135deg,#e8fdf0,#f0faf4)',
    accent: '#c8fca0',
    label: 'Environmental',
    title: 'Carbon, counted precisely.',
    body: 'Log verified operational emissions, track product ESG profiles, and hit science-based targets — all in a single connected ledger.',
    items: ['Real-time CO₂e dashboard', 'Emission factor library', 'Goal tracking & projections'],
  },
  {
    icon: Users,
    color: '#2c5fcb',
    bg: 'linear-gradient(135deg,#eef3ff,#f4f7ff)',
    accent: '#a8c4fc',
    label: 'Social',
    title: 'People impact, made visible.',
    body: 'Plan CSR initiatives, capture participation evidence, and surface workforce diversity — so culture and compliance move together.',
    items: ['CSR activity planner', 'Employee participation tracker', 'Diversity dashboard'],
  },
  {
    icon: ShieldCheck,
    color: '#6b3cc9',
    bg: 'linear-gradient(135deg,#f3eeff,#f8f5ff)',
    accent: '#c9b4f8',
    label: 'Governance',
    title: 'Compliance, never an afterthought.',
    body: 'Maintain policies, run audit cycles, and resolve compliance issues in one workflow — so nothing falls through the cracks.',
    items: ['Policy management & acknowledgements', 'Audit lifecycle tools', 'Issue resolution workflow'],
  },
];

const testimonials = [
  {
    quote: "EcoSphere turned our scattered ESG spreadsheets into one calm, trustworthy system. Board-ready reports used to take two weeks — now it's an afternoon.",
    name: 'Priya Sharma',
    role: 'Chief Sustainability Officer, Nexora',
    initials: 'PS',
    color: '#d4f5e0',
  },
  {
    quote: "The gamification layer genuinely changed employee behaviour. XP challenges made sustainability feel like something people wanted to do, not a tick-box exercise.",
    name: 'Rajan Mehta',
    role: 'Head of People, GreenWave',
    initials: 'RM',
    color: '#dde8ff',
  },
  {
    quote: "We passed our first GRI audit with zero findings. The governance module kept every policy acknowledgement timestamped and audit-ready from day one.",
    name: 'Aisha Lindqvist',
    role: 'Compliance Lead, Solaris Group',
    initials: 'AL',
    color: '#ede0ff',
  },
];

/* ─── Sections ────────────────────────────────────────────── */

function Hero({ onStart }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });

  // Parallax layers — compositor-friendly (transform + opacity only)
  const yHeadline = useTransform(scrollYProgress, [0, 1], [0, -120]);
  const yCard1 = useTransform(scrollYProgress, [0, 1], [0, -60]);
  const yCard2 = useTransform(scrollYProgress, [0, 1], [0, -110]);
  const yCard3 = useTransform(scrollYProgress, [0, 1], [0, -40]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0]);

  // Spring wrappers so motion is fluid, not a hard lerp
  const yH = useSpring(yHeadline, { stiffness: 80, damping: 20 });
  const yC1 = useSpring(yCard1,    { stiffness: 60, damping: 18 });
  const yC2 = useSpring(yCard2,    { stiffness: 50, damping: 18 });
  const yC3 = useSpring(yCard3,    { stiffness: 70, damping: 18 });

  return (
    <section ref={ref} className="lp-hero">
      {/* animated aurora blobs */}
      <div className="lp-aurora lp-aurora-a" />
      <div className="lp-aurora lp-aurora-b" />
      <div className="lp-aurora lp-aurora-c" />

      {/* floating background cards — parallax */}
      <motion.div className="lp-float-card lp-fc1" style={{ y: yC1 }}>
        <div className="lp-fc-eyebrow"><Leaf size={11} /> Environmental</div>
        <div className="lp-fc-value">2.4M tCO₂e</div>
        <div className="lp-fc-label">tracked this quarter</div>
        <div className="lp-fc-bar"><div className="lp-fc-fill" style={{ width: '72%', background: '#6ee7a0' }} /></div>
      </motion.div>

      <motion.div className="lp-float-card lp-fc2" style={{ y: yC2 }}>
        <div className="lp-fc-eyebrow"><Zap size={11} /> Gamification</div>
        <div className="lp-fc-value">+4 840 XP</div>
        <div className="lp-fc-label">earned this week</div>
        <div className="lp-fc-avatars">
          <i style={{ background: '#c4e7d1' }}>AS</i>
          <i style={{ background: '#cfd9fa' }}>RP</i>
          <i style={{ background: '#f4d7c6' }}>MK</i>
          <span>+23 employees</span>
        </div>
      </motion.div>

      <motion.div className="lp-float-card lp-fc3" style={{ y: yC3 }}>
        <div className="lp-fc-eyebrow"><ShieldCheck size={11} /> Governance</div>
        <div className="lp-fc-value">100%</div>
        <div className="lp-fc-label">policy acknowledgement</div>
        <div className="lp-fc-pill lp-pill-green">Audit-ready</div>
      </motion.div>

      {/* headline copy */}
      <motion.div className="lp-hero-copy" style={{ y: yH, opacity: heroOpacity }}>
        <motion.div
          className="lp-eyebrow"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', bounce: 0, duration: 0.5 }}
        >
          <Leaf size={13} /> ESG intelligence, made human
        </motion.div>

        <motion.h1
          className="lp-headline"
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', bounce: 0, duration: 0.55, delay: 0.07 }}
        >
          Sustainability,<br />
          <em>made intelligent.</em>
        </motion.h1>

        <motion.p
          className="lp-subline"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', bounce: 0, duration: 0.5, delay: 0.14 }}
        >
          Carbon tracking, social impact, and governance compliance — unified in
          one calm, connected workspace that your whole company will actually use.
        </motion.p>

        <motion.div
          className="lp-hero-actions"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', bounce: 0, duration: 0.5, delay: 0.2 }}
        >
          <button className="lp-cta-btn" onClick={onStart}>
            Get started <ArrowUpRight size={17} />
          </button>
          <div className="lp-trust">
            <div className="lp-avatars">
              <i style={{ background: '#c4e7d1' }}>AS</i>
              <i style={{ background: '#cfd9fa' }}>RP</i>
              <i style={{ background: '#f4d7c6' }}>MK</i>
            </div>
            <span>Trusted by conscious teams everywhere</span>
          </div>
        </motion.div>
      </motion.div>

      {/* scroll indicator */}
      <motion.div
        className="lp-scroll-hint"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
      >
        <motion.div
          className="lp-scroll-dot"
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 1.6, ease: 'easeInOut' }}
        />
      </motion.div>
    </section>
  );
}

function FeatureStorytelling() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  // 3 segments: 0–0.33, 0.33–0.67, 0.67–1
  const activeIndex = useTransform(scrollYProgress, [0, 0.34, 0.67, 1], [0, 1, 2, 2]);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const unsub = activeIndex.on('change', v => setActive(Math.round(v)));
    return unsub;
  }, [activeIndex]);

  return (
    <section ref={containerRef} className="lp-feature-outer">
      <div className="lp-feature-sticky">
        {/* left — text */}
        <div className="lp-feature-copy">
          <div className="lp-feature-tabs">
            {features.map((f, i) => (
              <button
                key={f.label}
                className={`lp-ftab ${active === i ? 'active' : ''}`}
                style={active === i ? { color: f.color, borderColor: f.color } : {}}
                onClick={() => {
                  if (!containerRef.current) return;
                  const el = containerRef.current;
                  const total = el.scrollHeight - window.innerHeight;
                  const target = el.offsetTop + (i / 3) * total;
                  window.scrollTo({ top: target, behavior: 'smooth' });
                }}
              >
                {f.label}
              </button>
            ))}
          </div>

          {features.map((f, i) => (
            <motion.div
              key={f.label}
              className="lp-feature-text"
              animate={{ opacity: active === i ? 1 : 0, y: active === i ? 0 : 18 }}
              transition={{ type: 'spring', bounce: 0, duration: 0.45 }}
              style={{ pointerEvents: active === i ? 'auto' : 'none', position: 'absolute' }}
            >
              <div className="lp-feature-icon" style={{ background: f.bg, color: f.color }}>
                <f.icon size={22} />
              </div>
              <h2 className="lp-feature-title">{f.title}</h2>
              <p className="lp-feature-body">{f.body}</p>
              <ul className="lp-feature-list">
                {f.items.map(item => (
                  <li key={item}>
                    <span className="lp-check" style={{ color: f.color }}>✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* right — morphing card */}
        <div className="lp-feature-card-wrap">
          {features.map((f, i) => (
            <motion.div
              key={f.label}
              className="lp-feature-card"
              style={{ background: f.bg }}
              animate={{
                opacity: active === i ? 1 : 0,
                scale: active === i ? 1 : 0.94,
                y: active === i ? 0 : 24,
              }}
              transition={{ type: 'spring', bounce: 0, duration: 0.5 }}
            >
              <div className="lp-fc-card-header">
                <div className="lp-feature-icon-sm" style={{ color: f.color }}>
                  <f.icon size={16} />
                </div>
                <span style={{ color: f.color, fontWeight: 800, fontSize: 11 }}>{f.label}</span>
              </div>
              <div className="lp-mock-chart">
                {[65, 82, 58, 90, 74, 95, 88].map((h, idx) => (
                  <motion.div
                    key={idx}
                    className="lp-bar"
                    style={{ background: f.accent }}
                    initial={{ scaleY: 0 }}
                    animate={{ scaleY: active === i ? 1 : 0 }}
                    transition={{ type: 'spring', bounce: 0, duration: 0.55, delay: idx * 0.04 }}
                    custom={h}
                  >
                    <div style={{ height: `${h}%`, width: '100%', background: f.accent, borderRadius: 4, transformOrigin: 'bottom' }} />
                  </motion.div>
                ))}
              </div>
              <div className="lp-fc-stat">
                <strong style={{ color: f.color }}>
                  {i === 0 ? '2.4M tCO₂e' : i === 1 ? '94%' : '100%'}
                </strong>
                <span>
                  {i === 0 ? 'emissions tracked' : i === 1 ? 'participation rate' : 'compliance score'}
                </span>
              </div>
              {f.items.map((item, idx) => (
                <motion.div
                  key={item}
                  className="lp-fc-row"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: active === i ? 1 : 0, x: active === i ? 0 : -10 }}
                  transition={{ type: 'spring', bounce: 0, duration: 0.4, delay: 0.1 + idx * 0.07 }}
                >
                  <span className="lp-check" style={{ color: f.color }}>✓</span>
                  <span>{item}</span>
                </motion.div>
              ))}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function StatsStrip() {
  const stats = [
    { value: 12000, suffix: '+', label: 'Teams worldwide', color: '#2a7a4b' },
    { value: 2.4, suffix: 'M tCO₂e', label: 'Emissions tracked', color: '#2c5fcb' },
    { value: 99.8, suffix: '%', label: 'Platform uptime', color: '#6b3cc9' },
    { value: 4, suffix: '×', label: 'Faster reporting', color: '#c05c18' },
  ];

  return (
    <section className="lp-stats">
      <motion.div
        className="lp-stats-inner"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-80px' }}
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.p
          className="lp-section-eyebrow"
          variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { type: 'spring', bounce: 0, duration: 0.5 } } }}
        >
          <Globe size={13} /> Trusted at scale
        </motion.p>
        <motion.h2
          className="lp-section-title"
          variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0, transition: { type: 'spring', bounce: 0, duration: 0.5, delay: 0.06 } } }}
        >
          Numbers that matter.
        </motion.h2>

        <div className="lp-stats-grid">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              className="lp-stat-card"
              variants={{
                hidden: { opacity: 0, y: 24, scale: 0.96 },
                visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', bounce: 0.1, duration: 0.55, delay: 0.1 + i * 0.08 } },
              }}
            >
              <div className="lp-stat-value" style={{ color: s.color }}>
                <AnimatedCount to={s.value} />{s.suffix}
              </div>
              <div className="lp-stat-label">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}

/* Rubber-band drag carousel (Apple §9) */
function TestimonialCarousel() {
  const trackRef = useRef(null);
  const x = useMotionValue(0);
  const [idx, setIdx] = useState(0);
  const CARD_W = 480; // roughly

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  // rubber-band resistance beyond edges
  function rubberband(overshoot, dim = 400, k = 0.55) {
    return (overshoot * dim * k) / (dim + k * Math.abs(overshoot));
  }

  const maxDrag = -(testimonials.length - 1) * CARD_W;

  const handleDragEnd = (_, info) => {
    const vel = info.velocity.x;
    const cur = x.get();
    const projected = cur + (vel / 1000) * 0.998 / (1 - 0.998); // Apple's projection
    const snapped = Math.round(clamp(projected, maxDrag, 0) / CARD_W) * CARD_W;
    setIdx(-snapped / CARD_W);
    animate(x, snapped, { type: 'spring', bounce: 0.15, duration: 0.5, velocity: vel });
  };

  return (
    <section className="lp-testimonials">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-60px' }}
        transition={{ type: 'spring', bounce: 0, duration: 0.5 }}
      >
        <p className="lp-section-eyebrow"><Star size={13} /> What teams say</p>
        <h2 className="lp-section-title">Calm clarity, every quarter.</h2>
      </motion.div>

      <div className="lp-carousel-outer">
        <motion.div
          ref={trackRef}
          className="lp-carousel-track"
          style={{ x }}
          drag="x"
          dragElastic={0}
          dragMomentum={false}
          onDrag={(_, info) => {
            const raw = x.get();
            if (raw > 0) {
              x.set(rubberband(raw));
            } else if (raw < maxDrag) {
              x.set(maxDrag + rubberband(raw - maxDrag));
            }
          }}
          onDragEnd={handleDragEnd}
          whileTap={{ cursor: 'grabbing' }}
        >
          {testimonials.map((t, i) => (
            <motion.article
              key={t.name}
              className="lp-tcard"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ type: 'spring', bounce: 0, duration: 0.5, delay: i * 0.1 }}
            >
              <p className="lp-tquote">"{t.quote}"</p>
              <div className="lp-tauthor">
                <div className="lp-tavatar" style={{ background: t.color }}>{t.initials}</div>
                <div>
                  <strong>{t.name}</strong>
                  <span>{t.role}</span>
                </div>
              </div>
            </motion.article>
          ))}
        </motion.div>
      </div>

      {/* dot indicators */}
      <div className="lp-dots">
        {testimonials.map((_, i) => (
          <button
            key={i}
            className={`lp-dot ${idx === i ? 'active' : ''}`}
            onClick={() => {
              setIdx(i);
              animate(x, -i * CARD_W, { type: 'spring', bounce: 0, duration: 0.5 });
            }}
          />
        ))}
      </div>
    </section>
  );
}

function DarkCTA({ onStart }) {
  return (
    <section className="lp-dark-cta">
      <div className="lp-dark-inner">
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.97 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ type: 'spring', bounce: 0, duration: 0.55 }}
          className="lp-dark-content"
        >
          <div className="lp-dark-orbs">
            <div className="lp-dark-orb lp-dark-orb-a" />
            <div className="lp-dark-orb lp-dark-orb-b" />
          </div>
          <p className="lp-eyebrow lp-eyebrow-light"><Leaf size={13} /> EcoSphere · ESG Platform</p>
          <h2 className="lp-dark-title">
            Start your ESG journey<br />
            <em>today.</em>
          </h2>
          <p className="lp-dark-body">
            Join thousands of conscious teams who turned sustainability from a spreadsheet
            into a company-wide movement.
          </p>
          <div className="lp-dark-actions">
            <button className="lp-cta-btn lp-cta-light" onClick={onStart}>
              Get started <ArrowUpRight size={17} />
            </button>
            <div className="lp-trust lp-trust-light">
              <div className="lp-avatars">
                <i style={{ background: '#4a7c5e' }}>AS</i>
                <i style={{ background: '#3c5caa' }}>RP</i>
                <i style={{ background: '#7c4c2e' }}>MK</i>
              </div>
              <span>12 000+ teams worldwide</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

/* ─── Main export ─────────────────────────────────────────── */

export default function LandingPage({ onStart }) {
  return (
    <div className="lp-root">
      {/* nav */}
      <motion.header
        className="lp-nav"
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', bounce: 0, duration: 0.5 }}
      >
        <div className="brand">
          <Mark />
          <span>EcoSphere</span>
        </div>
        <nav className="lp-nav-links">
          <a href="#features">Features</a>
          <a href="#stats">Impact</a>
          <a href="#testimonials">Reviews</a>
        </nav>
        <button className="lp-nav-cta" onClick={onStart}>
          Sign in <ArrowUpRight size={14} />
        </button>
      </motion.header>

      <Hero onStart={onStart} />

      <div id="features">
        <FeatureStorytelling />
      </div>

      <div id="stats">
        <StatsStrip />
      </div>

      <div id="testimonials">
        <TestimonialCarousel />
      </div>

      <DarkCTA onStart={onStart} />

      <footer className="lp-footer">
        <div className="brand">
          <Mark />
          <span>EcoSphere</span>
        </div>
        <span>© 2026 EcoSphere · Built for better business</span>
        <span className="lp-footer-links">
          <a href="#">Privacy</a>
          <a href="#">Terms</a>
          <a href="#">Security</a>
        </span>
      </footer>
    </div>
  );
}
