/**
 * Wiki7 Service Worker
 * Provides offline support and caching strategies for improved performance
 *
 * Cache-first: Static assets (JS, CSS, images, fonts)
 * Network-first: HTML pages and API calls
 * Offline fallback: Shows a basic offline page when network is unavailable
 */

const CACHE_VERSION = 'wiki7-v1';
const STATIC_CACHE = CACHE_VERSION + '-static';
const PAGES_CACHE = CACHE_VERSION + '-pages';

/**
 * Static asset file extensions that use cache-first strategy
 */
const STATIC_ASSET_REGEX = /\.(?:js|css|woff2?|ttf|otf|eot|png|jpe?g|gif|svg|ico|webp|avif)(?:\?|$)/i;

/**
 * API endpoint patterns that use network-first strategy
 */
const API_REGEX = /\/(?:api|rest)\.php/i;

/**
 * Offline fallback page HTML
 */
const OFFLINE_PAGE = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Offline</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f8f9fa;color:#202122;padding:1rem}
.offline{text-align:center;max-width:480px}
.offline h1{font-size:1.5rem;margin-bottom:0.5rem}
.offline p{color:#54595d;line-height:1.6;margin-bottom:1rem}
.offline button{padding:0.5rem 1.5rem;background:#36c;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:1rem}
.offline button:hover{background:#447ff5}
@media(prefers-color-scheme:dark){
body{background:#101418;color:#eaecf0}
.offline p{color:#a2a9b1}
}
</style>
</head>
<body>
<div class="offline">
<h1>You are offline</h1>
<p>This page is not available offline. Please check your internet connection and try again.</p>
<button onclick="location.reload()">Retry</button>
</div>
</body>
</html>`;

self.addEventListener( 'install', ( event ) => {
	event.waitUntil(
		caches.open( STATIC_CACHE ).then( ( cache ) => {
			// Pre-cache the offline fallback page
			return cache.put(
				new Request( '/_offline' ),
				new Response( OFFLINE_PAGE, {
					headers: { 'Content-Type': 'text/html; charset=utf-8' }
				} )
			);
		} ).then( () => {
			// Activate immediately without waiting for existing tabs to close
			return self.skipWaiting();
		} )
	);
} );

self.addEventListener( 'activate', ( event ) => {
	event.waitUntil(
		caches.keys().then( ( cacheNames ) => {
			return Promise.all(
				cacheNames
					.filter( ( name ) => name.startsWith( 'wiki7-' ) && name !== STATIC_CACHE && name !== PAGES_CACHE )
					.map( ( name ) => caches.delete( name ) )
			);
		} ).then( () => {
			// Take control of all open tabs immediately
			return self.clients.claim();
		} )
	);
} );

self.addEventListener( 'fetch', ( event ) => {
	const request = event.request;

	// Only handle GET requests
	if ( request.method !== 'GET' ) {
		return;
	}

	const url = new URL( request.url );

	// Skip cross-origin requests that are not static assets
	if ( url.origin !== self.location.origin && !STATIC_ASSET_REGEX.test( url.pathname ) ) {
		return;
	}

	// Cache-first strategy for static assets (JS, CSS, images, fonts)
	if ( STATIC_ASSET_REGEX.test( url.pathname ) ) {
		event.respondWith( cacheFirst( request, STATIC_CACHE ) );
		return;
	}

	// Network-first strategy for API calls
	if ( API_REGEX.test( url.pathname ) ) {
		event.respondWith( networkFirst( request, PAGES_CACHE ) );
		return;
	}

	// Network-first strategy for HTML/navigation requests
	if ( request.mode === 'navigate' || request.headers.get( 'Accept' )?.includes( 'text/html' ) ) {
		event.respondWith( networkFirstWithOfflineFallback( request, PAGES_CACHE ) );
		return;
	}
} );

/**
 * Cache-first strategy: Try cache, fall back to network, then cache the response
 *
 * @param {Request} request
 * @param {string} cacheName
 * @return {Promise<Response>}
 */
async function cacheFirst( request, cacheName ) {
	const cachedResponse = await caches.match( request );
	if ( cachedResponse ) {
		return cachedResponse;
	}

	try {
		const networkResponse = await fetch( request );
		if ( networkResponse.ok ) {
			const cache = await caches.open( cacheName );
			cache.put( request, networkResponse.clone() );
		}
		return networkResponse;
	} catch ( error ) {
		return new Response( 'Network error', { status: 503, statusText: 'Service Unavailable' } );
	}
}

/**
 * Network-first strategy: Try network, fall back to cache
 *
 * @param {Request} request
 * @param {string} cacheName
 * @return {Promise<Response>}
 */
async function networkFirst( request, cacheName ) {
	try {
		const networkResponse = await fetch( request );
		if ( networkResponse.ok ) {
			const cache = await caches.open( cacheName );
			cache.put( request, networkResponse.clone() );
		}
		return networkResponse;
	} catch ( error ) {
		const cachedResponse = await caches.match( request );
		if ( cachedResponse ) {
			return cachedResponse;
		}
		return new Response( 'Network error', { status: 503, statusText: 'Service Unavailable' } );
	}
}

/**
 * Network-first strategy with offline fallback page for navigation requests
 *
 * @param {Request} request
 * @param {string} cacheName
 * @return {Promise<Response>}
 */
async function networkFirstWithOfflineFallback( request, cacheName ) {
	try {
		const networkResponse = await fetch( request );
		if ( networkResponse.ok ) {
			const cache = await caches.open( cacheName );
			cache.put( request, networkResponse.clone() );
		}
		return networkResponse;
	} catch ( error ) {
		const cachedResponse = await caches.match( request );
		if ( cachedResponse ) {
			return cachedResponse;
		}
		// Return offline fallback page
		const offlineResponse = await caches.match( '/_offline' );
		if ( offlineResponse ) {
			return offlineResponse;
		}
		return new Response( OFFLINE_PAGE, {
			status: 503,
			headers: { 'Content-Type': 'text/html; charset=utf-8' }
		} );
	}
}
