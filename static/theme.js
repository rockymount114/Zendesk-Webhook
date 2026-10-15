/**
 * Rocky Mount Service Desk - Theme Management
 * Supports 'light', 'dark', and 'auto' (system preference).
 * Dispatches 'app-theme-changed' custom event when theme changes.
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'theme';
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function getSavedThemeSetting() {
        try {
            return localStorage.getItem(STORAGE_KEY) || 'auto';
        } catch (e) {
            return 'auto';
        }
    }

    function resolveTheme(setting) {
        if (setting === 'dark') return 'dark';
        if (setting === 'light') return 'light';
        return mediaQuery.matches ? 'dark' : 'light';
    }

    function applyTheme(setting, animate) {
        const resolved = resolveTheme(setting);
        const root = document.documentElement;

        if (animate) {
            root.classList.add('theme-transitioning');
            window.clearTimeout(applyTheme._animTimeout);
            applyTheme._animTimeout = window.setTimeout(function () {
                root.classList.remove('theme-transitioning');
            }, 250);
        }

        root.setAttribute('data-theme', resolved);
        root.setAttribute('data-theme-setting', setting);
        root.style.colorScheme = resolved;

        // Update UI buttons if present
        const buttons = document.querySelectorAll('.theme-btn');
        buttons.forEach(function (btn) {
            const val = btn.getAttribute('data-theme-value');
            const isActive = val === setting;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-checked', isActive ? 'true' : 'false');
        });

        // Dispatch custom event for charts and dynamic components
        window.dispatchEvent(new CustomEvent('app-theme-changed', {
            detail: {
                theme: resolved,
                setting: setting
            }
        }));
    }

    function setTheme(setting) {
        try {
            localStorage.setItem(STORAGE_KEY, setting);
        } catch (e) {}
        applyTheme(setting, true);
    }

    // Initialize on DOM ready
    function initTheme() {
        const currentSetting = getSavedThemeSetting();
        applyTheme(currentSetting, false);

        // Bind click events on theme selector buttons
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.theme-btn');
            if (!btn) return;
            const targetSetting = btn.getAttribute('data-theme-value');
            if (targetSetting) {
                setTheme(targetSetting);
            }
        });

        // Listen for OS system theme shifts if in 'auto' mode
        if (mediaQuery && mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', function () {
                if (getSavedThemeSetting() === 'auto') {
                    applyTheme('auto', true);
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }

    window.ThemeManager = {
        getSetting: getSavedThemeSetting,
        setTheme: setTheme,
        getResolvedTheme: function () {
            return resolveTheme(getSavedThemeSetting());
        }
    };
})();
