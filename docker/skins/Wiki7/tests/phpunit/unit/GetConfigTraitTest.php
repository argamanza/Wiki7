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

namespace MediaWiki\Skins\Wiki7\Tests\Unit;

use MediaWiki\Config\Config;
use MediaWiki\Config\ConfigException;
use MediaWiki\Output\OutputPage;
use MediaWiki\Skins\Wiki7\GetConfigTrait;
use MediaWikiUnitTestCase;

/**
 * Test class that uses the GetConfigTrait for testing.
 * This allows us to test the trait in isolation without needing the full SkinTemplate.
 */
class GetConfigTraitTestClass {
	use GetConfigTrait;

	/**
	 * Expose the protected method for testing.
	 *
	 * @param string $key
	 * @param OutputPage|null $out
	 * @return mixed|null
	 */
	public function testGetConfigValue( $key, $out = null ) {
		return $this->getConfigValue( $key, $out );
	}
}

/**
 * Test class that has an $out property (simulating a Partial that stores OutputPage).
 */
class GetConfigTraitWithOutPropertyTestClass {
	use GetConfigTrait;

	public OutputPage $out;

	public function __construct( OutputPage $out ) {
		$this->out = $out;
	}

	public function testGetConfigValue( $key, $out = null ) {
		return $this->getConfigValue( $key, $out );
	}
}

/**
 * Test class that has a getOutput() method (simulating SkinTemplate behavior).
 */
class GetConfigTraitWithGetOutputTestClass {
	use GetConfigTrait;

	private OutputPage $outputPage;

	public function __construct( OutputPage $out ) {
		$this->outputPage = $out;
	}

	public function getOutput(): OutputPage {
		return $this->outputPage;
	}

	public function testGetConfigValue( $key, $out = null ) {
		return $this->getConfigValue( $key, $out );
	}
}

/**
 * @group Wiki7
 * @coversDefaultClass \MediaWiki\Skins\Wiki7\GetConfigTrait
 */
class GetConfigTraitTest extends MediaWikiUnitTestCase {

	/**
	 * Create a mock OutputPage that returns the given config value.
	 *
	 * @param string $key
	 * @param mixed $value
	 * @return OutputPage
	 */
	private function createMockOutputPage( string $key, $value ): OutputPage {
		$config = $this->createMock( Config::class );
		$config->method( 'get' )->with( $key )->willReturn( $value );

		$out = $this->createMock( OutputPage::class );
		$out->method( 'getConfig' )->willReturn( $config );

		return $out;
	}

	/**
	 * Create a mock OutputPage that throws ConfigException for the given key.
	 *
	 * @param string $key
	 * @return OutputPage
	 */
	private function createMockOutputPageThrowingException( string $key ): OutputPage {
		$config = $this->createMock( Config::class );
		$config->method( 'get' )->with( $key )->willThrowException(
			new ConfigException( "Config key '$key' not found" )
		);

		$out = $this->createMock( OutputPage::class );
		$out->method( 'getConfig' )->willReturn( $config );

		return $out;
	}

	/**
	 * Test that getConfigValue returns the correct value when passed an OutputPage.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_withOutputPage_returnsValue(): void {
		$out = $this->createMockOutputPage( 'Wiki7EnablePreferences', true );

		$obj = new GetConfigTraitTestClass();
		$result = $obj->testGetConfigValue( 'Wiki7EnablePreferences', $out );

		$this->assertTrue( $result );
	}

	/**
	 * Test that getConfigValue returns a string config value.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_stringValue_returnsString(): void {
		$out = $this->createMockOutputPage( 'Wiki7ThemeDefault', 'auto' );

		$obj = new GetConfigTraitTestClass();
		$result = $obj->testGetConfigValue( 'Wiki7ThemeDefault', $out );

		$this->assertEquals( 'auto', $result );
	}

	/**
	 * Test that getConfigValue returns null when ConfigException is thrown.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_configException_returnsNull(): void {
		$out = $this->createMockOutputPageThrowingException( 'NonExistentKey' );

		$obj = new GetConfigTraitTestClass();
		$result = $obj->testGetConfigValue( 'NonExistentKey', $out );

		$this->assertNull( $result,
			'getConfigValue should return null when ConfigException is thrown' );
	}

	/**
	 * Test that getConfigValue uses the $out property when available.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_usesOutProperty_whenAvailable(): void {
		$outProp = $this->createMockOutputPage( 'Wiki7EnableManifest', true );

		$obj = new GetConfigTraitWithOutPropertyTestClass( $outProp );
		// Pass null as the $out parameter - it should use the property instead
		$result = $obj->testGetConfigValue( 'Wiki7EnableManifest', null );

		$this->assertTrue( $result,
			'getConfigValue should use the $out property when available' );
	}

	/**
	 * Test that getConfigValue uses getOutput() method when available.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_usesGetOutput_whenCallable(): void {
		$outFromMethod = $this->createMockOutputPage( 'Wiki7SearchGateway', 'mwRestApi' );

		$obj = new GetConfigTraitWithGetOutputTestClass( $outFromMethod );
		// Pass null as $out - it should use getOutput() instead
		$result = $obj->testGetConfigValue( 'Wiki7SearchGateway', null );

		$this->assertEquals( 'mwRestApi', $result,
			'getConfigValue should use getOutput() when callable' );
	}

	/**
	 * Test that getConfigValue returns various data types correctly.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_returnsVariousTypes(): void {
		$obj = new GetConfigTraitTestClass();

		// Boolean
		$out = $this->createMockOutputPage( 'BoolKey', false );
		$this->assertFalse( $obj->testGetConfigValue( 'BoolKey', $out ) );

		// Integer
		$out = $this->createMockOutputPage( 'IntKey', 42 );
		$this->assertEquals( 42, $obj->testGetConfigValue( 'IntKey', $out ) );

		// Array
		$out = $this->createMockOutputPage( 'ArrayKey', [ 'a', 'b' ] );
		$this->assertEquals( [ 'a', 'b' ], $obj->testGetConfigValue( 'ArrayKey', $out ) );
	}

	/**
	 * Test that getConfigValue handles ConfigException gracefully for unknown keys
	 * in the getOutput() flow.
	 *
	 * @covers ::getConfigValue
	 */
	public function testGetConfigValue_getOutputFlow_configException_returnsNull(): void {
		$out = $this->createMockOutputPageThrowingException( 'UnknownKey' );

		$obj = new GetConfigTraitWithGetOutputTestClass( $out );
		$result = $obj->testGetConfigValue( 'UnknownKey' );

		$this->assertNull( $result,
			'getConfigValue should return null when ConfigException is thrown in getOutput() flow' );
	}

	/**
	 * Data provider for config key/value pairs.
	 *
	 * @return array[]
	 */
	public static function provideConfigValues(): array {
		return [
			'boolean true' => [ 'Wiki7EnablePreferences', true ],
			'boolean false' => [ 'Wiki7EnableManifest', false ],
			'string value' => [ 'Wiki7ThemeColor', '#0d0e12' ],
			'integer value' => [ 'Wiki7MaxSearchResults', 10 ],
			'array value' => [ 'Wiki7OverflowInheritedClasses', [ 'floatleft', 'floatright' ] ],
			'empty string' => [ 'Wiki7GlobalToolsPortlet', '' ],
		];
	}

	/**
	 * @covers ::getConfigValue
	 * @dataProvider provideConfigValues
	 */
	public function testGetConfigValue_variousConfigTypes( string $key, $expectedValue ): void {
		$config = $this->createMock( Config::class );
		$config->method( 'get' )->with( $key )->willReturn( $expectedValue );

		$out = $this->createMock( OutputPage::class );
		$out->method( 'getConfig' )->willReturn( $config );

		$obj = new GetConfigTraitTestClass();
		$result = $obj->testGetConfigValue( $key, $out );

		$this->assertSame( $expectedValue, $result );
	}
}
