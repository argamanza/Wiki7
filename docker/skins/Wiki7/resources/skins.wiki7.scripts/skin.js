/**
 * Lazy-load images that are below the fold using IntersectionObserver (v3.8.0+)
 * This improves initial page load performance by deferring off-screen images
 *
 * @return {void}
 */
function initLazyLoading() {
	// Skip if native lazy loading is sufficient or IntersectionObserver is unavailable
	if ( !( 'IntersectionObserver' in window ) ) {
		return;
	}

	const config = require( './config.json' );
	if ( config.wgWiki7EnablePerformanceMode !== true ) {
		return;
	}

	const lazyImages = document.querySelectorAll( '.mw-parser-output img[loading="lazy"]' );
	if ( !lazyImages.length ) {
		return;
	}

	const imageObserver = new IntersectionObserver( ( entries ) => {
		entries.forEach( ( entry ) => {
			if ( entry.isIntersecting ) {
				const img = /** @type {HTMLImageElement} */ ( entry.target );
				if ( img.dataset.src ) {
					img.src = img.dataset.src;
					delete img.dataset.src;
				}
				if ( img.dataset.srcset ) {
					img.srcset = img.dataset.srcset;
					delete img.dataset.srcset;
				}
				img.classList.remove( 'wiki7-lazy' );
				imageObserver.unobserve( img );
			}
		} );
	}, {
		rootMargin: '200px 0px' // Start loading 200px before the image enters viewport
	} );

	lazyImages.forEach( ( img ) => {
		imageObserver.observe( img );
	} );
}

/**
 * @return {void}
 */
function deferredTasks() {
	const
		setupObservers = require( './setupObservers.js' ),
		speculationRules = require( './speculationRules.js' );

	setupObservers.main();
	speculationRules.init();
	registerServiceWorker();
	initLazyLoading();

	window.addEventListener( 'beforeunload', () => {
		// Set up loading indicator
		document.documentElement.classList.add( 'wiki7-loading' );
	}, false );

	// Remove loading indicator once the page is unloaded/hidden
	window.addEventListener( 'pagehide', () => {
		document.documentElement.classList.remove( 'wiki7-loading' );
	} );
}

/**
 * Register service worker
 *
 * @return {void}
 */
function registerServiceWorker() {
	const scriptPath = mw.config.get( 'wgScriptPath' );
	// Only allow serviceWorker when the scriptPath is at root because of its scope
	// I can't figure out how to add the Service-Worker-Allowed HTTP header
	// to change the default scope
	if ( scriptPath !== '' ) {
		return;
	}

	if ( 'serviceWorker' in navigator ) {
		const SW_MODULE_NAME = 'skins.wiki7.serviceWorker',
			version = mw.loader.moduleRegistry[ SW_MODULE_NAME ].version,
			// HACK: Faking a RL link
			swUrl = scriptPath +
				'/load.php?modules=' + SW_MODULE_NAME +
				'&only=scripts&raw=true&skin=wiki7&version=' + version;
		navigator.serviceWorker.register( swUrl, { scope: '/' } );
	}
}

/**
 * Initialize scripts related to wiki page content
 *
 * @param {HTMLElement} bodyContent
 * @return {void}
 */
function initBodyContent( bodyContent ) {
	const
		sections = require( './sections.js' ),
		overflowElements = require( './overflowElements.js' );

	// Collapsable sections
	sections.init( bodyContent );
	// Overflow element enhancements
	overflowElements.init( bodyContent );
}

/**
 * @param {Window} window
 * @return {void}
 */
function main( window ) {
	const
		config = require( './config.json' ),
		echo = require( './echo.js' ),
		search = require( './search.js' ),
		dropdown = require( './dropdown.js' ),
		lastModified = require( './lastModified.js' ),
		share = require( './share.js' );

	dropdown.init();
	search.init( window );
	echo();
	lastModified.init();
	share.init();

	mw.hook( 'wikipage.content' ).add( ( content ) => {
		// content is a jQuery object
		// note that this refers to .mw-body-content, not #bodyContent
		initBodyContent( content[ 0 ] );
	} );

	// Preference module
	if ( config.wgWiki7EnablePreferences === true ) {
		mw.loader.load( 'skins.wiki7.preferences' );
	}

	// Defer non-essential tasks
	mw.requestIdleCallback( deferredTasks, { timeout: 3000 } );
}

if ( document.readyState === 'interactive' || document.readyState === 'complete' ) {
	main( window );
} else {
	document.addEventListener( 'DOMContentLoaded', () => {
		main( window );
	} );
}
