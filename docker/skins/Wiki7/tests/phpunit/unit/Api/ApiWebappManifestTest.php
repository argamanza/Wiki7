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

namespace MediaWiki\Skins\Wiki7\Tests\Unit\Api;

use MediaWiki\Skins\Wiki7\Api\ApiWebappManifest;
use MediaWikiUnitTestCase;
use ReflectionMethod;

/**
 * @group Wiki7
 * @group Api
 * @coversDefaultClass \MediaWiki\Skins\Wiki7\Api\ApiWebappManifest
 */
class ApiWebappManifestTest extends MediaWikiUnitTestCase {

	/**
	 * Invoke the private isValidIconUrl method via reflection.
	 *
	 * We cannot easily construct ApiWebappManifest (it requires ApiMain etc.),
	 * so we create a partial mock that bypasses the constructor and use
	 * reflection to call the private method.
	 *
	 * @param string $url
	 * @return bool
	 */
	private function callIsValidIconUrl( string $url ): bool {
		// Create a mock that skips the constructor
		$mock = $this->getMockBuilder( ApiWebappManifest::class )
			->disableOriginalConstructor()
			->getMock();

		$method = new ReflectionMethod( ApiWebappManifest::class, 'isValidIconUrl' );
		$method->setAccessible( true );
		return $method->invoke( $mock, $url );
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_httpsUrl_isAccepted(): void {
		$this->assertTrue(
			$this->callIsValidIconUrl( 'https://example.com/icon.png' ),
			'HTTPS URLs should be accepted'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_httpUrl_isAccepted(): void {
		$this->assertTrue(
			$this->callIsValidIconUrl( 'http://example.com/icon.png' ),
			'HTTP URLs should be accepted'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_relativeUrl_isAccepted(): void {
		$this->assertTrue(
			$this->callIsValidIconUrl( '/path/to/icon.png' ),
			'Relative URLs starting with / should be accepted'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_protocolRelativeUrl_isAccepted(): void {
		$this->assertTrue(
			$this->callIsValidIconUrl( '//example.com/icon.png' ),
			'Protocol-relative URLs should be accepted'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_javascriptUrl_isRejected(): void {
		$this->assertFalse(
			$this->callIsValidIconUrl( 'javascript:alert(1)' ),
			'javascript: URLs must be rejected'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_dataUrl_isRejected(): void {
		$this->assertFalse(
			$this->callIsValidIconUrl( 'data:text/html,<script>alert(1)</script>' ),
			'data: URLs must be rejected'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_dataImageUrl_isRejected(): void {
		$this->assertFalse(
			$this->callIsValidIconUrl( 'data:image/png;base64,iVBORw0KGgo=' ),
			'data: image URLs must be rejected'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_ftpUrl_isRejected(): void {
		$this->assertFalse(
			$this->callIsValidIconUrl( 'ftp://example.com/icon.png' ),
			'FTP URLs must be rejected'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_emptyString_isRejected(): void {
		$this->assertFalse(
			$this->callIsValidIconUrl( '' ),
			'Empty string should be rejected'
		);
	}

	/**
	 * @covers ::isValidIconUrl
	 */
	public function testIsValidIconUrl_justText_isRejected(): void {
		$this->assertFalse(
			$this->callIsValidIconUrl( 'not-a-url' ),
			'Plain text without a scheme should be rejected'
		);
	}

	/**
	 * Data provider for comprehensive URL validation testing.
	 *
	 * @return array[]
	 */
	public static function provideIconUrls(): array {
		return [
			'https URL' => [ 'https://wiki.example.com/logo.png', true ],
			'http URL' => [ 'http://wiki.example.com/logo.png', true ],
			'HTTPS uppercase' => [ 'HTTPS://wiki.example.com/logo.png', true ],
			'relative path' => [ '/w/images/logo.png', true ],
			'protocol-relative' => [ '//upload.wikimedia.org/logo.png', true ],
			'deep relative path' => [ '/w/skins/Wiki7/resources/icon.svg', true ],
			'javascript scheme' => [ 'javascript:alert(document.cookie)', false ],
			'JavaScript mixed case' => [ 'JavaScript:alert(1)', false ],
			'data text/html' => [ 'data:text/html,<script>alert(1)</script>', false ],
			'data image/svg' => [ 'data:image/svg+xml,<svg onload=alert(1)>', false ],
			'data base64 image' => [ 'data:image/png;base64,abc123', false ],
			'ftp scheme' => [ 'ftp://files.example.com/icon.png', false ],
			'file scheme' => [ 'file:///etc/passwd', false ],
			'empty string' => [ '', false ],
			'bare domain' => [ 'example.com/icon.png', false ],
		];
	}

	/**
	 * @covers ::isValidIconUrl
	 * @dataProvider provideIconUrls
	 */
	public function testIsValidIconUrl_comprehensiveValidation( string $url, bool $expected ): void {
		$this->assertSame(
			$expected,
			$this->callIsValidIconUrl( $url ),
			"URL '$url' validation result did not match expected"
		);
	}

	/**
	 * Test that getIcons filters out icons with invalid src URLs.
	 *
	 * @covers ::getIcons
	 */
	public function testGetIcons_filtersInvalidSrcUrls(): void {
		$mock = $this->getMockBuilder( ApiWebappManifest::class )
			->disableOriginalConstructor()
			->getMock();

		// Set up the private 'options' property via reflection
		$optionsProperty = new \ReflectionProperty( ApiWebappManifest::class, 'options' );
		$optionsProperty->setAccessible( true );
		$optionsProperty->setValue( $mock, [
			'icons' => [
				[ 'src' => 'https://example.com/valid.png', 'sizes' => '192x192' ],
				[ 'src' => 'javascript:alert(1)', 'sizes' => '192x192' ],
				[ 'src' => '/relative/path/icon.png', 'sizes' => '512x512' ],
				[ 'src' => 'data:image/png;base64,abc', 'sizes' => '64x64' ],
			],
		] );

		$method = new ReflectionMethod( ApiWebappManifest::class, 'getIcons' );
		$method->setAccessible( true );
		$result = $method->invoke( $mock );

		$this->assertCount( 2, $result,
			'Only valid URLs should be included in the icons result' );

		$srcs = array_column( $result, 'src' );
		$this->assertContains( 'https://example.com/valid.png', $srcs );
		$this->assertContains( '/relative/path/icon.png', $srcs );
		$this->assertNotContains( 'javascript:alert(1)', $srcs );
		$this->assertNotContains( 'data:image/png;base64,abc', $srcs );
	}

	/**
	 * Test that getIcons only keeps allowed keys.
	 *
	 * @covers ::getIcons
	 */
	public function testGetIcons_filtersUnknownKeys(): void {
		$mock = $this->getMockBuilder( ApiWebappManifest::class )
			->disableOriginalConstructor()
			->getMock();

		$optionsProperty = new \ReflectionProperty( ApiWebappManifest::class, 'options' );
		$optionsProperty->setAccessible( true );
		$optionsProperty->setValue( $mock, [
			'icons' => [
				[
					'src' => 'https://example.com/icon.png',
					'sizes' => '192x192',
					'type' => 'image/png',
					'purpose' => 'any',
					'malicious_key' => '<script>alert(1)</script>',
					'extra' => 'should-be-removed',
				],
			],
		] );

		$method = new ReflectionMethod( ApiWebappManifest::class, 'getIcons' );
		$method->setAccessible( true );
		$result = $method->invoke( $mock );

		$this->assertCount( 1, $result );
		$icon = $result[0];
		$this->assertArrayHasKey( 'src', $icon );
		$this->assertArrayHasKey( 'sizes', $icon );
		$this->assertArrayHasKey( 'type', $icon );
		$this->assertArrayHasKey( 'purpose', $icon );
		$this->assertArrayNotHasKey( 'malicious_key', $icon,
			'Unknown keys should be filtered out' );
		$this->assertArrayNotHasKey( 'extra', $icon,
			'Unknown keys should be filtered out' );
	}

	/**
	 * Test that getIcons skips non-array icon entries.
	 *
	 * @covers ::getIcons
	 */
	public function testGetIcons_skipsNonArrayEntries(): void {
		$mock = $this->getMockBuilder( ApiWebappManifest::class )
			->disableOriginalConstructor()
			->getMock();

		$optionsProperty = new \ReflectionProperty( ApiWebappManifest::class, 'options' );
		$optionsProperty->setAccessible( true );
		$optionsProperty->setValue( $mock, [
			'icons' => [
				'not-an-array',
				42,
				null,
				[ 'src' => 'https://example.com/valid.png' ],
			],
		] );

		$method = new ReflectionMethod( ApiWebappManifest::class, 'getIcons' );
		$method->setAccessible( true );
		$result = $method->invoke( $mock );

		$this->assertCount( 1, $result,
			'Non-array icon entries should be skipped' );
	}
}
