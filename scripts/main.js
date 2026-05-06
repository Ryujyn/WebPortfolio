(function () {
  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  function setupRevealObserver() {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      document.querySelectorAll("[data-reveal]").forEach((el) => el.classList.add("revealed"));
      window.RevealObserver = {
        observe(el) {
          el.classList.add("revealed");
        },
      };
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );

    window.RevealObserver = observer;
    document.querySelectorAll("[data-reveal]").forEach((el) => observer.observe(el));
  }

  function setupNav() {
    const nav = document.getElementById("nav");
    if (!nav) return;

    const update = () => nav.classList.toggle("scrolled", window.scrollY > 8);
    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  function setupActiveLink() {
    const sections = document.querySelectorAll("main section[id]");
    const navLinks = document.querySelectorAll('.nav__link[href^="#"], .mobile-menu__link[href^="#"]');
    if (!sections.length || !navLinks.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            navLinks.forEach((link) => {
              link.classList.toggle("active", link.getAttribute("href") === `#${id}`);
            });
          }
        });
      },
      { rootMargin: "-40% 0px -55% 0px", threshold: 0.01 }
    );

    sections.forEach((s) => observer.observe(s));
  }

  function setupMobileMenu() {
    const menuBtn = document.getElementById("menu-toggle");
    const mobileMenu = document.getElementById("mobile-menu");
    if (!menuBtn || !mobileMenu) return;

    function close() {
      mobileMenu.classList.remove("open");
      menuBtn.classList.remove("open");
      menuBtn.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    }

    menuBtn.addEventListener("click", () => {
      const willOpen = !mobileMenu.classList.contains("open");
      mobileMenu.classList.toggle("open", willOpen);
      menuBtn.classList.toggle("open", willOpen);
      menuBtn.setAttribute("aria-expanded", String(willOpen));
      document.body.style.overflow = willOpen ? "hidden" : "";
    });

    mobileMenu.querySelectorAll(".mobile-menu__link").forEach((link) => {
      link.addEventListener("click", close);
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 900) close();
    });
  }

  function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", (e) => {
        const href = anchor.getAttribute("href");
        if (!href || href === "#") return;
        const target = document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        const navH =
          parseInt(getComputedStyle(document.documentElement).getPropertyValue("--nav-h"), 10) || 72;
        const top = target.getBoundingClientRect().top + window.scrollY - navH - 12;
        window.scrollTo({ top, behavior: "smooth" });
      });
    });
  }

  function setupThemeButton() {
    const btn = document.getElementById("theme-toggle");
    if (!btn || !window.ThemeManager) return;
    btn.addEventListener("click", () => window.ThemeManager.toggle());
  }

  function setupYear() {
    const node = document.getElementById("footer-year");
    if (node) node.textContent = new Date().getFullYear();
  }

  ready(() => {
    setupRevealObserver();
    setupNav();
    setupActiveLink();
    setupMobileMenu();
    setupSmoothScroll();
    setupThemeButton();
    setupYear();
  });
})();
