/**
 * Set up functionality of collapsable sections
 *
 * @param {HTMLElement} bodyContent
 * @return {void}
 */
function init( bodyContent ) {
	if ( !document.body.classList.contains( 'wiki7-sections-enabled' ) ) {
		return;
	}

	const onEditSectionClick = ( e ) => {
		e.stopPropagation();
	};

	const handleClick = ( e ) => {
		const target = e.target;
		const isEditSection = target.closest( '.mw-editsection, .mw-editsection-like' );

		if ( isEditSection ) {
			onEditSectionClick( e );
			return;
		}

		const heading = target.closest( '.wiki7-section-heading' );

		if ( heading && heading.nextElementSibling && heading.nextElementSibling.classList.contains( 'wiki7-section' ) ) {
			const section = heading.nextElementSibling;

			if ( section ) {
				section.hidden = section.hidden ? false : 'until-found';
			}
		}
	};

	bodyContent.addEventListener( 'click', handleClick, false );
}

module.exports = {
	init: init
};
