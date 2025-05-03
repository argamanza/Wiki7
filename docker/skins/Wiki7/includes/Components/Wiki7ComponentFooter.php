<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

use MessageLocalizer;

/**
 * Wiki7ComponentFooter component
 */
class Wiki7ComponentFooter implements Wiki7Component {

	public function __construct(
		private MessageLocalizer $localizer,
		private array $footerData
	) {
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		$localizer = $this->localizer;
		$footerData = $this->footerData;

		return $footerData + [
			'msg-wiki7-footer-desc' => $localizer->msg( "wiki7-footer-desc" )->inContentLanguage()->parse(),
			'msg-wiki7-footer-tagline' => $localizer->msg( "wiki7-footer-tagline" )->inContentLanguage()->parse()
		];
	}
}
