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

namespace MediaWiki\Skins\Wiki7;

use MediaWiki\MediaWikiServices;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentFooter;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentMainMenu;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentPageFooter;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentPageHeading;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentPageSidebar;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentPageTools;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentSearchBox;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentSiteStats;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentUserInfo;
use MediaWiki\Skins\Wiki7\Partials\BodyContent;
use MediaWiki\Skins\Wiki7\Partials\Metadata;
use MediaWiki\Skins\Wiki7\Partials\Theme;
use SkinMustache;
use SkinTemplate;

/**
 * Skin subclass for Wiki7
 * @ingroup Skins
 */
class SkinWiki7 extends SkinMustache {

	/** For caching purposes */
	private ?array $languages = null;

	/**
	 * Overrides template, styles and scripts module
	 *
	 * @inheritDoc
	 */
	public function __construct( $options = [] ) {
		if ( !isset( $options['name'] ) ) {
			$options['name'] = 'wiki7';
		}

		// Add skin-specific features
		$this->buildSkinFeatures( $options );
		parent::__construct( $options );
	}

	/**
	 * Ensure onSkinTemplateNavigation runs after all SkinTemplateNavigation hooks
	 * @see T287622
	 *
	 * @param SkinTemplate $skin The skin template object.
	 * @param array &$content_navigation The content navigation array.
	 */
	protected function runOnSkinTemplateNavigationHooks( SkinTemplate $skin, &$content_navigation ) {
		parent::runOnSkinTemplateNavigationHooks( $skin, $content_navigation );
		Hooks\SkinHooks::onSkinTemplateNavigation( $skin, $content_navigation );
	}

	/**
	 * Calls getLanguages with caching.
	 * From Vector 2022
	 */
	protected function getLanguagesCached(): array {
		if ( $this->languages === null ) {
			$this->languages = $this->getLanguages();
		}
		return $this->languages;
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		$parentData = parent::getTemplateData();

		$config = $this->getConfig();
		$localizer = $this->getContext();
		$out = $this->getOutput();
		$title = $this->getTitle();
		$user = $this->getUser();
		$pageLang = $title->getPageLanguage();
		$services = MediaWikiServices::getInstance();

		$isRegistered = $user->isRegistered();
		$isTemp = $user->isTemp();

		$bodycontent = new BodyContent( $this );

		$components = [
			'data-footer' => new Wiki7ComponentFooter(
				$localizer,
				$parentData['data-footer']
			),
			'data-main-menu' => new Wiki7ComponentMainMenu( $parentData['data-portlets-sidebar'] ),
			'data-page-footer' => new Wiki7ComponentPageFooter(
				$localizer,
				$parentData['data-footer']['data-info']
			),
			'data-page-heading' => new Wiki7ComponentPageHeading(
				$services,
				$localizer,
				$out,
				$pageLang,
				$title,
				$parentData['html-title-heading']
			),
			'data-page-sidebar' => new Wiki7ComponentPageSidebar(
				$localizer,
				$out,
				$pageLang,
				$title,
				$user
			),
			'data-page-tools' => new Wiki7ComponentPageTools(
				$config,
				$localizer,
				$title,
				$user,
				$services->getPermissionManager(),
				count( $this->getLanguagesCached() ),
				$parentData['data-portlets-sidebar'],
				// These portlets can be unindexed
				$parentData['data-portlets']['data-languages'] ?? [],
				$parentData['data-portlets']['data-variants'] ?? []
			),
			'data-search-box' => new Wiki7ComponentSearchBox(
				$localizer,
				$services->getExtensionRegistry(),
				$parentData['data-search-box']
			),
			'data-site-stats' => new Wiki7ComponentSiteStats(
				$config,
				$localizer,
				$pageLang
			),
			'data-user-info' => new Wiki7ComponentUserInfo(
				$isRegistered,
				$isTemp,
				$services,
				$localizer,
				$title,
				$user,
				$parentData['data-portlets']['data-user-page']
			)
		];

		foreach ( $components as $key => $component ) {
			// Array of components or null values.
			if ( $component ) {
				$parentData[$key] = $component->getTemplateData();
			}
		}

		// HACK: So that we can use Icon.mustache in Header__logo.mustache
		$parentData['data-logos']['icon-home'] = 'home';

		return array_merge( $parentData, [
			// Booleans
			'toc-enabled' => !empty( $parentData['data-toc'] ),
			'html-body-content--formatted' => $bodycontent->decorateBodyContent( $parentData['html-body-content'] )
		] );
	}

	/**
	 * @inheritDoc
	 *
	 * Manually disable some site-wide tools in TOOLBOX
	 * They are re-added in the drawer
	 *
	 * TODO: Remove this hack when Desktop Improvements separate page and site tools
	 */
	protected function buildNavUrls(): array {
		$urls = parent::buildNavUrls();

		$urls['upload'] = false;
		$urls['specialpages'] = false;

		return $urls;
	}

	/**
	 * Add client preferences features
	 * Did not add the wiki7-feature- prefix because there might be features from core MW or extensions
	 *
	 * @param string $feature
	 * @param string $value
	 */
	private function addClientPrefFeature( string $feature, string $value = 'standard' ): void {
		$this->getOutput()->addHtmlClasses( $feature . '-clientpref-' . $value );
	}

	/**
	 * Set up optional skin features
	 */
	private function buildSkinFeatures( array &$options ): void {
		$config = $this->getConfig();
		$title = $this->getOutput()->getTitle();

		$metadata = new Metadata( $this );
		$skinTheme = new Theme( $this );

		// Add metadata
		$metadata->addMetadata();

		// Add theme handler
		$skinTheme->setSkinTheme( $options );

		// Clientprefs feature handling
		$this->addClientPrefFeature( 'wiki7-feature-autohide-navigation', '1' );
		$this->addClientPrefFeature( 'wiki7-feature-pure-black', '0' );
		$this->addClientPrefFeature( 'wiki7-feature-custom-font-size' );
		$this->addClientPrefFeature( 'wiki7-feature-custom-width' );

		if ( $title !== null ) {
			// Collapsible sections
			if (
				$config->get( 'Wiki7EnableCollapsibleSections' ) === true &&
				$title->isContentPage()
			) {
				$options['bodyClasses'][] = 'wiki7-sections-enabled';
			}

            // HE fonts
            // Load Hebrew fonts only for pages where the content language is Hebrew
            // This ensures Roboto (which also supports Hebrew) doesn't override preferred fonts
            if ( $title->getPageLanguage()->getCode() === 'he' && $config->get( 'Wiki7EnableHEFonts' ) === true ) {
                $options['styles'][] = 'skins.wiki7.styles.fonts.he';
            }
		}

		// CJK fonts
		if ( $config->get( 'Wiki7EnableCJKFonts' ) === true ) {
			$options['styles'][] = 'skins.wiki7.styles.fonts.cjk';
		}

		// AR fonts
		if ( $config->get( 'Wiki7EnableARFonts' ) === true ) {
			$options['styles'][] = 'skins.wiki7.styles.fonts.ar';
		}
	}
}
