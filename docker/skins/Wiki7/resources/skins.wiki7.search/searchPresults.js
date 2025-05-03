const config = require( './config.json' );
const searchHistory = require( './searchHistory.js' )( config );

function searchPresults() {
	return {
		renderHistory: function ( results, templates ) {
			const items = [];
			results.forEach( ( result, index ) => {
				items.push( {
					id: index,
					href: `${ config.wgScriptPath }/index.php?title=Special:Search&search=${ result }`,
					text: result,
					icon: 'history'
				} );
			} );

			const data = {
				type: 'history',
				'array-list-items': items
			};

			const partials = {
				TypeaheadListItem: templates.TypeaheadListItem
			};

			document.getElementById( 'wiki7-typeahead-list-history' ).outerHTML = templates.TypeaheadList.render( data, partials ).html();
			document.getElementById( 'wiki7-typeahead-group-history' ).hidden = false;
		},
		render: function ( templates ) {
			const placeholderEl = document.getElementById( 'wiki7-typeahead-placeholder' );
			placeholderEl.innerHTML = '';
			placeholderEl.hidden = true;

			const historyResults = searchHistory.get();
			if ( historyResults && historyResults.length > 0 ) {
				this.renderHistory( historyResults, templates );
			} else {
				const data = {
					icon: 'articlesSearch',
					title: mw.message( 'searchsuggest-search' ).text(),
					description: mw.message( 'wiki7-search-empty-desc' ).text()
				};
				placeholderEl.innerHTML = templates.TypeaheadPlaceholder.render( data ).html();
				placeholderEl.hidden = false;
			}
		},
		clear: function () {
			document.getElementById( 'wiki7-typeahead-list-history' ).innerHTML = '';
			document.getElementById( 'wiki7-typeahead-group-history' ).hidden = true;
		}
	};
}

/** @module searchPresults */
module.exports = searchPresults;
