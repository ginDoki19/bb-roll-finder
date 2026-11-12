/* maps.js
 * Google Maps links for exam centres. The embedded iframe is built in app.js
 * when a centre row is expanded.
 */
const mapsUrl = q => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
