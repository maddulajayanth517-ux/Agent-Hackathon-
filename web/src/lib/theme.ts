export type Theme = "light" | "dark";

const STORAGE_KEY = "mentorflow_theme";

export function applyTheme(theme: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
  try {
    window.localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Private browsing / storage disabled — theme still applies for this session.
  }
}
