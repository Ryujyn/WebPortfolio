import React, { useEffect, useState, useCallback } from 'react';
import {
  motion,
  useMotionValue,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
} from 'framer-motion';
import { SITE, CONTENT, PROJECTS, SKILLS } from './data/content.js';

// ── Animation variants ────────────────────────────────────────────────
const sectionVariants = {
  hidden:  { opacity: 0.88, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.65, ease: [0.22, 1, 0.36, 1] } },
};
const stagger = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.1 } },
};
const cardAnim = {
  hidden:  { opacity: 0.9, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
};

// ── Hooks ────────────────────────────────────────────────────────────
function useTheme() {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'dark';
    const s = localStorage.getItem('theme');
    if (s === 'light' || s === 'dark') return s;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);
  const toggleTheme = useCallback(() => setTheme(t => t === 'dark' ? 'light' : 'dark'), []);
  return { theme, toggleTheme };
}

function useLanguage() {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'th');
  useEffect(() => {
    document.documentElement.lang = lang === 'th' ? 'th' : 'en';
    document.documentElement.dataset.lang = lang;
    localStorage.setItem('lang', lang);
  }, [lang]);
  const toggleLang = useCallback(() => setLang(l => l === 'th' ? 'en' : 'th'), []);
  const t = useCallback((key) => CONTENT[lang][key] ?? key, [lang]);
  return { lang, toggleLang, t };
}

function usePointerEnabled() {
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    const q = window.matchMedia('(pointer: fine) and (min-width: 768px)');
    const update = () => setEnabled(q.matches);
    update();
    q.addEventListener('change', update);
    return () => q.removeEventListener('change', update);
  }, []);
  return enabled;
}

// ── Background ────────────────────────────────────────────────────────
function InteractiveBackground() {
  const pointerEnabled = usePointerEnabled();
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const bandY = useTransform(scrollYProgress, [0, 1], ['0%', '18%']);
  const gridY = useTransform(scrollYProgress, [0, 1], ['0%', '8%']);
  const x = useMotionValue(-200);
  const y = useMotionValue(-200);
  const sx = useSpring(x, { stiffness: 90, damping: 24, mass: 0.25 });
  const sy = useSpring(y, { stiffness: 90, damping: 24, mass: 0.25 });

  useEffect(() => {
    if (!pointerEnabled || reduceMotion) return;
    const h = (e) => { x.set(e.clientX); y.set(e.clientY); };
    window.addEventListener('pointermove', h);
    return () => window.removeEventListener('pointermove', h);
  }, [pointerEnabled, reduceMotion, x, y]);

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden="true">
      <motion.div className="cyber-grid" style={{ y: gridY }} />
      <motion.div className="light-field light-field-one" style={{ y: bandY }} />
      <motion.div className="light-field light-field-two" style={{ y: gridY }} />
      <div className="energy-line energy-line-blue" />
      <div className="energy-line energy-line-yellow" />
      {pointerEnabled && !reduceMotion && (
        <motion.div className="pointer-field" style={{ x: sx, y: sy }} />
      )}
    </div>
  );
}

// ── Header ────────────────────────────────────────────────────────────
const NAV_KEYS = ['nav_projects','nav_about','nav_focus','nav_skills','nav_contact'];
const NAV_HREFS = ['#projects','#about','#focus','#skills','#contact'];
const NAV_IDS = NAV_HREFS.map((h) => h.slice(1));

function useActiveSection(ids) {
  const [active, setActive] = useState('');
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) setActive(e.target.id); }),
      { rootMargin: '-45% 0px -50% 0px' }
    );
    ids.forEach((id) => { const el = document.getElementById(id); if (el) obs.observe(el); });
    return () => obs.disconnect();
  }, [ids]);
  return active;
}

function Header({ theme, toggleTheme, t, toggleLang }) {
  const isDark = theme === 'dark';
  const active = useActiveSection(NAV_IDS);
  const logoSrc = isDark
    ? '/assets/images/sparx-logo-web-white.png'
    : '/assets/images/sparx-logo-web-black.png';

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-border/70 bg-background/72 backdrop-blur-2xl">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Main row */}
        <div className="flex min-h-[52px] items-center justify-between gap-2 py-1 md:min-h-[78px] md:gap-3 md:py-1.5">
          <a href="#hero" className="group flex min-w-0 shrink-0 items-center" aria-label="SPARX home">
            <img src={logoSrc} alt="SPARX" className="h-9 w-auto md:h-16" />
          </a>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-0.5 md:flex" aria-label="Primary">
            {NAV_KEYS.map((k, i) => {
              const isActive = active === NAV_IDS[i];
              return (
                <a key={k} href={NAV_HREFS[i]} aria-current={isActive ? 'page' : undefined}
                  className={`rounded-md px-3 py-2 text-sm font-medium transition hover:bg-primary/10 hover:text-foreground ${isActive ? 'bg-primary/10 text-foreground' : 'text-muted'}`}>
                  {t(k)}
                </a>
              );
            })}
          </nav>

          {/* Desktop controls */}
          <div className="hidden items-center gap-2 md:flex">
            <button onClick={toggleLang} type="button"
              className="rounded-md border border-border bg-surface/80 px-3 py-2 text-xs font-black tracking-widest text-muted transition hover:border-primary/50 hover:text-foreground">
              {t('lang_toggle')}
            </button>
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <a href="#contact"
              className="rounded-md bg-honey px-4 py-2 text-sm font-black text-slate-950 shadow-[0_0_28px_rgba(250,204,21,0.24)] transition hover:-translate-y-0.5 hover:bg-honey/90">
              {t('nav_contact')}
            </a>
          </div>

          {/* Mobile: lang + theme only */}
          <div className="flex shrink-0 items-center gap-1 md:hidden">
            <button onClick={toggleLang} type="button"
              className="rounded-md border border-border bg-surface/80 px-2 py-1 text-[11px] font-black tracking-widest text-muted">
              {t('lang_toggle')}
            </button>
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} compact />
          </div>
        </div>

        {/* Mobile nav row */}
        <nav className="flex flex-wrap items-center justify-center gap-0 border-t border-border/50 pb-1 pt-0.5 md:hidden" aria-label="Mobile">
          {NAV_KEYS.map((k, i) => {
            const isActive = active === NAV_IDS[i];
            return (
              <a key={k} href={NAV_HREFS[i]} aria-current={isActive ? 'page' : undefined}
                className={`inline-flex min-h-[38px] items-center rounded-md px-2.5 py-1.5 text-[11px] font-semibold transition hover:bg-primary/10 hover:text-foreground ${isActive ? 'bg-primary/10 text-foreground' : 'text-muted'}`}>
                {t(k)}
              </a>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

function ThemeToggle({ theme, toggleTheme, compact = false }) {
  const isDark = theme === 'dark';
  return (
    <button type="button" onClick={toggleTheme}
      className={`group flex shrink-0 items-center rounded-md border border-border bg-surface/80 text-sm font-semibold text-foreground transition hover:border-primary/50 hover:bg-primary/10 ${compact ? 'h-8 w-12 justify-center px-1.5' : 'h-9 gap-2.5 px-3'}`}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}>
      <span className={`relative rounded-full border transition ${compact ? 'h-4 w-8' : 'h-5 w-9'} ${isDark ? 'border-primary/50 bg-background/80' : 'border-honey/60 bg-honey/20'}`}>
        <span className={`absolute top-1/2 -translate-y-1/2 rounded-full shadow-sm transition ${compact ? 'h-3 w-3' : 'h-4 w-4'} ${isDark ? 'left-0.5 bg-electric' : 'left-[1.05rem] bg-honey'}`} />
      </span>
      {!compact && <span className="text-xs">{isDark ? 'Dark' : 'Light'}</span>}
    </button>
  );
}

// ── Shared: RevealSection, SectionHeader ─────────────────────────────
function RevealSection({ id, children, className = '' }) {
  return (
    <motion.section id={id} variants={sectionVariants}
      initial="hidden" whileInView="visible"
      viewport={{ once: true, amount: 0.1 }}
      className={`relative z-10 scroll-mt-28 px-4 py-14 sm:px-6 sm:py-16 md:scroll-mt-24 md:py-20 lg:px-8 ${className}`}>
      <div className="mx-auto max-w-7xl">{children}</div>
    </motion.section>
  );
}

function SectionHeader({ num, eyebrow, title, intro, split = false }) {
  return (
    <header className={`mb-12 ${split ? 'grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,34rem)] lg:items-start lg:gap-8' : ''}`}>
      <div>
        <span className="mb-3 block text-xs font-black tracking-[0.2em] text-primary">
          {num} — {eyebrow}
        </span>
        <h2 className="text-3xl font-black tracking-normal text-foreground sm:text-4xl">{title}</h2>
      </div>
      {intro && (
        <p className={split
          ? 'text-base leading-8 text-muted lg:max-w-[34rem]'
          : 'mt-4 max-w-2xl text-sm leading-7 text-muted'}>
          {intro}
        </p>
      )}
    </header>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────
function Hero({ t }) {
  return (
    <section id="hero" className="hero-stage relative z-10 scroll-mt-28 overflow-hidden px-4 pb-10 pt-28 sm:px-6 sm:pb-14 sm:pt-32 md:scroll-mt-24 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex min-h-[32rem] items-center justify-center sm:min-h-[36rem] md:min-h-[calc(100svh-14rem)]">
          <motion.div initial={{ opacity: 0.92, y: 18 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="relative mx-auto flex w-full max-w-5xl flex-col items-center text-center">
            <h1 className="break-words text-4xl font-black leading-[1.06] tracking-normal text-foreground sm:text-6xl lg:text-8xl">
              <span className="block">{t('hero_title_1')}</span>
              <span className="block text-primary">{t('hero_title_2')}</span>
              <span className="block">{t('hero_title_3')}</span>
            </h1>
            <p className="mt-6 max-w-3xl text-base leading-8 text-muted sm:text-lg">
              {t('hero_desc')}
            </p>
            <div className="mt-7 flex flex-wrap justify-center gap-3 sm:mt-8">
              <a href="#projects"
                className="inline-flex min-h-[42px] items-center justify-center rounded-md bg-honey px-4 py-2 text-sm font-black text-slate-950 shadow-[0_0_32px_rgba(250,204,21,0.26)] transition hover:-translate-y-0.5 hover:bg-honey/90 sm:min-h-[44px] sm:px-5 sm:py-2.5">
                {t('hero_cta_projects')}
                <span className="ml-2">→</span>
              </a>
              <a href="#contact"
                className="inline-flex min-h-[42px] items-center justify-center rounded-md border border-primary/35 bg-surface/70 px-4 py-2 text-sm font-bold text-foreground backdrop-blur-xl transition hover:-translate-y-0.5 hover:border-honey/60 hover:bg-primary/10 sm:min-h-[44px] sm:px-5 sm:py-2.5">
                {t('hero_cta_contact')}
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ── About ─────────────────────────────────────────────────────────────
function About({ t }) {
  return (
    <RevealSection id="about">
      <div className="grid gap-12 lg:grid-cols-[1fr_1.4fr]">
        <SectionHeader num={t('about_num')} eyebrow={t('about_eyebrow')} title={t('about_title')} />

        <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }}
          className="grid gap-5">
          <motion.p variants={cardAnim} className="text-base leading-8 font-medium text-foreground/90">
            {t('about_lead')}
          </motion.p>
          <motion.p variants={cardAnim} className="text-sm leading-7 text-muted">
            {t('about_p1')}
          </motion.p>
          <motion.p variants={cardAnim} className="text-sm leading-7 text-muted">
            {t('about_p2')}
          </motion.p>

          {/* Kitchen photos */}
          <motion.div variants={cardAnim}
            className="grid grid-cols-3 gap-2 overflow-hidden rounded-lg">
            {[1,2,3].map(n => (
              <img key={n} src={`/assets/kitchen/dish-${n}.jpg`} alt=""
                className="aspect-square w-full rounded-lg object-cover opacity-80 transition hover:opacity-100"
                loading="lazy" />
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div variants={cardAnim}
            className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {[
              { num: t('stat_1_num'), label: t('stat_1_label') },
              { num: t('stat_2_num'), label: t('stat_2_label') },
              { num: t('stat_3_num'), label: t('stat_3_label') },
            ].map((s, i) => (
              <div key={s.num}
                className={`rounded-lg border border-border bg-surface/60 p-4 text-center backdrop-blur-xl ${i === 2 ? 'col-span-2 sm:col-span-1' : ''}`}>
                <strong className="block text-xl font-black text-honey">{s.num}</strong>
                <span className="mt-1 block text-xs text-muted">{s.label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </RevealSection>
  );
}

// ── Focus ─────────────────────────────────────────────────────────────
function Focus({ t }) {
  const cards = [
    { num: t('focus_1_num'), title: t('focus_1_title'), desc: t('focus_1_desc'), keys: t('focus_1_keys') },
    { num: t('focus_2_num'), title: t('focus_2_title'), desc: t('focus_2_desc'), keys: t('focus_2_keys') },
    { num: t('focus_3_num'), title: t('focus_3_title'), desc: t('focus_3_desc'), keys: t('focus_3_keys') },
  ];
  return (
    <RevealSection id="focus" className="bg-surface/20">
      <SectionHeader num={t('focus_num')} eyebrow={t('focus_eyebrow')}
        title={t('focus_title')} intro={t('focus_intro')} split />
      <motion.div variants={stagger} initial="hidden" whileInView="visible"
        viewport={{ once: true, amount: 0.15 }}
        className="grid gap-5 md:grid-cols-3">
        {cards.map(c => (
          <motion.article key={c.num} variants={cardAnim} data-cursor="accent"
            whileHover={{ y: -6 }}
            className="hover-glow relative overflow-hidden rounded-lg border border-border bg-surface/78 p-6 shadow-sm backdrop-blur-xl transition hover:border-primary/55 hover:shadow-glow">
            <span className="text-sm font-black text-honey">{c.num}</span>
            <h3 className="mt-4 text-xl font-black text-foreground">{c.title}</h3>
            <p className="mt-3 text-sm leading-7 text-muted">{c.desc}</p>
            <p className="mt-4 text-xs font-black tracking-wider text-primary">{c.keys}</p>
          </motion.article>
        ))}
      </motion.div>
    </RevealSection>
  );
}

// ── Projects ──────────────────────────────────────────────────────────
function Projects({ lang, t }) {
  const projects = PROJECTS[lang];
  return (
    <RevealSection id="projects" className="pt-16">
      <SectionHeader num={t('projects_num')} eyebrow={t('projects_eyebrow')}
        title={t('projects_title')} intro={t('projects_intro')} split />
      <motion.div variants={stagger} initial="hidden" whileInView="visible"
        viewport={{ once: true, amount: 0.1 }}
        className="grid gap-8">
        {projects.map(p => (
          <ProjectCard key={p.id} project={p} t={t} />
        ))}
      </motion.div>
    </RevealSection>
  );
}

function ProjectCard({ project: p, t }) {
  const [activeImg, setActiveImg] = useState(0);

  const statusLabel = p.status === 'live' ? t('status_live')
    : p.status === 'building' ? t('status_building') : t('status_concept');
  const statusColor = p.status === 'live'
    ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-400'
    : p.status === 'building'
    ? 'border-honey/30 bg-honey/10 text-honey'
    : 'border-border bg-surface/50 text-muted';

  return (
    <motion.article variants={cardAnim} data-cursor="accent"
      className="project-shell console-panel relative overflow-hidden rounded-lg border border-border bg-surface/78 shadow-premium backdrop-blur-xl transition hover:border-primary/55">
      <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-primary via-honey to-electric" />

      <div className="grid gap-0 lg:grid-cols-[0.9fr_1.1fr]">
        {/* Left: project info */}
        <div className="flex flex-col p-5 sm:p-8 lg:p-10">
          <div className="mb-4 flex flex-wrap items-center gap-2 sm:mb-5 sm:gap-3">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-muted">{p.eyebrow}</span>
            <span className={`rounded-md border px-2.5 py-1 text-xs font-bold ${statusColor}`}>
              {statusLabel}
            </span>
            <span className="ml-auto text-xs text-muted">{p.year}</span>
          </div>
          <h3 className="text-2xl font-black text-foreground sm:text-3xl">{p.name}</h3>
          <p className="mt-3 text-sm leading-7 text-muted">{p.summary}</p>

          {/* Problem / Solution / Impact */}
          <div className="mt-6 grid gap-3 sm:mt-7 sm:gap-4">
            {[
              { label: t('project_problem'),  text: p.problem },
              { label: t('project_solution'), text: p.solution },
              { label: t('project_impact'),   text: p.impact },
            ].map(pt => (
              <div key={pt.label} className="rounded-md border-l-2 border-primary/40 bg-background/35 py-2 pl-4 pr-3">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-primary">{pt.label}</p>
                <p className="mt-1 text-sm leading-6 text-muted">{pt.text}</p>
              </div>
            ))}
          </div>

          {/* Tags */}
          <div className="mt-6 flex flex-wrap gap-2">
            {p.tags.map(tag => (
              <span key={tag}
                className="rounded-md border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
                {tag}
              </span>
            ))}
          </div>

          <a
            href="#contact"
            className="mt-5 inline-flex w-fit rounded-md border border-border bg-background/50 px-3 py-2 text-xs font-bold text-muted transition hover:border-honey/50 hover:text-foreground"
          >
            {t('project_no_links')}
          </a>
        </div>

        {/* Right: image gallery */}
        <div className="flex flex-col gap-3 border-t border-border bg-background/24 p-3 sm:gap-4 sm:p-4 lg:border-l lg:border-t-0 lg:p-6">
          {/* Main image */}
          <div className="project-screen relative flex h-[18rem] items-center justify-center overflow-hidden rounded-lg border border-border bg-background/70 p-3 sm:h-[27rem] sm:p-4 lg:h-[33rem]">
            <img src={p.images[activeImg].src} alt={p.images[activeImg].alt}
              className="h-full max-h-full w-auto max-w-full object-contain transition duration-300"
              loading="lazy" />
          </div>
          {/* Thumbnails */}
          <div className="flex gap-2 overflow-x-auto pb-1 sm:grid sm:grid-cols-5 sm:overflow-x-visible">
            {p.images.map((img, i) => (
              <button key={i} type="button" onClick={() => setActiveImg(i)}
                className={`shrink-0 overflow-hidden rounded-md border-2 bg-background/60 transition sm:shrink ${i === activeImg ? 'border-honey shadow-[0_0_14px_rgba(250,204,21,0.4)]' : 'border-border hover:border-primary/50'}`}>
                <img src={img.src} alt={img.alt}
                  className="h-14 w-14 object-cover sm:h-auto sm:w-full sm:aspect-square"
                  loading="lazy" />
              </button>
            ))}
          </div>
          <p className="text-center text-xs text-muted">{p.images[activeImg].alt}</p>
        </div>
      </div>
    </motion.article>
  );
}

// ── Skills ────────────────────────────────────────────────────────────
function Skills({ t }) {
  return (
    <RevealSection id="skills" className="bg-surface/20">
      <SectionHeader num={t('skills_num')} eyebrow={t('skills_eyebrow')} title={t('skills_title')} />
      <motion.div variants={stagger} initial="hidden" whileInView="visible"
        viewport={{ once: true, amount: 0.15 }}
        className="grid gap-5 md:grid-cols-3">
        {SKILLS.map((group, i) => (
          <motion.div key={group.category_key} variants={cardAnim} data-cursor="accent"
            className="rounded-lg border border-border bg-surface/72 p-6 shadow-sm backdrop-blur-xl transition hover:border-primary/55 hover:shadow-glow">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-black text-foreground">{t(group.category_key)}</h3>
              <span className="text-sm font-black text-honey">0{i + 1}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {group.items.map(skill => (
                <span key={skill}
                  className="rounded-md border border-border bg-background/55 px-3 py-2 text-sm font-semibold text-muted transition hover:border-honey/50 hover:text-foreground">
                  {skill}
                </span>
              ))}
            </div>
          </motion.div>
        ))}
      </motion.div>
    </RevealSection>
  );
}

// ── Contact ───────────────────────────────────────────────────────────
function Contact({ t }) {
  const links = [
    { key: 'contact_email',    value: SITE.email,       href: `mailto:${SITE.email}` },
    { key: 'contact_github',   value: SITE.githubLabel, href: SITE.github },
    { key: 'contact_phone',    value: SITE.phone,       href: SITE.phoneLink },
    { key: 'contact_line',     value: SITE.line,        href: SITE.lineLink },
    { key: 'contact_location', value: SITE.location,    href: null },
  ];

  return (
    <RevealSection id="contact">
      <motion.div initial={{ opacity: 0, scale: 0.97 }} whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true, amount: 0.25 }}
        transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        className="relative overflow-hidden rounded-lg border border-primary/30 bg-surface/86 p-6 shadow-premium backdrop-blur-2xl sm:p-8 lg:p-10">
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary via-honey to-electric" />
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
          {/* Left copy */}
          <div>
            <span className="text-xs font-black uppercase tracking-[0.22em] text-primary">
              {t('contact_num')} — {t('contact_eyebrow')}
            </span>
            <h2 className="mt-4 text-3xl font-black tracking-normal text-foreground sm:text-4xl">
              {t('contact_title')}
            </h2>
            <p className="mt-4 text-sm leading-7 text-muted">{t('contact_lead')}</p>
            <div className="mt-5 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400"
                style={{ animation: 'statusPulse 2.4s ease-in-out infinite' }} />
              <span className="text-sm text-muted">{t('contact_status')}</span>
            </div>
          </div>

          {/* Right links */}
          <div className="rounded-lg border border-border bg-background/60 p-5">
            <div className="grid gap-2">
              {links.map(({ key, value, href }) => {
                const inner = (
                  <span className="flex items-center justify-between gap-4">
                    <span>
                      <span className="block text-xs font-black uppercase tracking-[0.18em] text-primary">{t(key)}</span>
                      <span className="mt-0.5 block break-words text-sm font-semibold text-foreground [overflow-wrap:anywhere]">{value}</span>
                    </span>
                    {href && <span className="text-honey transition group-hover:translate-x-1">→</span>}
                  </span>
                );
                return href ? (
                  <a key={key} href={href} target={href.startsWith('http') ? '_blank' : undefined}
                    rel={href.startsWith('http') ? 'noopener noreferrer' : undefined}
                    className="group rounded-lg border border-border bg-surface/60 px-4 py-3 transition hover:border-honey/50 hover:bg-primary/10">
                    {inner}
                  </a>
                ) : (
                  <div key={key} className="rounded-lg border border-border bg-surface/60 px-4 py-3">
                    {inner}
                  </div>
                );
              })}
            </div>
            <a href={`mailto:${SITE.email}`}
              className="mt-5 flex w-full items-center justify-center rounded-lg bg-honey px-6 py-3 text-sm font-black text-slate-950 shadow-[0_0_32px_rgba(250,204,21,0.26)] transition hover:-translate-y-0.5 hover:bg-honey/90">
              {t('contact_cta')}
            </a>
          </div>
        </div>
      </motion.div>
    </RevealSection>
  );
}

// ── Footer ────────────────────────────────────────────────────────────
function Footer({ theme, t }) {
  const logoSrc = theme === 'dark'
    ? '/assets/images/sparx-logo-web-white.png'
    : '/assets/images/sparx-logo-web-black.png';
  return (
    <footer className="relative z-10 border-t border-border bg-background/80 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-3 text-center sm:flex-row sm:justify-between">
        <span className="flex items-center gap-2">
          <img src={logoSrc} alt="SPARX" className="h-5 w-auto opacity-70" />
          <span className="text-xs text-muted">© {new Date().getFullYear()} {SITE.owner}</span>
        </span>
        <span className="text-xs text-muted">{t('footer_text')}</span>
      </div>
    </footer>
  );
}

// ── App root ──────────────────────────────────────────────────────────
export default function App() {
  const { theme, toggleTheme } = useTheme();
  const { lang, toggleLang, t } = useLanguage();

  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
      <InteractiveBackground />
      <Header theme={theme} toggleTheme={toggleTheme} t={t} toggleLang={toggleLang} />
      <main>
        <Hero t={t} />
        <Projects lang={lang} t={t} />
        <About t={t} />
        <Focus t={t} />
        <Skills t={t} />
        <Contact t={t} />
      </main>
      <Footer theme={theme} t={t} />
    </div>
  );
}
