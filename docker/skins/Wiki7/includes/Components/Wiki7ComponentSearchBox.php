<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

use MediaWiki\Registration\ExtensionRegistry;
use MediaWiki\Skin\SkinComponentUtils;
use MessageLocalizer;

/**
 * Wiki7ComponentSearchBox component
 */
class Wiki7ComponentSearchBox implements Wiki7Component {

	public function __construct(
		private MessageLocalizer $localizer,
		private ExtensionRegistry $extensionRegistry,
		private array $searchBoxData
	) {
	}

	/**
	 * Get the keyboard hint data
	 */
	private function getKeyboardHintData(): array {
		$data = [];
		// There is probably a cleaner way to handle this
		$map = [
			'↑ ↓' => $this->localizer->msg( "wiki7-search-keyhint-select" )->text(),
			'/' => $this->localizer->msg( "wiki7-search-keyhint-open" )->text(),
			'Esc' => $this->localizer->msg( "wiki7-search-keyhint-exit" )->text()
		];

		foreach ( $map as $key => $label ) {
			$keyhint = new Wiki7ComponentKeyboardHint( $label, $key );
			$data[] = $keyhint->getTemplateData();
		}
		return $data;
	}

	/**
	 * Get the footer message
	 */
	private function getFooterMessage(): string {
		$isCirrusSearchExtensionEnabled = $this->extensionRegistry->isLoaded( 'CirrusSearch' );
		$searchBackend = $isCirrusSearchExtensionEnabled ? 'cirrussearch' : 'mediawiki';
		return $this->localizer->msg(
			'wiki7-search-poweredby',
			$this->localizer->msg( "wiki7-search-poweredby-$searchBackend" )
		)->text();
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		$searchBoxData = $this->searchBoxData + [
			'array-keyboard-hint' => $this->getKeyboardHintData(),
			'msg-wiki7-search-footer' => $this->getFooterMessage(),
			'msg-wiki7-search-toggle-shortcut' => '[/]',
			'html-random-href' => SkinComponentUtils::makeSpecialUrl( 'Randompage' )
		];
		return $searchBoxData;
	}
}
