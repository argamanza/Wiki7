<?php
/**
 * PHPUnit bootstrap file for the Wiki7 skin.
 *
 * This bootstrap attempts to load MediaWiki's PHPUnit bootstrap.
 * When running via MediaWiki's test runner (e.g., `php tests/phpunit/phpunit.php`),
 * the framework is already loaded.
 *
 * For standalone execution, set MW_INSTALL_PATH to your MediaWiki installation.
 */

// If MediaWiki's test framework is already loaded, nothing to do.
if ( class_exists( 'MediaWikiUnitTestCase' ) ) {
	return;
}

// Attempt to find MediaWiki's PHPUnit bootstrap
$mwInstallPath = getenv( 'MW_INSTALL_PATH' );
if ( !$mwInstallPath ) {
	// Common paths relative to the skin's test directory
	$candidates = [
		// Standard MediaWiki installation layout
		dirname( __DIR__, 5 ) . '/tests/phpunit/MediaWikiUnitTestCase.php',
		// Docker layout
		'/var/www/html/tests/phpunit/MediaWikiUnitTestCase.php',
	];
	foreach ( $candidates as $candidate ) {
		if ( file_exists( $candidate ) ) {
			$mwInstallPath = dirname( $candidate, 3 );
			break;
		}
	}
}

if ( $mwInstallPath && file_exists( "$mwInstallPath/tests/phpunit/MediaWikiUnitTestCase.php" ) ) {
	require_once "$mwInstallPath/tests/phpunit/MediaWikiUnitTestCase.php";
}
