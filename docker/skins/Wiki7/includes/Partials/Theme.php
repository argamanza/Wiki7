<?php
/**
 * Wiki7 - A responsive skin developed for the Star Wiki7 Wiki
 *
 * This file is part of Wiki7.
 *
 * Wiki7 is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Wiki7 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Wiki7.  If not, see <https://www.gnu.org/licenses/>.
 *
 * @file
 * @ingroup Skins
 */

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Partials;

const CLIENTPREFS_THEME_MAP = [
	'auto' => 'os',
	'light' => 'day',
	'dark' => 'night'
];

/**
 * Theme switcher partial of Skin Wiki7
 */
final class Theme extends Partial {

	/**
	 * Sets the corresponding theme class on the <html> element
	 * If the theme is set to auto, the theme switcher script will be added
	 *
	 * @param array &$options
	 */
	public function setSkinTheme( array &$options ) {
		$out = $this->out;

		// Set theme to site theme
		$theme = $this->getConfigValue( 'Wiki7ThemeDefault' ) ?? 'auto';

		// Legacy class to be deprecated
		$out->addHtmlClasses( 'skin-wiki7-' . $theme );

		// Add HTML class based on theme set
		if ( CLIENTPREFS_THEME_MAP[ $theme ] ) {
			$out->addHtmlClasses( 'skin-theme-clientpref-' . CLIENTPREFS_THEME_MAP[ $theme ] );
		}
	}
}
