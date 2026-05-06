(function () {
  const STORAGE_KEY = "ryujyn:lang";
  const root = document.documentElement;

  const STATUS_MAP = {
    live: { key: "project_status_live", cls: "badge--live" },
    building: { key: "project_status_building", cls: "badge--building" },
    concept: { key: "project_status_concept", cls: "badge--concept" },
  };

  function readLang() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "th" || saved === "en") return saved;
    } catch (_) {}
    return root.getAttribute("lang") === "en" ? "en" : "th";
  }

  function persistLang(lang) {
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (_) {}
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function applySiteData() {
    document.querySelectorAll("[data-site]").forEach((el) => {
      const key = el.getAttribute("data-site");
      if (key === "githubLabel") {
        el.textContent = SITE.githubLabel || SITE.github.replace(/^https?:\/\//, "");
        return;
      }
      if (SITE[key] !== undefined) el.textContent = SITE[key];
    });
    document.querySelectorAll("[data-site-href]").forEach((el) => {
      const key = el.getAttribute("data-site-href");
      if (SITE[key]) el.href = SITE[key];
    });
  }

  function applyLang(lang) {
    const dict = CONTENT[lang] || CONTENT.th;

    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang === "th" ? "th" : "en");
    persistLang(lang);

    document.querySelectorAll("[data-key]").forEach((el) => {
      const key = el.getAttribute("data-key");
      if (dict[key] !== undefined) el.textContent = dict[key];
    });

    const langLabel = document.getElementById("lang-label");
    if (langLabel) langLabel.textContent = lang === "th" ? "EN" : "TH";

    applySiteData();
    renderProjects(lang);
    renderSkills(lang);
  }

  function renderMockup(project, dict) {
    if (!project.mockup || project.mockup.type === "placeholder") {
      return `
        <div class="mockup mockup--placeholder" aria-hidden="true">
          <div class="mockup__chrome">
            <span class="mockup__dot"></span>
            <span class="mockup__dot"></span>
            <span class="mockup__dot"></span>
            <span class="mockup__url">${escapeHtml(project.id)}.app/dashboard</span>
          </div>
          <div class="mockup__body">
            <div class="mockup__head">
              <span class="mockup__head-label">${escapeHtml(project.name)}</span>
              <span class="mockup__head-badge">${escapeHtml(dict.project_mockup_caption)}</span>
            </div>
            <div class="mockup__rows">
              <div class="mockup__row"><span></span><i style="width:30%"></i></div>
              <div class="mockup__row"><span></span><i style="width:72%"></i></div>
              <div class="mockup__row"><span></span><i style="width:48%"></i></div>
            </div>
          </div>
        </div>`;
    }
    if (project.mockup.type === "image" && project.mockup.src) {
      return `
        <div class="mockup mockup--image">
          <img src="${escapeHtml(project.mockup.src)}" alt="${escapeHtml(project.mockup.alt || project.name)}" loading="lazy">
        </div>`;
    }
    if (project.mockup.type === "gallery" && Array.isArray(project.mockup.images)) {
      const imgs = project.mockup.images
        .map((img) => `<img src="${escapeHtml(img.src)}" alt="${escapeHtml(img.alt || project.name)}" loading="lazy">`)
        .join("");
      return `<div class="mockup--gallery">${imgs}</div>`;
    }
    return "";
  }

  function renderProjectLinks(project, dict) {
    const items = [];
    if (project.link)
      items.push(
        `<a href="${escapeHtml(project.link)}" target="_blank" rel="noopener" class="project-link project-link--primary">${escapeHtml(dict.project_visit)} <span aria-hidden="true">→</span></a>`
      );
    if (project.demo)
      items.push(
        `<a href="${escapeHtml(project.demo)}" target="_blank" rel="noopener" class="project-link">${escapeHtml(dict.project_demo)}</a>`
      );
    if (project.github)
      items.push(
        `<a href="${escapeHtml(project.github)}" target="_blank" rel="noopener" class="project-link">${escapeHtml(dict.project_github)}</a>`
      );

    if (items.length === 0) {
      return `<a href="#contact" class="project-card__no-links-btn">${escapeHtml(dict.project_no_links)}</a>`;
    }
    return `<div class="project-card__links">${items.join("")}</div>`;
  }

  function renderProjects(lang) {
    const grid = document.getElementById("projects-grid");
    if (!grid) return;

    const dict = CONTENT[lang] || CONTENT.th;
    const projects = PROJECTS[lang] || PROJECTS.th;

    grid.innerHTML = projects
      .map((project) => {
        const status = STATUS_MAP[project.status] || STATUS_MAP.building;
        const stackRows = project.stack
          .map(
            ([label, value]) => `
              <div class="stack-row">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
              </div>`
          )
          .join("");

        const tags = project.tags
          .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
          .join("");

        const yearLine = project.year
          ? `<span class="project-card__year">${escapeHtml(project.year)}</span>`
          : "";

        return `
          <article class="project-card" data-reveal>
            <header class="project-card__head">
              <div class="project-card__head-left">
                <p class="project-card__eyebrow">${escapeHtml(project.eyebrow)}</p>
                <h3 class="project-card__title">${escapeHtml(project.name)}</h3>
              </div>
              <div class="project-card__head-right">
                ${yearLine}
                <span class="badge ${status.cls}">
                  <span class="badge__dot"></span>
                  ${escapeHtml(dict[status.key])}
                </span>
              </div>
            </header>

            <div class="project-card__visual">
              ${renderMockup(project, dict)}
            </div>

            <p class="project-card__summary">${escapeHtml(project.summary)}</p>

            <div class="project-card__body">
              <div class="case-grid">
                <section>
                  <span class="case-grid__label">${escapeHtml(dict.project_problem)}</span>
                  <p>${escapeHtml(project.problem)}</p>
                </section>
                <section>
                  <span class="case-grid__label">${escapeHtml(dict.project_solution)}</span>
                  <p>${escapeHtml(project.solution)}</p>
                </section>
                <section>
                  <span class="case-grid__label">${escapeHtml(dict.project_impact)}</span>
                  <p>${escapeHtml(project.impact)}</p>
                </section>
              </div>

              <aside class="stack-card">
                <h4>${escapeHtml(dict.project_stack)}</h4>
                <div class="stack-rows">${stackRows}</div>
              </aside>
            </div>

            <footer class="project-card__footer">
              <div class="project-card__tags">${tags}</div>
              ${renderProjectLinks(project, dict)}
            </footer>
          </article>`;
      })
      .join("");

    observeDynamic("#projects-grid [data-reveal]");
  }

  function renderSkills(lang) {
    const grid = document.getElementById("skills-grid");
    if (!grid) return;

    const dict = CONTENT[lang] || CONTENT.th;

    grid.innerHTML = SKILLS.map(
      (group, index) => `
        <section class="skill-group" data-reveal data-delay="${index + 1}">
          <p class="skill-group__num">${String(index + 1).padStart(2, "0")}</p>
          <h3 class="skill-group__title">${escapeHtml(dict[group.category_key])}</h3>
          <div class="skill-group__items">
            ${group.items.map((item) => `<span class="skill-item">${escapeHtml(item)}</span>`).join("")}
          </div>
        </section>`
    ).join("");

    observeDynamic("#skills-grid [data-reveal]");
  }

  function observeDynamic(selector) {
    if (!window.RevealObserver) return;
    document.querySelectorAll(selector).forEach((el) => {
      if (!el.classList.contains("revealed")) window.RevealObserver.observe(el);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("lang-toggle");
    if (btn) {
      btn.addEventListener("click", () => {
        const next = readLang() === "th" ? "en" : "th";
        applyLang(next);
      });
    }
    applyLang(readLang());
  });

  window.I18n = {
    apply: applyLang,
    get current() {
      return readLang();
    },
  };
})();
