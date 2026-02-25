#!/usr/bin/env python3
"""Master orchestration script for the Wiki7 data pipeline.

Chains together: scrape -> normalize -> import to MediaWiki.

Usage:
    python run_pipeline.py                        # Full pipeline (scrape + normalize + import)
    python run_pipeline.py --dry-run              # Preview what would be imported
    python run_pipeline.py --skip-scrape          # Skip scraping, just normalize + import
    python run_pipeline.py --season 2023          # Run for a specific season
    python run_pipeline.py --skip-scrape --dry-run  # Normalize existing data and preview import
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

import click

logger = logging.getLogger("wiki7_pipeline")

# Project directory layout
DATA_DIR = Path(__file__).resolve().parent
SCRAPER_DIR = DATA_DIR / "tmk-scraper"
SCRAPER_OUTPUT_DIR = SCRAPER_DIR / "output"
PIPELINE_DIR = DATA_DIR / "data_pipeline"
PIPELINE_OUTPUT_DIR = PIPELINE_DIR / "output"


def _run_spider(spider_name: str, season: str, output_file: str, extra_args: list | None = None) -> bool:
    """Run a Scrapy spider and return True on success."""
    output_path = SCRAPER_OUTPUT_DIR / output_file

    # Remove existing output to avoid appending to stale data
    if output_path.exists():
        output_path.unlink()
        logger.info("Removed stale output: %s", output_path)

    cmd = [
        sys.executable, "-m", "scrapy", "crawl", spider_name,
        "-a", f"season={season}",
        "-o", str(output_path),
    ]
    if extra_args:
        cmd.extend(extra_args)

    logger.info("Running spider: %s", spider_name)
    logger.debug("Command: %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=str(SCRAPER_DIR),
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error("Spider '%s' failed (exit code %d)", spider_name, result.returncode)
        if result.stderr:
            for line in result.stderr.strip().split("\n")[-10:]:
                logger.error("  %s", line)
        return False

    if not output_path.exists():
        logger.error("Spider '%s' produced no output at %s", spider_name, output_path)
        return False

    logger.info("Spider '%s' completed -> %s", spider_name, output_path)
    return True


def run_scrape(season: str) -> bool:
    """Run all four spiders in the correct order.

    Order matters:
    1. squad - produces squad.json (player list with profile URLs)
    2. player - reads squad.json, produces players.json
    3. fixtures - produces fixtures.json (match list with report URLs)
    4. match - reads fixtures.json, produces matches.json
    """
    SCRAPER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    spiders = [
        ("squad", "squad.json"),
        ("player", "players.json"),
        ("fixtures", "fixtures.json"),
        ("match", "matches.json"),
    ]

    for spider_name, output_file in spiders:
        if not _run_spider(spider_name, season, output_file):
            logger.error("Pipeline aborted: spider '%s' failed", spider_name)
            return False

    logger.info("All spiders completed successfully")
    return True


def run_normalize() -> bool:
    """Run the normalization pipeline."""
    logger.info("Running normalization pipeline...")
    try:
        from data_pipeline.normalize_enrich_players import main as normalize_main
        normalize_main(
            raw_path=SCRAPER_OUTPUT_DIR / "players.json",
            out_dir=PIPELINE_OUTPUT_DIR,
        )
        logger.info("Normalization completed")
        return True
    except FileNotFoundError as exc:
        logger.error("Normalization failed: %s", exc)
        return False
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("Normalization failed with data error: %s", exc)
        return False


def run_import(season: str, dry_run: bool = False, wiki_url: str | None = None) -> bool:
    """Run the MediaWiki import step.

    If wiki_url is not set, forces dry_run mode.
    """
    if not wiki_url:
        if not dry_run:
            logger.warning("No WIKI_URL configured. Forcing dry-run mode.")
        dry_run = True

    site = None
    if not dry_run:
        import mwclient
        import os
        try:
            site = mwclient.Site(wiki_url, path="/")
            wiki_user = os.environ.get("WIKI_BOT_USER", "")
            wiki_pass = os.environ.get("WIKI_BOT_PASS", "")
            if wiki_user and wiki_pass:
                site.login(wiki_user, wiki_pass)
                logger.info("Logged in to %s as %s", wiki_url, wiki_user)
            else:
                logger.warning("WIKI_BOT_USER/WIKI_BOT_PASS not set; proceeding without auth")
        except (mwclient.errors.LoginError, ConnectionError) as exc:
            logger.error("Failed to connect to wiki at %s: %s", wiki_url, exc)
            return False

    from wiki_import.import_players import import_players
    from wiki_import.import_matches import import_matches
    from wiki_import.import_templates import import_cargo_templates, import_squad_page, import_transfer_page

    results = {}
    all_ok = True

    try:
        logger.info("Importing Cargo templates...")
        results["cargo"] = import_cargo_templates(site=site, dry_run=dry_run)
    except FileNotFoundError as exc:
        logger.error("Cargo template import failed: %s", exc)
        all_ok = False

    try:
        logger.info("Importing player pages...")
        results["players"] = import_players(site=site, dry_run=dry_run)
    except FileNotFoundError as exc:
        logger.error("Player import failed: %s", exc)
        all_ok = False

    try:
        logger.info("Importing match report pages...")
        results["matches"] = import_matches(site=site, dry_run=dry_run)
    except FileNotFoundError as exc:
        logger.error("Match import failed: %s", exc)
        all_ok = False

    try:
        logger.info("Importing squad page...")
        results["squad"] = import_squad_page(site=site, season=season, dry_run=dry_run)
    except FileNotFoundError as exc:
        logger.error("Squad page import failed: %s", exc)
        all_ok = False

    try:
        logger.info("Importing transfer page...")
        results["transfers"] = import_transfer_page(site=site, season=season, dry_run=dry_run)
    except FileNotFoundError as exc:
        logger.error("Transfer page import failed: %s", exc)
        all_ok = False

    # Print summary
    logger.info("=" * 60)
    logger.info("IMPORT SUMMARY%s", " (DRY RUN)" if dry_run else "")
    logger.info("=" * 60)
    total_created = total_updated = total_skipped = total_failed = 0
    for step, result in results.items():
        c, u, s, f = result["created"], result["updated"], result["skipped"], result["failed"]
        total_created += c
        total_updated += u
        total_skipped += s
        total_failed += f
        logger.info(
            "  %-12s: %d created, %d updated, %d skipped, %d failed",
            step, c, u, s, f,
        )
        for err in result.get("errors", []):
            logger.error("    ERROR: %s -> %s", err["page"], err["error"])

    logger.info("-" * 60)
    logger.info(
        "  TOTAL: %d created, %d updated, %d skipped, %d failed",
        total_created, total_updated, total_skipped, total_failed,
    )

    return all_ok and total_failed == 0


@click.command()
@click.option("--season", default="2024", help="Season year to process (default: 2024)")
@click.option("--dry-run", is_flag=True, help="Preview import without writing to wiki")
@click.option("--skip-scrape", is_flag=True, help="Skip the scraping step")
@click.option("--skip-normalize", is_flag=True, help="Skip the normalization step")
@click.option("--skip-import", is_flag=True, help="Skip the wiki import step")
@click.option("--wiki-url", envvar="WIKI_URL", default=None, help="MediaWiki site URL (or set WIKI_URL env var)")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(season, dry_run, skip_scrape, skip_normalize, skip_import, wiki_url, verbose):
    """Wiki7 data pipeline: scrape -> normalize -> import."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)-20s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    start_time = time.time()
    logger.info("Wiki7 pipeline starting (season=%s, dry_run=%s)", season, dry_run)
    errors = []

    # Step 1: Scrape
    if not skip_scrape:
        logger.info("=" * 60)
        logger.info("STEP 1: SCRAPING (season=%s)", season)
        logger.info("=" * 60)
        if not run_scrape(season):
            errors.append("Scraping failed")
            logger.error("Scraping failed. Continuing with existing data if available...")
    else:
        logger.info("Skipping scrape step (--skip-scrape)")

    # Step 2: Normalize
    if not skip_normalize:
        logger.info("=" * 60)
        logger.info("STEP 2: NORMALIZATION")
        logger.info("=" * 60)
        if not run_normalize():
            errors.append("Normalization failed")
            logger.error("Normalization failed.")
    else:
        logger.info("Skipping normalize step (--skip-normalize)")

    # Step 3: Import
    if not skip_import:
        logger.info("=" * 60)
        logger.info("STEP 3: WIKI IMPORT%s", " (DRY RUN)" if dry_run else "")
        logger.info("=" * 60)
        if not run_import(season, dry_run=dry_run, wiki_url=wiki_url):
            errors.append("Wiki import had failures")
    else:
        logger.info("Skipping import step (--skip-import)")

    # Final summary
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    if errors:
        logger.error("PIPELINE FINISHED WITH ERRORS (%.1fs):", elapsed)
        for err in errors:
            logger.error("  - %s", err)
        sys.exit(1)
    else:
        logger.info("PIPELINE COMPLETED SUCCESSFULLY (%.1fs)", elapsed)


if __name__ == "__main__":
    main()
