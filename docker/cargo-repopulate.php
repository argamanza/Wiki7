<?php
/**
 * Re-parse sample data pages to populate Cargo tables.
 *
 * Run AFTER import-pages.php and cargoRecreateData so that:
 *  1. Infobox templates exist (contain #cargo_store)
 *  2. Cargo SQL tables exist (created by cargoRecreateData)
 *
 * This script forces a re-parse of each page, triggering #cargo_store
 * to insert data into the now-existing Cargo tables.
 *
 * Usage: php maintenance/run.php /var/www/html/cargo-repopulate.php
 */

require_once __DIR__ . '/maintenance/Maintenance.php';

use MediaWiki\Title\Title;

class CargoRepopulateSampleData extends Maintenance {

    public function __construct() {
        parent::__construct();
        $this->addDescription( 'Re-parse sample data pages to populate Cargo tables via #cargo_store' );
    }

    /** Pages that contain infobox templates with #cargo_store. */
    private function getSamplePages(): array {
        return [
            'הנה באנו',
            'אדום זה הצבע',
            'שער שער שער',
            'חולצת אליפות 2016',
            'כרטיס גמר גביע 1997',
            'מדליית אליפות 2017',
            'מדי בית 2024/25',
            'מדי חוץ 2024/25',
        ];
    }

    public function execute() {
        $pages = $this->getSamplePages();
        $stored = 0;
        $skipped = 0;

        foreach ( $pages as $pageName ) {
            $title = Title::newFromText( $pageName );
            if ( !$title || !$title->exists() ) {
                $this->output( "  SKIP (not found): $pageName\n" );
                $skipped++;
                continue;
            }

            $wikiPage = $this->getServiceContainer()
                ->getWikiPageFactory()
                ->newFromTitle( $title );
            $content = $wikiPage->getContent();
            if ( !$content ) {
                $this->output( "  SKIP (no content): $pageName\n" );
                $skipped++;
                continue;
            }

            $contentText = CargoUtils::getContentText( $content );

            // Delete any existing Cargo data for this page, then re-parse.
            // Use 'page save' origin so #cargo_store stores to any table
            // (unlike 'template' origin which filters by dbTableName).
            CargoStore::$settings['origin'] = 'page save';
            CargoUtils::parsePageForStorage( $title, $contentText );

            $this->output( "  STORED: $pageName\n" );
            $stored++;
        }

        $this->output( "\nCargo repopulate: $stored stored, $skipped skipped.\n" );
    }
}

$maintClass = CargoRepopulateSampleData::class;
require_once RUN_MAINTENANCE_IF_MAIN;
