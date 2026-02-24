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

namespace MediaWiki\Skins\Wiki7\Tests\Unit\Components;

use MediaWiki\Language\Language;
use MediaWiki\MediaWikiServices;
use MediaWiki\Output\OutputPage;
use MediaWiki\Skins\Wiki7\Components\Wiki7ComponentPageHeading;
use MediaWiki\Title\Title;
use MediaWikiUnitTestCase;
use MessageLocalizer;
use ReflectionMethod;

/**
 * @group Wiki7
 * @group Components
 * @coversDefaultClass \MediaWiki\Skins\Wiki7\Components\Wiki7ComponentPageHeading
 */
class Wiki7ComponentPageHeadingTest extends MediaWikiUnitTestCase {

	/**
	 * Create a Wiki7ComponentPageHeading instance with mocked dependencies.
	 *
	 * @param bool $isContentPage Whether the title is a content page
	 * @param string $titleData The HTML title heading string
	 * @param bool $isSpecialPage Whether the title is a special page
	 * @param bool $isTalkPage Whether the title is a talk page
	 * @param string|null $shortdesc Short description property from OutputPage
	 * @return Wiki7ComponentPageHeading
	 */
	private function createComponent(
		bool $isContentPage = true,
		string $titleData = '<h1 id="firstHeading"><span>Test Page</span></h1>',
		bool $isSpecialPage = false,
		bool $isTalkPage = false,
		?string $shortdesc = null
	): Wiki7ComponentPageHeading {
		$services = $this->createMock( MediaWikiServices::class );
		$localizer = $this->createMock( MessageLocalizer::class );
		$out = $this->createMock( OutputPage::class );
		$pageLang = $this->createMock( Language::class );
		$title = $this->createMock( Title::class );

		$title->method( 'isContentPage' )->willReturn( $isContentPage );
		$title->method( 'isSpecialPage' )->willReturn( $isSpecialPage );
		$title->method( 'isTalkPage' )->willReturn( $isTalkPage );
		$title->method( 'getText' )->willReturn( 'Test Page' );
		$title->method( 'getNsText' )->willReturn( '' );
		$title->method( 'inNamespace' )->willReturn( false );
		$title->method( 'isSubpage' )->willReturn( false );

		$out->method( 'getProperty' )->with( 'shortdesc' )->willReturn( $shortdesc );

		// Mock the message handling for tagline
		$msg = $this->createMock( \Message::class );
		$msg->method( 'isDisabled' )->willReturn( false );
		$msg->method( 'parse' )->willReturn( 'Site tagline' );
		$msg->method( 'text' )->willReturn( 'Site tagline' );
		$localizer->method( 'msg' )->willReturn( $msg );

		// Mock language converter factory for getTagline
		$langConv = $this->createMock( \MediaWiki\Language\ILanguageConverter::class );
		$langConv->method( 'convert' )->willReturnArgument( 0 );

		$langConverterFactory = $this->createMock( \MediaWiki\Language\LanguageConverterFactory::class );
		$langConverterFactory->method( 'getLanguageConverter' )->willReturn( $langConv );

		$contentLanguage = $this->createMock( Language::class );

		$services->method( 'getLanguageConverterFactory' )->willReturn( $langConverterFactory );
		$services->method( 'getContentLanguage' )->willReturn( $contentLanguage );

		return new Wiki7ComponentPageHeading(
			$services,
			$localizer,
			$out,
			$pageLang,
			$title,
			$titleData
		);
	}

	/**
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_returnsExpectedKeys(): void {
		$component = $this->createComponent();
		$data = $component->getTemplateData();

		$this->assertArrayHasKey( 'html-tagline', $data,
			'Template data should contain html-tagline' );
		$this->assertArrayHasKey( 'html-title-heading', $data,
			'Template data should contain html-title-heading' );
	}

	/**
	 * Test that getPageHeading wraps parenthetical text for content pages.
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_contentPage_wrapsParentheses(): void {
		$titleData = '<h1 id="firstHeading"><span>Test Page (Disambiguation)</span></h1>';
		$component = $this->createComponent(
			isContentPage: true,
			titleData: $titleData
		);
		$data = $component->getTemplateData();

		$this->assertStringContainsString(
			'mw-page-title-parenthesis',
			$data['html-title-heading'],
			'Parenthetical text on content pages should be wrapped with mw-page-title-parenthesis class'
		);
	}

	/**
	 * Test that getPageHeading does NOT modify non-content pages.
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_nonContentPage_preservesOriginal(): void {
		$titleData = '<h1 id="firstHeading"><span>Special:RecentChanges (Filtered)</span></h1>';
		$component = $this->createComponent(
			isContentPage: false,
			titleData: $titleData
		);
		$data = $component->getTemplateData();

		$this->assertEquals( $titleData, $data['html-title-heading'],
			'Non-content page headings should not be modified' );
	}

	/**
	 * Test that getPageHeading handles titles without parentheses.
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_contentPage_noParentheses_unchanged(): void {
		$titleData = '<h1 id="firstHeading"><span>Simple Title</span></h1>';
		$component = $this->createComponent(
			isContentPage: true,
			titleData: $titleData
		);
		$data = $component->getTemplateData();

		$this->assertEquals( $titleData, $data['html-title-heading'],
			'Titles without parentheses should not be modified' );
	}

	/**
	 * Test that getPageHeading preserves HTML entities in the title.
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_htmlSpecialCharsInTitle_preserved(): void {
		$titleData = '<h1 id="firstHeading"><span>Tom &amp; Jerry</span></h1>';
		$component = $this->createComponent(
			isContentPage: true,
			titleData: $titleData
		);
		$data = $component->getTemplateData();

		$this->assertStringContainsString( '&amp;', $data['html-title-heading'],
			'HTML entities should be preserved in the title' );
	}

	/**
	 * Test that the short description is used as the tagline when present.
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_withShortDescription_usesAsTagline(): void {
		$component = $this->createComponent(
			shortdesc: 'A short description of the page'
		);
		$data = $component->getTemplateData();

		$this->assertEquals( 'A short description of the page', $data['html-tagline'],
			'When a short description is set, it should be used as the tagline' );
	}

	/**
	 * Test that special pages return an empty tagline.
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_specialPage_emptyTagline(): void {
		$component = $this->createComponent(
			isSpecialPage: true,
			shortdesc: null
		);
		$data = $component->getTemplateData();

		$this->assertEmpty( $data['html-tagline'],
			'Special pages should have an empty tagline' );
	}

	/**
	 * Test the parenthesis wrapping regex handles displaytitle (h1 closing tag).
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_displayTitle_wrapsParentheses(): void {
		// When using {{DISPLAYTITLE}}, the closing tag is </h1>
		$titleData = '<h1 id="firstHeading">Page Name (Season 2)</h1>';
		$component = $this->createComponent(
			isContentPage: true,
			titleData: $titleData
		);
		$data = $component->getTemplateData();

		$this->assertStringContainsString(
			'mw-page-title-parenthesis',
			$data['html-title-heading'],
			'Parenthetical text in displaytitle (closing with </h1>) should be wrapped'
		);
		$this->assertStringContainsString(
			'(Season 2)',
			$data['html-title-heading'],
			'The parenthetical content should be preserved'
		);
	}

	/**
	 * Test that getPageHeading handles unicode parentheses (e.g. CJK brackets).
	 *
	 * @covers ::getTemplateData
	 */
	public function testGetTemplateData_unicodeParentheses_wrapped(): void {
		// The regex uses \p{Ps} (open punctuation) and \p{Pe} (close punctuation)
		// which matches CJK brackets like () and other unicode bracket types
		$titleData = '<h1 id="firstHeading"><span>Page Title (Note)</span></h1>';
		$component = $this->createComponent(
			isContentPage: true,
			titleData: $titleData
		);
		$data = $component->getTemplateData();

		$this->assertStringContainsString(
			'mw-page-title-parenthesis',
			$data['html-title-heading'],
			'Unicode parentheses (fullwidth) should also be wrapped'
		);
	}
}
