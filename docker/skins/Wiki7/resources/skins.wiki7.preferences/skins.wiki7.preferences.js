/**
 * Clientprefs names theme differently from Wiki7, we will need to translate it
 * TODO: Migrate to clientprefs fully on MW 1.43
 */
const CLIENTPREFS_THEME_MAP = {
	auto: 'os',
	light: 'day',
	dark: 'night'
};

const clientPrefs = require( './clientPrefs.polyfill.js' )();

/**
 * Load client preferences based on the existence of 'wiki7-preferences__card' element.
 */
function loadClientPreferences() {
	const clientPreferenceId = 'wiki7-preferences-content';
	const clientPreferenceExists = document.getElementById( clientPreferenceId ) !== null;
	if ( clientPreferenceExists ) {
		const clientPreferences = require( /** @type {string} */( './clientPreferences.js' ) );
		const clientPreferenceConfig = ( require( './clientPreferences.json' ) );

		clientPreferenceConfig[ 'skin-theme' ].callback = () => {
			const LEGACY_THEME_CLASSES = [
				'skin-wiki7-auto',
				'skin-wiki7-light',
				'skin-wiki7-dark'
			];
			const legacyThemeKey = Object.keys( CLIENTPREFS_THEME_MAP ).find( ( key ) => CLIENTPREFS_THEME_MAP[ key ] === clientPrefs.get( 'skin-theme' ) );
			document.documentElement.classList.remove( ...LEGACY_THEME_CLASSES );
			document.documentElement.classList.add( `skin-wiki7-${ legacyThemeKey }` );
		};

		clientPreferences.render( `#${ clientPreferenceId }`, clientPreferenceConfig );
	}
}

/**
 * Set up the listen for preferences button
 *
 * @return {void}
 */
function listenForButtonClick() {
	const details = document.getElementById( 'wiki7-preferences-details' );
	if ( !details ) {
		return;
	}
	details.addEventListener( 'click', loadClientPreferences, { once: true } );
}

listenForButtonClick();
