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

namespace MediaWiki\Skins\Wiki7\Hooks;

use MediaWiki\Config\Config;
use MediaWiki\MainConfigNames;
use MediaWiki\Registration\ExtensionRegistry;
use MediaWiki\ResourceLoader as RL;

/**
 * Hooks to run relating to the resource loader
 */
class ResourceLoaderHooks {

	/**
	 * Passes config variables to skins.wiki7.scripts ResourceLoader module.
	 * @param RL\Context $context
	 * @param Config $config
	 * @return array
	 */
	public static function getWiki7ResourceLoaderConfig(
		RL\Context $context,
		Config $config
	) {
		return [
			'wgWiki7EnablePreferences' => $config->get( 'Wiki7EnablePreferences' ),
			'wgWiki7OverflowInheritedClasses' => $config->get( 'Wiki7OverflowInheritedClasses' ),
			'wgWiki7OverflowNowrapClasses' => $config->get( 'Wiki7OverflowNowrapClasses' ),
			'wgWiki7SearchModule' => $config->get( 'Wiki7SearchModule' ),
			'wgWiki7EnableCommandPalette' => $config->get( 'Wiki7EnableCommandPalette' ),
		];
	}

	/**
	 * Passes config variables to skins.wiki7.preferences ResourceLoader module.
	 * @param RL\Context $context
	 * @param Config $config
	 * @return array
	 */
	public static function getWiki7PreferencesResourceLoaderConfig(
		RL\Context $context,
		Config $config
	) {
		return [
			'wgWiki7ThemeDefault' => $config->get( 'Wiki7ThemeDefault' ),
		];
	}

	/**
	 * Passes config variables to skins.wiki7.search ResourceLoader module.
	 * @param RL\Context $context
	 * @param Config $config
	 * @return array
	 */
	public static function getWiki7SearchResourceLoaderConfig(
		RL\Context $context,
		Config $config
	) {
		return [
			'isAdvancedSearchExtensionEnabled' => ExtensionRegistry::getInstance()->isLoaded( 'AdvancedSearch' ),
			'isMediaSearchExtensionEnabled' => ExtensionRegistry::getInstance()->isLoaded( 'MediaSearch' ),
			'wgWiki7SearchGateway' => $config->get( 'Wiki7SearchGateway' ),
			'wgWiki7SearchDescriptionSource' => $config->get( 'Wiki7SearchDescriptionSource' ),
			'wgWiki7MaxSearchResults' => $config->get( 'Wiki7MaxSearchResults' ),
			'wgScriptPath' => $config->get( MainConfigNames::ScriptPath ),
			'wgSearchSuggestCacheExpiry' => $config->get( MainConfigNames::SearchSuggestCacheExpiry )
		];
	}

	/**
	 * Passes config variables to skins.wiki7.commandPalette ResourceLoader module.
	 * @param RL\Context $context
	 * @param Config $config
	 * @return array
	 */
	public static function getWiki7CommandPaletteResourceLoaderConfig(
		RL\Context $context,
		Config $config
	) {
		return [
			'wgSearchSuggestCacheExpiry' => $config->get( MainConfigNames::SearchSuggestCacheExpiry )
		];
	}
}
