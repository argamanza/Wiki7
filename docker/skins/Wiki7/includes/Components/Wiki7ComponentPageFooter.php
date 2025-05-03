<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

use MessageLocalizer;

/**
 * Wiki7ComponentPageFooter component
 * FIXME: Need unit test
 */
class Wiki7ComponentPageFooter implements Wiki7Component {

	public function __construct(
		private MessageLocalizer $localizer,
		private array $footerData
	) {
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		$footerData = $this->footerData;

		// Add label to footer-info to use in PageFooter
		foreach ( $footerData['array-items'] as &$item ) {
			$msgKey = 'wiki7-page-info-' . $item['name'];
			$item['label'] = $this->localizer->msg( $msgKey )->text();
		}

		return $footerData;
	}
}
