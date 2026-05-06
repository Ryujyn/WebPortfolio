(function () {
  const STORAGE_KEY = "ryujyn:theme";
  const root = document.documentElement;

  function resolveInitial() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "light" || saved === "dark") return saved;
    } catch (_) {}
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  function apply(theme) {
    root.dataset.theme = theme;
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {}
  }

  apply(resolveInitial());

  window.ThemeManager = {
    get current() {
      return root.dataset.theme;
    },
    set(theme) {
      if (theme !== "light" && theme !== "dark") return;
      apply(theme);
    },
    toggle() {
      apply(root.dataset.theme === "dark" ? "light" : "dark");
    },
  };
})();
