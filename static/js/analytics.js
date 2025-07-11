/**
 * Analytics tracking for AUS Archive
 * Handles page view tracking and other analytics events
 */

document.addEventListener("DOMContentLoaded", function () {
	// Track page view
	const currentPage = window.location.pathname;
	trackPageView(currentPage);

	// Set up event listeners for tracking interactions
	setupEventTracking();
});

/**
 * Track a page view
 * @param {string} page - The page path to track
 */
function trackPageView(page) {
	fetch("/analytics/api/analytics/record-view", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ page: page }),
		// Use non-blocking request
		keepalive: true,
	}).catch((error) => {
		// Silent failure - don't impact user experience
		console.log("Analytics tracking error:", error);
	});
}

/**
 * Set up event listeners for tracking user interactions
 */
function setupEventTracking() {
	// Track external link clicks
	document.querySelectorAll('a[href^="http"]').forEach((link) => {
		link.addEventListener("click", function (e) {
			// Don't block navigation
			const url = this.getAttribute("href");
			const linkText = this.innerText || "external link";

			// Track external link click
			navigator.sendBeacon(
				"/analytics/api/analytics/record-event",
				JSON.stringify({
					event_type: "external_link",
					event_data: { url, linkText },
				})
			);
		});
	});

	// Track file download clicks
	document.querySelectorAll('a[href*="file_link"]').forEach((link) => {
		link.addEventListener("click", function () {
			const fileId = this.getAttribute("data-file-id");
			const fileName = this.getAttribute("data-file-name") || "unknown";

			// Track file download
			navigator.sendBeacon(
				"/analytics/api/analytics/record-event",
				JSON.stringify({
					event_type: "file_download",
					event_data: { fileId, fileName },
				})
			);
		});
	});
}
