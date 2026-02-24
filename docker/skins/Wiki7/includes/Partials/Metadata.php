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

use Exception;
use MediaWiki\MainConfigNames;
use MediaWiki\MediaWikiServices;

final class Metadata extends Partial {

	/**
	 * Adds metadata to the output page
	 */
	public function addMetadata(): void {
		// Theme color
		$this->out->addMeta( 'theme-color', $this->getConfigValue( 'Wiki7ThemeColor' ) ?? '' );

		// Generate webapp manifest
		$this->addManifest();

		// Add color-scheme meta tag for improved dark mode support (v3.5.0+)
		$themeDefault = $this->getConfigValue( 'Wiki7ThemeDefault' ) ?? 'auto';
		if ( $themeDefault === 'auto' ) {
			$this->out->addMeta( 'color-scheme', 'light dark' );
		} elseif ( $themeDefault === 'dark' ) {
			$this->out->addMeta( 'color-scheme', 'dark light' );
		} else {
			$this->out->addMeta( 'color-scheme', 'light' );
		}

		// Add preload hints for critical resources (v3.13.0+)
		$this->addPreloadHints();
	}

	/**
	 * Adds <link rel="preload"> hints for critical fonts and styles
	 * to improve initial page load performance.
	 * Introduced in Wiki7 v3.13.0
	 */
	private function addPreloadHints(): void {
		$skinPath = $this->out->getSkin()->getSkinName() === 'wiki7'
			? $this->out->getConfig()->get( 'StylePath' ) . '/Wiki7'
			: '';

		if ( !$skinPath ) {
			return;
		}

		// Preload the primary Latin font subset (most commonly needed)
		$this->out->addLink( [
			'rel' => 'preload',
			'href' => $skinPath . '/resources/skins.wiki7.styles/fonts/RobotoFlex_latin.woff2',
			'as' => 'font',
			'type' => 'font/woff2',
			'crossorigin' => 'anonymous',
		] );

		// Preload the main skin stylesheet for faster rendering
		$this->out->addLink( [
			'rel' => 'preload',
			'href' => $skinPath . '/resources/skins.wiki7.styles/skin.less',
			'as' => 'style',
		] );
	}

	/**
	 * Adds the manifest if:
	 * * Enabled in 'Wiki7EnableManifest'
	 * * User has read access (i.e. not a private wiki)
	 * Manifest link will be empty if wfExpandUrl throws an exception.
	 */
	private function addManifest(): void {
		if (
			$this->getConfigValue( 'Wiki7EnableManifest' ) !== true ||
			$this->getConfigValue( MainConfigNames::GroupPermissions )['*']['read'] !== true
		) {
			return;
		}

		try {
			$href = MediaWikiServices::getInstance()->getUrlUtils()
				->expand( wfAppendQuery( wfScript( 'api' ),
					[ 'action' => 'webapp-manifest' ] ), PROTO_RELATIVE );
		} catch ( Exception $e ) {
			$href = '';
		}

		$this->out->addLink( [
			'rel' => 'manifest',
			'href' => $href,
		] );
	}
}
