<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Hooks;

use MediaWiki\Config\Config;
use MediaWiki\MainConfigNames;
use MediaWiki\MediaWikiServices;
use MediaWiki\Registration\ExtensionRegistry;
use MediaWiki\ResourceLoader as RL;
use MediaWiki\Skins\Wiki7\PreferencesConfigProvider;

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
		$extensionRegistry = ExtensionRegistry::getInstance();

		return [
			'isAdvancedSearchExtensionEnabled' => $extensionRegistry->isLoaded( 'AdvancedSearch' ),
			'isMediaSearchExtensionEnabled' => $extensionRegistry->isLoaded( 'MediaSearch' ),
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
		$extensionRegistry = ExtensionRegistry::getInstance();

		return [
			'isMediaSearchExtensionEnabled' => $extensionRegistry->isLoaded( 'MediaSearch' ),
			'wgSearchSuggestCacheExpiry' => $config->get( MainConfigNames::SearchSuggestCacheExpiry )
		];
	}

	/**
	 * Return on-wiki preferences overrides with pre-resolved message texts.
	 *
	 * @param RL\Context $context
	 * @param Config $config
	 * @return array{overrides: ?array, messages: \stdClass|array<string, string>}
	 */
	public static function getWiki7PreferencesOverrides(
		RL\Context $context,
		Config $config
	): array {
		$services = MediaWikiServices::getInstance();
		$provider = new PreferencesConfigProvider(
			$services->getRevisionLookup(),
			$services->getTitleFactory(),
			$context
		);
		return $provider->getOverrides( $context->getLanguage() );
	}
}
