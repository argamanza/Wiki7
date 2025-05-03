<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

/**
 * Component interface for managing Wiki7-modified components
 *
 * @internal
 */
interface Wiki7Component {

	public function getTemplateData(): array;
}
