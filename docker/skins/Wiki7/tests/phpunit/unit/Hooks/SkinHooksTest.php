<?php
/**
 * Wiki7 - A responsive skin developed for the Star Wiki7 Wiki
 *
 * This file is part of Wiki7.
 *
 * Wiki7 is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Wiki7 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Wiki7.  If not, see <https://www.gnu.org/licenses/>.
 *
 * @file
 */

namespace MediaWiki\Skins\Wiki7\Tests\Unit\Hooks;

use MediaWiki\Skins\Wiki7\Hooks\SkinHooks;
use MediaWikiUnitTestCase;
use ReflectionMethod;

/**
 * @group Wiki7
 * @group Hooks
 * @coversDefaultClass \MediaWiki\Skins\Wiki7\Hooks\SkinHooks
 */
class SkinHooksTest extends MediaWikiUnitTestCase {

	/**
	 * Helper to invoke private static methods on SkinHooks via reflection.
	 *
	 * @param string $methodName
	 * @param array $args
	 * @return mixed
	 */
	private function invokePrivateStaticMethod( string $methodName, array $args ) {
		$method = new ReflectionMethod( SkinHooks::class, $methodName );
		$method->setAccessible( true );
		return $method->invokeArgs( null, $args );
	}

	/**
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_validIcon_generatesLinkHtml(): void {
		$links = [
			'views' => [
				'edit' => [
					'icon' => 'edit',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayHasKey( 'link-html', $links['views']['edit'] );
		$this->assertStringContainsString( 'wiki7-ui-icon', $links['views']['edit']['link-html'] );
		$this->assertStringContainsString( 'mw-ui-icon-edit', $links['views']['edit']['link-html'] );
		$this->assertStringContainsString( 'mw-ui-icon-wikimedia-edit', $links['views']['edit']['link-html'] );
	}

	/**
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_validIconWithHyphen_generatesLinkHtml(): void {
		$links = [
			'views' => [
				'special-item' => [
					'icon' => 'arrow-left',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayHasKey( 'link-html', $links['views']['special-item'] );
		$this->assertStringContainsString( 'mw-ui-icon-arrow-left', $links['views']['special-item']['link-html'] );
	}

	/**
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_validIconWithUnderscore_generatesLinkHtml(): void {
		$links = [
			'actions' => [
				'my_action' => [
					'icon' => 'my_icon',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'actions' ] );

		$this->assertArrayHasKey( 'link-html', $links['actions']['my_action'] );
		$this->assertStringContainsString( 'mw-ui-icon-my_icon', $links['actions']['my_action']['link-html'] );
	}

	/**
	 * Test that an icon name containing HTML/CSS injection characters is rejected.
	 *
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_maliciousIconWithHtml_isRejected(): void {
		$links = [
			'views' => [
				'evil' => [
					'icon' => 'edit"><script>alert(1)</script>',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayNotHasKey( 'link-html', $links['views']['evil'],
			'Malicious icon name with HTML tags should be rejected' );
	}

	/**
	 * Test that an icon name containing spaces is rejected.
	 *
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_iconWithSpaces_isRejected(): void {
		$links = [
			'views' => [
				'bad' => [
					'icon' => 'edit icon',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayNotHasKey( 'link-html', $links['views']['bad'],
			'Icon name with spaces should be rejected' );
	}

	/**
	 * Test that an icon name containing CSS class injection characters is rejected.
	 *
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_iconWithCssInjection_isRejected(): void {
		$links = [
			'views' => [
				'inject' => [
					'icon' => 'edit" onclick="alert(1)',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayNotHasKey( 'link-html', $links['views']['inject'],
			'Icon name with double quotes should be rejected' );
	}

	/**
	 * Test that an empty icon string does not generate link-html.
	 *
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_emptyIcon_noLinkHtml(): void {
		$links = [
			'views' => [
				'noicon' => [
					'icon' => '',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayNotHasKey( 'link-html', $links['views']['noicon'],
			'Empty icon name should not generate link-html' );
	}

	/**
	 * Test that a missing icon key does not generate link-html.
	 *
	 * @covers ::addIconsToMenuItems
	 */
	public function testAddIconsToMenuItems_missingIcon_noLinkHtml(): void {
		$links = [
			'views' => [
				'nokey' => [
					'text' => 'Some link',
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'views' ] );

		$this->assertArrayNotHasKey( 'link-html', $links['views']['nokey'],
			'Missing icon key should not generate link-html' );
	}

	/**
	 * @covers ::mapIconsToMenuItems
	 */
	public function testMapIconsToMenuItems_mapsCorrectIcons(): void {
		$links = [
			'views' => [
				'edit' => [],
				'history' => [],
				'nonexistent' => [],
			],
		];

		$iconMap = [
			'edit' => 'edit',
			'history' => 'history',
		];

		$this->invokePrivateStaticMethod( 'mapIconsToMenuItems', [ &$links, 'views', $iconMap ] );

		$this->assertEquals( 'edit', $links['views']['edit']['icon'] );
		$this->assertEquals( 'history', $links['views']['history']['icon'] );
		$this->assertArrayNotHasKey( 'icon', $links['views']['nonexistent'],
			'Items not in the icon map should not have icons set' );
	}

	/**
	 * @covers ::mapIconsToMenuItems
	 */
	public function testMapIconsToMenuItems_doesNotOverrideExistingIcon(): void {
		$links = [
			'views' => [
				'edit' => [
					'icon' => 'customEdit',
				],
			],
		];

		$iconMap = [
			'edit' => 'edit',
		];

		$this->invokePrivateStaticMethod( 'mapIconsToMenuItems', [ &$links, 'views', $iconMap ] );

		$this->assertEquals( 'customEdit', $links['views']['edit']['icon'],
			'mapIconsToMenuItems should not override an existing icon value' );
	}

	/**
	 * @covers ::appendClassToItem
	 */
	public function testAppendClassToItem_stringToString(): void {
		$item = 'existing-class';
		$this->invokePrivateStaticMethod( 'appendClassToItem', [ &$item, 'new-class' ] );
		$this->assertEquals( 'existing-class new-class', $item );
	}

	/**
	 * @covers ::appendClassToItem
	 */
	public function testAppendClassToItem_arrayToArray(): void {
		$item = [ 'existing-class' ];
		$this->invokePrivateStaticMethod( 'appendClassToItem', [ &$item, [ 'new-class', 'another-class' ] ] );
		$this->assertEquals( [ 'existing-class', 'new-class', 'another-class' ], $item );
	}

	/**
	 * @covers ::appendClassToItem
	 */
	public function testAppendClassToItem_stringToArray(): void {
		$item = [ 'existing-class' ];
		$this->invokePrivateStaticMethod( 'appendClassToItem', [ &$item, 'new-class' ] );
		$this->assertEquals( [ 'existing-class', 'new-class' ], $item );
	}

	/**
	 * @covers ::appendClassToItem
	 */
	public function testAppendClassToItem_nullItem_setsClasses(): void {
		$item = null;
		$this->invokePrivateStaticMethod( 'appendClassToItem', [ &$item, 'new-class' ] );
		$this->assertEquals( 'new-class', $item );
	}

	/**
	 * Data provider for icon name validation.
	 * Tests the regex pattern /^[a-zA-Z0-9\-_]+$/ used in addIconsToMenuItems.
	 *
	 * @return array[]
	 */
	public static function provideIconNames(): array {
		return [
			'simple lowercase' => [ 'edit', true ],
			'simple uppercase' => [ 'Edit', true ],
			'with hyphen' => [ 'arrow-left', true ],
			'with underscore' => [ 'my_icon', true ],
			'with numbers' => [ 'icon123', true ],
			'mixed' => [ 'myIcon-2_test', true ],
			'with space' => [ 'edit icon', false ],
			'with dot' => [ 'edit.icon', false ],
			'with double quote' => [ 'edit"inject', false ],
			'with angle bracket' => [ 'edit<script>', false ],
			'with single quote' => [ "edit'inject", false ],
			'with slash' => [ 'path/icon', false ],
			'with backslash' => [ 'path\\icon', false ],
			'empty string' => [ '', false ],
		];
	}

	/**
	 * @covers ::addIconsToMenuItems
	 * @dataProvider provideIconNames
	 */
	public function testAddIconsToMenuItems_iconNameValidation( string $iconName, bool $shouldBeAccepted ): void {
		if ( $iconName === '' ) {
			// Empty string is a special case - it evaluates to falsy so no link-html is set
			$this->assertEmpty( $iconName );
			return;
		}

		$links = [
			'test-menu' => [
				'test-item' => [
					'icon' => $iconName,
				],
			],
		];

		$this->invokePrivateStaticMethod( 'addIconsToMenuItems', [ &$links, 'test-menu' ] );

		if ( $shouldBeAccepted ) {
			$this->assertArrayHasKey( 'link-html', $links['test-menu']['test-item'],
				"Icon name '$iconName' should be accepted" );
		} else {
			$this->assertArrayNotHasKey( 'link-html', $links['test-menu']['test-item'],
				"Icon name '$iconName' should be rejected" );
		}
	}
}
