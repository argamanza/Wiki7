<?php

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Components;

use MediaWiki\Language\Language;
use MediaWiki\Output\OutputPage;
use MediaWiki\StubObject\StubUserLang;
use MediaWiki\Title\Title;
use MediaWiki\User\UserIdentity;
use MessageLocalizer;

/**
 * Wiki7ComponentPageSidebar component
 * FIXME: Need unit test
 */
class Wiki7ComponentPageSidebar implements Wiki7Component {

	public function __construct(
		private MessageLocalizer $localizer,
		private OutputPage $out,
		private Language|StubUserLang $pageLang,
		private Title $title,
		private UserIdentity $user
	) {
	}

	/**
	 * Get the last modified data
	 * TODO: Use core instead when update to MW 1.43
	 */
	private function getLastModData(): array {
		$timestamp = $this->out->getRevisionTimestamp();

		if ( !$timestamp ) {
			return [];
		}

		$localizer = $this->localizer;
		$pageLang = $this->pageLang;
		$title = $this->title;
		$user = $this->user;

		$d = $pageLang->userDate( $timestamp, $user );
		$t = $pageLang->userTime( $timestamp, $user );
		$s = $localizer->msg( 'lastmodifiedat', $d, $t );

		// FIXME: Use Wiki7ComponentMenuListItem
		$items = [
			'item-id' => 'lm-time',
			'item-class' => 'mw-list-item',
			'array-links' => [
				'array-attributes' => [
					[
						'key' => 'id',
						'value' => 'wiki7-lastmod-relative'
					],
					[
						'key' => 'href',
						'value' => $title->getLocalURL( [ 'diff' => '' ] )
					],
					[
						'key' => 'title',
						'value' => $s
					],
					[
						'key' => 'data-timestamp',
						'value' => wfTimestamp( TS_UNIX, $timestamp )
					]
				],
				'icon' => 'history',
				'text' => $d
			]
		];

		$menu = new Wiki7ComponentMenu(
			[
				'id' => 'wiki7-sidebar-lastmod',
				'label' => $localizer->msg( 'wiki7-page-info-lastmod' ),
				'array-list-items' => $items
			]
		);

		return $menu->getTemplateData();
	}

	/**
	 * @inheritDoc
	 */
	public function getTemplateData(): array {
		return [
			'data-page-sidebar-lastmod' => $this->getLastModData()
		];
	}
}
