#!/usr/bin/env python3
"""Master orchestration script for the Wiki7 data pipeline.

Chains together: scrape -> normalize -> merge -> import to MediaWiki.

Usage:
    python run_pipeline.py                              # Full pipeline, single season (2024)
    python run_pipeline.py --dry-run                    # Preview what would be imported
    python run_pipeline.py --skip-scrape                # Skip scraping, just normalize + import
    python run_pipeline.py --season 2023                # Run for a specific season
    python run_pipeline.py --seasons 2015-2025          # Run for multiple seasons
    python run_pipeline.py --seasons 2015,2020,2024     # Run for specific seasons
    python run_pipeline.py --skip-scrape --dry-run      # Normalize existing data and preview import
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


def parse_seasons(seasons_arg: str) -> list[str]:
    """Parse --seasons argument into list of season year strings.

    Supports range ('2015-2025') and comma-separated ('2015,2020,2024') formats.
    """
    if "-" in seasons_arg and "," not in seasons_arg:
        parts = seasons_arg.split("-")
        return [str(y) for y in range(int(parts[0]), int(parts[1]) + 1)]
    return [s.strip() for s in seasons_arg.split(",")]


def _run_spider(spider_name: str, season: str, output_file: str) -> bool:
    """Run a Scrapy spider and return True on success."""
    season_output_dir = SCRAPER_OUTPUT_DIR / season
    season_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = season_output_dir / output_file

    if output_path.exists():
        output_path.unlink()
        logger.info("Removed stale output: %s", output_path)

    cmd = [
        sys.executable, "-m", "scrapy", "crawl", spider_name,
        "-a", f"season={season}",
        "-o", str(output_path),
    ]

    logger.info("Running spider: %s (season=%s)", spider_name, season)

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
    """Run all five spiders in the correct order for a single season."""
    spiders = [
        ("squad", "squad.json"),
        ("player", "players.json"),
        ("stats", "stats.json"),
        ("fixtures", "fixtures.json"),
        ("match", "matches.json"),
    ]

    for spider_name, output_file in spiders:
        if not _run_spider(spider_name, season, output_file):
            logger.error("Pipeline aborted: spider '%s' failed for season %s", spider_name, season)
            return False

    logger.info("All spiders completed successfully for season %s", season)
    return True


def run_normalize(season: str) -> bool:
    """Run the normalization pipeline for a single season."""
    logger.info("Running normalization pipeline for season %s...", season)
    try:
        from data_pipeline.normalize_enrich_players import main as normalize_main

        scraper_season_dir = SCRAPER_OUTPUT_DIR / season
        pipeline_season_dir = PIPELINE_OUTPUT_DIR / season

        normalize_main(
            raw_path=scraper_season_dir / "players.json",
            stats_path=scraper_season_dir / "stats.json",
            out_dir=pipeline_season_dir,
        )
        logger.info("Normalization completed for season %s", season)
        return True
    except FileNotFoundError as exc:
        logger.error("Normalization failed for season %s: %s", season, exc)
        return False
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("Normalization failed with data error for season %s: %s", season, exc)
        return False


def run_merge(seasons: list[str]) -> bool:
    """Merge normalized data from multiple seasons."""
    logger.info("Merging data from %d seasons...", len(seasons))
    try:
        from data_pipeline.merge_seasons import merge_seasons
        merge_seasons(
            base_dir=PIPELINE_OUTPUT_DIR,
            seasons=seasons,
            output_dir=PIPELINE_OUTPUT_DIR / "merged",
        )
        logger.info("Merge completed")
        return True
    except FileNotFoundError as exc:
        logger.error("Merge failed: %s", exc)
        return False


def run_import(
    seasons: list[str],
    dry_run: bool = False,
    wiki_url: str | None = None,
    data_dir: Path | None = None,
) -> bool:
    """Run the MediaWiki import step."""
    import os

    if not wiki_url:
        if not dry_run:
            logger.warning("No WIKI_URL configured. Forcing dry-run mode.")
        dry_run = True

    site = None
    if not dry_run:
        import mwclient
        try:
            site = mwclient.Site(wiki_url, path="/")
            wiki_user = os.environ.get("WIKI_BOT_USER", "")
            wiki_pass = os.environ.get("WIKI_BOT_PASS", "")
            if wiki_user and wiki_pass:
                site.login(wiki_user, wiki_pass)
                logger.info("Logged in to %s as %s", wiki_url, wiki_user)
            else:
                logger.warning("WIKI_BOT_USER/WIKI_BOT_PASS not set; proceeding without auth")
        except Exception as exc:
            logger.error("Failed to connect to wiki at %s: %s", wiki_url, exc)
            return False

    from wiki_import.import_players import import_players
    from wiki_import.import_matches import import_matches
    from wiki_import.import_templates import import_cargo_templates, import_squad_page, import_transfer_page

    # Determine data directory (merged or single-season)
    resolved_data_dir = data_dir or PIPELINE_OUTPUT_DIR

    results = {}
    all_ok = True

    # Cargo templates (once)
    try:
        logger.info("Importing Cargo templates...")
        results["cargo"] = import_cargo_templates(site=site, dry_run=dry_run)
    except FileNotFoundError as exc:
        logger.error("Cargo template import failed: %s", exc)
        all_ok = False

    # Player pages (from merged/single data dir)
    try:
        logger.info("Importing player pages...")
        players_path = resolved_data_dir / "players.jsonl"
        # Check for Hebrew-enriched version
        he_path = resolved_data_dir / "players.he.jsonl"
        if he_path.exists():
            players_path = he_path
        results["players"] = import_players(
            site=site,
            players_path=players_path,
            transfers_path=resolved_data_dir / "transfers.jsonl",
            market_values_path=resolved_data_dir / "market_values.jsonl",
            stats_path=resolved_data_dir / "stats.jsonl",
            dry_run=dry_run,
        )
    except FileNotFoundError as exc:
        logger.error("Player import failed: %s", exc)
        all_ok = False

    # Match reports (per season)
    for season in seasons:
        try:
            matches_path = SCRAPER_OUTPUT_DIR / season / "matches.json"
            if matches_path.exists():
                logger.info("Importing match reports for season %s...", season)
                results[f"matches_{season}"] = import_matches(
                    site=site, matches_path=matches_path, dry_run=dry_run,
                )
        except FileNotFoundError as exc:
            logger.error("Match import failed for season %s: %s", season, exc)
            all_ok = False

    # Squad and transfer pages (per season)
    for season in seasons:
        try:
            logger.info("Importing squad page for season %s...", season)
            results[f"squad_{season}"] = import_squad_page(
                site=site, season=season,
                players_path=resolved_data_dir / "players.jsonl",
                stats_path=resolved_data_dir / "stats.jsonl",
                dry_run=dry_run,
            )
        except FileNotFoundError as exc:
            logger.error("Squad page import failed for season %s: %s", season, exc)
            all_ok = False

        try:
            logger.info("Importing transfer page for season %s...", season)
            results[f"transfers_{season}"] = import_transfer_page(
                site=site, season=season,
                players_path=resolved_data_dir / "players.jsonl",
                transfers_path=resolved_data_dir / "transfers.jsonl",
                dry_run=dry_run,
            )
        except FileNotFoundError as exc:
            logger.error("Transfer page import failed for season %s: %s", season, exc)
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
            "  %-20s: %d created, %d updated, %d skipped, %d failed",
            step, c, u, s, f,
        )

    logger.info("-" * 60)
    logger.info(
        "  TOTAL: %d created, %d updated, %d skipped, %d failed",
        total_created, total_updated, total_skipped, total_failed,
    )

    return all_ok and total_failed == 0


@click.command()
@click.option("--season", default="2024", help="Season year to process (default: 2024)")
@click.option("--seasons", default=None, help="Multi-season range (e.g., '2015-2025') or list (e.g., '2015,2020,2024')")
@click.option("--dry-run", is_flag=True, help="Preview import without writing to wiki")
@click.option("--skip-scrape", is_flag=True, help="Skip the scraping step")
@click.option("--skip-normalize", is_flag=True, help="Skip the normalization step")
@click.option("--skip-merge", is_flag=True, help="Skip the merge step")
@click.option("--skip-import", is_flag=True, help="Skip the wiki import step")
@click.option("--wiki-url", envvar="WIKI_URL", default=None, help="MediaWiki site URL (or set WIKI_URL env var)")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(season, seasons, dry_run, skip_scrape, skip_normalize, skip_merge, skip_import, wiki_url, verbose):
    """Wiki7 data pipeline: scrape -> normalize -> merge -> import."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)-20s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    # Determine season list
    if seasons:
        season_list = parse_seasons(seasons)
        multi_season = True
    else:
        season_list = [season]
        multi_season = False

    start_time = time.time()
    logger.info(
        "Wiki7 pipeline starting (seasons=%s, dry_run=%s, multi_season=%s)",
        season_list, dry_run, multi_season,
    )
    errors = []

    # Step 1: Scrape (per season)
    if not skip_scrape:
        logger.info("=" * 60)
        logger.info("STEP 1: SCRAPING (%d seasons)", len(season_list))
        logger.info("=" * 60)
        for s in season_list:
            logger.info("--- Scraping season %s ---", s)
            if not run_scrape(s):
                errors.append(f"Scraping failed for season {s}")
                logger.error("Scraping failed for season %s. Continuing with next...", s)
    else:
        logger.info("Skipping scrape step (--skip-scrape)")

    # Step 2: Normalize (per season)
    if not skip_normalize:
        logger.info("=" * 60)
        logger.info("STEP 2: NORMALIZATION (%d seasons)", len(season_list))
        logger.info("=" * 60)
        for s in season_list:
            logger.info("--- Normalizing season %s ---", s)
            if not run_normalize(s):
                errors.append(f"Normalization failed for season {s}")
                logger.error("Normalization failed for season %s.", s)
    else:
        logger.info("Skipping normalize step (--skip-normalize)")

    # Step 3: Merge (multi-season only)
    data_dir = None
    if multi_season and not skip_merge:
        logger.info("=" * 60)
        logger.info("STEP 3: MERGE (%d seasons)", len(season_list))
        logger.info("=" * 60)
        if not run_merge(season_list):
            errors.append("Merge failed")
            logger.error("Merge failed.")
        else:
            data_dir = PIPELINE_OUTPUT_DIR / "merged"
    elif multi_season:
        logger.info("Skipping merge step (--skip-merge)")
        data_dir = PIPELINE_OUTPUT_DIR / "merged"
    else:
        # Single season: use season-specific dir
        data_dir = PIPELINE_OUTPUT_DIR / season_list[0]

    # Step 4: Import
    if not skip_import:
        step_num = 4 if multi_season else 3
        logger.info("=" * 60)
        logger.info("STEP %d: WIKI IMPORT%s", step_num, " (DRY RUN)" if dry_run else "")
        logger.info("=" * 60)
        if not run_import(season_list, dry_run=dry_run, wiki_url=wiki_url, data_dir=data_dir):
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
