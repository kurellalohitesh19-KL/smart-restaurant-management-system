/**
 * Smart Restaurant Management System
 * SaaS Interactive Dashboard Engine
 *
 * Provides:
 * - Animated KPI counters (requestAnimationFrame + prefers-reduced-motion support)
 * - Standardized Chart.js SaaS theme & helper
 * - Table status grid micro-interactions
 * - Live operational polling & refresh triggers
 */

(function () {
    'use strict';

    // Theme color constants matching the black, cream & gold identity
    window.SmartTheme = {
        gold: '#c59b27',
        goldHover: '#b0871e',
        goldLight: 'rgba(197, 155, 39, 0.15)',
        goldBorder: 'rgba(197, 155, 39, 0.35)',
        charcoal: '#141414',
        surfaceDark: '#1e1e1e',
        cream: '#faf8f5',
        creamAlt: '#f3efe6',
        textPrimary: '#1e2022',
        textMuted: '#70757d',
        border: '#e4dfd5',
        success: '#198754',
        successLight: 'rgba(25, 135, 84, 0.15)',
        warning: '#ffc107',
        warningLight: 'rgba(255, 193, 7, 0.18)',
        danger: '#dc3545',
        dangerLight: 'rgba(220, 53, 69, 0.15)',
        info: '#0dcaf0',
        infoLight: 'rgba(13, 202, 240, 0.15)',
        secondary: '#6c757d'
    };

    /**
     * Animate KPI Numbers smoothly on load.
     * Supports integers and float amounts (e.g. currency).
     */
    function initCounters() {
        const counters = document.querySelectorAll('.smart-counter[data-target]');
        if (!counters.length) return;

        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        counters.forEach(counter => {
            const rawTarget = counter.getAttribute('data-target');
            const target = parseFloat(rawTarget);
            if (isNaN(target)) {
                counter.textContent = rawTarget;
                return;
            }

            const prefix = counter.getAttribute('data-prefix') || '';
            const suffix = counter.getAttribute('data-suffix') || '';
            const isFloat = rawTarget.includes('.');
            const decimals = isFloat ? (rawTarget.split('.')[1] || '').length : 0;

            if (prefersReducedMotion || target === 0) {
                counter.textContent = prefix + (isFloat ? target.toFixed(decimals) : Math.round(target)) + suffix;
                return;
            }

            const duration = 850; // ms
            const startTime = performance.now();

            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease-out cubic
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const currentVal = target * easeOut;

                counter.textContent = prefix + (isFloat ? currentVal.toFixed(decimals) : Math.round(currentVal)) + suffix;

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = prefix + (isFloat ? target.toFixed(decimals) : Math.round(target)) + suffix;
                }
            }

            requestAnimationFrame(updateCounter);
        });
    }

    /**
     * Helper to render standardized SaaS Chart.js visualizations
     */
    window.renderSaaSChart = function (canvasId, config) {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js is not loaded.');
            return null;
        }

        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        // Destroy existing instance if canvas was previously used
        const existing = Chart.getChart(canvas);
        if (existing) {
            existing.destroy();
        }

        // Apply global Chart.js SaaS font and tooltip defaults
        Chart.defaults.font.family = "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        Chart.defaults.color = window.SmartTheme.textPrimary;

        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                        padding: 16,
                        usePointStyle: true,
                        font: {
                            size: 12,
                            weight: 500
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(20, 20, 20, 0.92)',
                    titleColor: '#ffffff',
                    bodyColor: '#f7eed7',
                    borderColor: 'rgba(197, 155, 39, 0.4)',
                    borderWidth: 1,
                    padding: 10,
                    boxPadding: 6,
                    cornerRadius: 8,
                    usePointStyle: true,
                    titleFont: { size: 13, weight: 600 },
                    bodyFont: { size: 12 }
                }
            }
        };

        const mergedOptions = Object.assign({}, baseOptions, config.options || {});
        if (config.options && config.options.plugins) {
            mergedOptions.plugins = Object.assign({}, baseOptions.plugins, config.options.plugins);
        }

        return new Chart(canvas, {
            type: config.type || 'doughnut',
            data: config.data,
            options: mergedOptions
        });
    };

    /**
     * Staggered entrance animations
     */
    function initCardStagger() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) return;

        const cards = document.querySelectorAll('.smart-animate-up');
        cards.forEach((card, index) => {
            const delay = Math.min(index * 60, 450); // ms
            card.style.animationDelay = `${delay}ms`;
        });
    }

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            initCounters();
            initCardStagger();
        });
    } else {
        initCounters();
        initCardStagger();
    }
})();
