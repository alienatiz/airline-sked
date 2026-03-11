const THEME_KEY = "airline-sked-theme";
const LIGHT_THEME = "light";
const DARK_THEME = "dark";

function normalizeTheme(theme) {
  return theme === LIGHT_THEME || theme === DARK_THEME ? theme : null;
}

function getStoredTheme() {
  try {
    return normalizeTheme(window.localStorage.getItem(THEME_KEY));
  } catch (error) {
    return null;
  }
}

function persistTheme(theme) {
  try {
    window.localStorage.setItem(THEME_KEY, theme);
  } catch (error) {
    // Ignore storage failures so theme toggling still works in restricted contexts.
  }
}

function getThemeMediaQuery() {
  if (typeof window.matchMedia !== "function") {
    return null;
  }
  return window.matchMedia("(prefers-color-scheme: light)");
}

function getSystemTheme() {
  const mediaQuery = getThemeMediaQuery();
  return mediaQuery && mediaQuery.matches ? LIGHT_THEME : DARK_THEME;
}

function getActiveTheme() {
  return normalizeTheme(document.documentElement.getAttribute("data-theme")) || getStoredTheme() || getSystemTheme();
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", normalizeTheme(theme) || DARK_THEME);
}

function updateThemeButtons() {
  const activeTheme = getActiveTheme();
  const nextTheme = activeTheme === LIGHT_THEME ? DARK_THEME : LIGHT_THEME;
  const icon = nextTheme === LIGHT_THEME ? "SUN" : "MOON";
  const label = nextTheme.toUpperCase();

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.setAttribute("aria-pressed", String(activeTheme === LIGHT_THEME));
    button.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
    button.setAttribute("title", `Switch to ${nextTheme} mode`);

    const iconNode = button.querySelector("[data-theme-icon]");
    const labelNode = button.querySelector("[data-theme-label]");

    if (iconNode) iconNode.textContent = icon;
    if (labelNode) labelNode.textContent = label;
  });
}

function setTheme(theme, persist = true) {
  const resolvedTheme = normalizeTheme(theme) || getSystemTheme();
  applyTheme(resolvedTheme);
  if (persist) {
    persistTheme(resolvedTheme);
  }
  updateThemeButtons();
}

function toggleTheme() {
  setTheme(getActiveTheme() === LIGHT_THEME ? DARK_THEME : LIGHT_THEME);
}

document.addEventListener("DOMContentLoaded", () => {
  updateThemeButtons();

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", toggleTheme);
  });
});

window.addEventListener("storage", (event) => {
  if (event.key !== THEME_KEY) return;
  setTheme(normalizeTheme(event.newValue) || getSystemTheme(), false);
});

const themeMediaQuery = getThemeMediaQuery();
if (themeMediaQuery) {
  const handleSystemThemeChange = (event) => {
    if (getStoredTheme()) return;
    setTheme(event.matches ? LIGHT_THEME : DARK_THEME, false);
  };

  if (typeof themeMediaQuery.addEventListener === "function") {
    themeMediaQuery.addEventListener("change", handleSystemThemeChange);
  } else if (typeof themeMediaQuery.addListener === "function") {
    themeMediaQuery.addListener(handleSystemThemeChange);
  }
}
