(() => {
    window.reportScriptLoads = (window.reportScriptLoads || 0) + 1;
    const initialize = () => {
        const output = document.getElementById('report-status');
        if (output) output.textContent = 'Report ready';
    };
    document.addEventListener('admin-htmx:load', initialize);
    initialize();
})();
