<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

/**
 * Wiki7ComponentMenuListItem component
 */
class Wiki7ComponentMenuListItem implements Wiki7Component {

	public function __construct(
		private Wiki7ComponentLink $link,
		private string $class = '',
		private string $id = ''
	) {
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		return [
			'array-links' => $this->link->getTemplateData(),
			'item-class' => $this->class,
			'item-id' => $this->id,
		];
	}
}
