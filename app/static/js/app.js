/**
 * Cat Bond Portfolio Optimizer — Client-side JavaScript
 *
 * Provides utility functions used across templates:
 *  - Tab switching
 *  - Toast auto-dismiss
 *  - HTMX event hooks
 */

"use strict";

/* ── Tab switching (called from optimization_results.html) ── */
window.switchTab = window.switchTab || function(btn, panelId) {
    document.querySelectorAll('.tab-btn').forEach(function(t) {
        t.classList.remove('border-navy', 'text-navy', 'bg-white');
        t.classList.add('border-transparent', 'text-gray-500');
        t.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-panel').forEach(function(p) {
        p.classList.add('hidden');
    });
    btn.classList.add('border-navy', 'text-navy', 'bg-white');
    btn.classList.remove('border-transparent', 'text-gray-500');
    btn.setAttribute('aria-selected', 'true');
    var panel = document.getElementById(panelId);
    if (panel) {
        panel.classList.remove('hidden');
    }
    /* Trigger resize so Plotly charts re-fit to container */
    setTimeout(function() {
        window.dispatchEvent(new Event('resize'));
    }, 50);
};