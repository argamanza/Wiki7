<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

/**
 * Wiki7ComponentKeyboardHint component
 */
class Wiki7ComponentKeyboardHint implements Wiki7Component {

	public function __construct(
		private readonly string $label = '',
		private readonly string $key = ''
	) {
	}

	public function getTemplateData(): array {
		return [
			'label' => $this->label,
			'key' => $this->key,
		];
	}
}
