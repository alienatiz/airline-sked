const THEME_KEY = "airline-sked-theme";

function getStoredTheme() {
  return window.localStorage.getItem(THEME_KEY);
}

function getSystemTheme() {
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function getActiveTheme() {
  return document.documentElement.getAttribute("data-theme") || getStoredTheme() || getSystemTheme();
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

function updateThemeButtons() {
  const theme = getActiveTheme();
  const icon = theme === "light" ? "SUN" : "MOON";
  const label = theme === "light" ? "LIGHT" : "DARK";

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.setAttribute("aria-pressed", String(theme === "light"));
    button.setAttribute("aria-label", `Switch to ${theme === "light" ? "dark" : "light"} mode`);

    const iconNode = button.querySelector("[data-theme-icon]");
    const labelNode = button.querySelector("[data-theme-label]");

    if (iconNode) iconNode.textContent = icon;
    if (labelNode) labelNode.textContent = label;
  });
}

function setTheme(theme, persist = true) {
  applyTheme(theme);
  if (persist) {
    window.localStorage.setItem(THEME_KEY, theme);
  }
  updateThemeButtons();
}

function toggleTheme() {
  setTheme(getActiveTheme() === "light" ? "dark" : "light");
}

document.addEventListener("DOMContentLoaded", () => {
  updateThemeButtons();

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", toggleTheme);
  });
});

window.addEventListener("storage", (event) => {
  if (event.key !== THEME_KEY) return;
  setTheme(event.newValue || getSystemTheme(), false);
});

window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", (event) => {
  if (getStoredTheme()) return;
  setTheme(event.matches ? "light" : "dark", false);
});
