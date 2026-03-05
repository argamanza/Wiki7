<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

use MessageLocalizer;

/**
 * Wiki7ComponentPageFooter component
 */
class Wiki7ComponentPageFooter implements Wiki7Component {

	public function __construct(
		private readonly MessageLocalizer $localizer,
		private readonly array $footerData
	) {
	}

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
