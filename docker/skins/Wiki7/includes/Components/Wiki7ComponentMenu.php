<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

use Countable;

/**
 * Wiki7ComponentMenu component
 */
class Wiki7ComponentMenu implements Wiki7Component, Countable {

	public function __construct( private array $data ) {
	}

	/**
	 * Counts how many items the menu has.
	 *
	 * @return int
	 */
	public function count(): int {
		$items = $this->data['array-list-items'] ?? null;
		if ( $items ) {
			return count( $items );
		}
		$htmlItems = $this->data['html-items'] ?? '';
		// FIXME: Counting '<li' occurrences in raw HTML is fragile — it could match
		// inside attributes, comments, or nested elements. This should ideally use
		// DOM parsing (e.g. DOMDocument) for accurate counting, but that would be
		// disproportionately heavy for this use case.
		return substr_count( $htmlItems, '<li' );
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		return $this->data + [
			'class' => '',
			'label' => '',
			'html-tooltip' => '',
			'label-class' => '',
			'html-before-portal' => '',
			'html-items' => '',
			'html-after-portal' => '',
			'array-list-items' => null,
		];
	}
}
