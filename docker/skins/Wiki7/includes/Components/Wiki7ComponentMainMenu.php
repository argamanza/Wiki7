<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

/**
 * Wiki7ComponentMainMenu component
 */
class Wiki7ComponentMainMenu implements Wiki7Component {

	public function __construct( private array $sidebarData ) {
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		$portletsRest = [];
		foreach ( $this->sidebarData[ 'array-portlets-rest' ] as $data ) {
			/**
			 * Remove toolbox from main menu as we moved it to article tools
			 * TODO: Move handling to SkinWiki7.php after we convert pagetools to component
			 */
			if ( $data['id'] === 'p-tb' ) {
				continue;
			}
			$portletsRest[] = ( new Wiki7ComponentMenu( $data ) )->getTemplateData();
		}
		$firstPortlet = new Wiki7ComponentMenu( $this->sidebarData['data-portlets-first'] );

		return [
			'data-portlets-first' => $firstPortlet->getTemplateData(),
			'array-portlets-rest' => $portletsRest
		];
	}
}
