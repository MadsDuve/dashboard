/* Auto-refresh: reload the page every 5 minutes so data stays current.
   Dash serves a fresh layout (with new API calls) on each full page load. */
(function () {
    var INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
    setTimeout(function () {
        window.location.reload();
    }, INTERVAL_MS);
})();
