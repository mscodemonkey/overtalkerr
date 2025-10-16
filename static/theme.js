/**
 * Theme Management for Overtalkerr
 * Supports light, dark, and auto (system preference) modes
 */

class ThemeManager {
  constructor() {
    this.currentTheme = 'auto'; // 'light', 'dark', or 'auto'
    this.systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)');

    // Load theme from localStorage or config
    this.loadTheme();

    // Listen for system theme changes
    this.systemPrefersDark.addEventListener('change', (e) => {
      if (this.currentTheme === 'auto') {
        this.applyTheme();
      }
    });
  }

  /**
   * Load theme preference from localStorage or fetch from server config
   */
  async loadTheme() {
    // Try localStorage first (faster)
    const stored = localStorage.getItem('overtalkerr_theme');
    if (stored && ['light', 'dark', 'auto'].includes(stored)) {
      this.currentTheme = stored;
      this.applyTheme();
      return;
    }

    // Fetch from server config as fallback
    try {
      const response = await fetch('/api/config');
      if (response.ok) {
        const config = await response.json();
        if (config.UI_THEME) {
          this.currentTheme = config.UI_THEME;
          localStorage.setItem('overtalkerr_theme', this.currentTheme);
        }
      }
    } catch (e) {
      console.warn('Could not load theme from server, using default:', e);
    }

    this.applyTheme();
  }

  /**
   * Set and apply a new theme
   * @param {string} theme - 'light', 'dark', or 'auto'
   */
  setTheme(theme) {
    if (!['light', 'dark', 'auto'].includes(theme)) {
      console.error('Invalid theme:', theme);
      return;
    }

    this.currentTheme = theme;
    localStorage.setItem('overtalkerr_theme', theme);
    this.applyTheme();
  }

  /**
   * Get the effective theme (resolves 'auto' to 'light' or 'dark')
   */
  getEffectiveTheme() {
    if (this.currentTheme === 'auto') {
      return this.systemPrefersDark.matches ? 'dark' : 'light';
    }
    return this.currentTheme;
  }

  /**
   * Apply the current theme to the document
   */
  applyTheme() {
    const effective = this.getEffectiveTheme();
    document.documentElement.setAttribute('data-theme', effective);

    // Dispatch event for components that need to react to theme changes
    window.dispatchEvent(new CustomEvent('themechange', {
      detail: { theme: this.currentTheme, effective }
    }));
  }

  /**
   * Get current theme setting
   */
  getTheme() {
    return this.currentTheme;
  }
}

// Initialize theme manager globally
const themeManager = new ThemeManager();

// Expose globally for easy access
window.themeManager = themeManager;
