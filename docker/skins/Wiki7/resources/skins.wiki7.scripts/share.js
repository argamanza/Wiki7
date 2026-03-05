/**
 * @param {Object} deps
 * @param {Document} deps.document
 * @param {Window} deps.window
 * @param {Object} deps.mw
 * @param {Object} deps.navigator
 * @return {Object}
 */
function createShare( { document, window, mw, navigator } ) {
	/**
	 * Initializes the share button functionality for Wiki7
	 *
	 * @return {void}
	 */
	function init() {
		const shareButton = document.getElementById( 'wiki7-share' );
		if ( !shareButton ) {
			// Wiki7 will not add the wiki7-share element if the share button is undesirable
			return;
		}

		const canonicalLink = document.querySelector( 'link[rel="canonical"]' );
		const url = canonicalLink ? canonicalLink.href : window.location.href;
		const shareData = {
			title: document.title,
			url: url
		};

		const handleShareButtonClick = async () => {
			shareButton.disabled = true; // Disable the button
			try {
				if ( navigator.share ) {
					await navigator.share( shareData );
				} else if ( navigator.clipboard ) {
					// Fallback to navigator.clipboard if Share API is not supported
					await navigator.clipboard.writeText( url );
					mw.notify( mw.msg( 'wiki7-share-copied' ), {
						tag: 'wiki7-share',
						type: 'success'
					} );
				}
			} catch ( error ) {
				mw.log.error( `[Wiki7] ${ error }` );
			} finally {
				shareButton.disabled = false; // Re-enable button after error or share completes
			}
		};

		shareButton.addEventListener( 'click', mw.util.debounce( handleShareButtonClick, 100 ) );
	}

	return { init };
}

module.exports = { createShare };
