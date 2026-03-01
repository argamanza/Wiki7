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

import json
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

    verbose = logger.isEnabledFor(logging.DEBUG)
    logger.info("Running spider: %s (season=%s)", spider_name, season)

    result = subprocess.run(
        cmd,
        cwd=str(SCRAPER_DIR),
        stdout=None if verbose else subprocess.DEVNULL,
        stderr=None if verbose else subprocess.PIPE,
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

    # Check output file has actual data
    # squad, player, and stats are critical — empty means Transfermarkt is blocking us.
    # fixtures and match may legitimately return [] (future/incomplete seasons).
    CRITICAL_SPIDERS = {"squad", "player", "stats"}
    with open(output_path, "r") as f:
        data = json.load(f)
    if not data:
        if spider_name in CRITICAL_SPIDERS:
            logger.error("Spider '%s' returned empty results for season %s", spider_name, season)
            return False
        logger.warning("Spider '%s' returned empty results for season %s (non-critical, continuing)", spider_name, season)

    logger.info("Spider '%s' completed -> %s", spider_name, output_path)
    return True


# Per-season spiders (run once per season)
ALL_SPIDERS = [
    ("squad", "squad.json"),
    ("player", "players.json"),
    ("stats", "stats.json"),
    ("fixtures", "fixtures.json"),
    ("match", "matches.json"),
    ("transfers", "transfers.json"),
]

# Club-level spiders (run once, not per-season)
CLUB_SPIDERS = [
    ("coach", "coaches.json"),
    ("honours", "honours.json"),
    ("stadium", "stadium.json"),
    ("records", "records.json"),
]


def run_scrape(season: str, only: set[str] | None = None) -> bool:
    """Run per-season spiders in the correct order for a single season.

    If *only* is given, run just those spiders (order is preserved).
    """
    spiders = [(n, f) for n, f in ALL_SPIDERS if only is None or n in only]

    for spider_name, output_file in spiders:
        if not _run_spider(spider_name, season, output_file):
            logger.error("Pipeline aborted: spider '%s' failed for season %s", spider_name, season)
            return False

    logger.info("All spiders completed successfully for season %s", season)
    return True


def run_club_scrape(only: set[str] | None = None) -> bool:
    """Run club-level spiders (not per-season).

    These are run once and output to the base scraper output directory.
    """
    spiders = [(n, f) for n, f in CLUB_SPIDERS if only is None or n in only]

    if not spiders:
        return True

    for spider_name, output_file in spiders:
        output_path = SCRAPER_OUTPUT_DIR / output_file
        if output_path.exists():
            output_path.unlink()
            logger.info("Removed stale output: %s", output_path)

        cmd = [
            sys.executable, "-m", "scrapy", "crawl", spider_name,
            "-o", str(output_path),
        ]

        verbose = logger.isEnabledFor(logging.DEBUG)
        logger.info("Running club spider: %s", spider_name)

        result = subprocess.run(
            cmd,
            cwd=str(SCRAPER_DIR),
            stdout=None if verbose else subprocess.DEVNULL,
            stderr=None if verbose else subprocess.PIPE,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            logger.error("Club spider '%s' failed (exit code %d)", spider_name, result.returncode)
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-10:]:
                    logger.error("  %s", line)
            return False

        logger.info("Club spider '%s' completed -> %s", spider_name, output_path)

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
        from urllib.parse import urlparse
        try:
            parsed = urlparse(wiki_url if "://" in wiki_url else f"http://{wiki_url}")
            host = parsed.hostname or wiki_url
            port = parsed.port
            scheme = parsed.scheme or ("http" if host in ("localhost", "127.0.0.1") else "https")
            host_str = f"{host}:{port}" if port else host
            site = mwclient.Site(host_str, path="/", scheme=scheme)
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
    from wiki_import.import_templates import (
        import_cargo_templates, import_squad_page, import_transfer_page,
        import_coaches_page, import_honours_page, import_stadium_page,
        import_records_page, import_season_overview, import_leaderboards,
        import_attendance, import_competition_pages,
    )

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

    # Season overview pages (per season)
    for season in seasons:
        try:
            logger.info("Importing season overview for %s...", season)
            results[f"season_{season}"] = import_season_overview(
                site=site, season=season,
                players_path=resolved_data_dir / "players.jsonl",
                stats_path=resolved_data_dir / "stats.jsonl",
                dry_run=dry_run,
            )
        except FileNotFoundError as exc:
            logger.error("Season overview import failed for %s: %s", season, exc)
            all_ok = False

    # Club-level pages (once)
    for label, func, kwargs in [
        ("coaches", import_coaches_page, {}),
        ("honours", import_honours_page, {}),
        ("stadium", import_stadium_page, {}),
        ("records", import_records_page, {}),
    ]:
        try:
            logger.info("Importing %s page...", label)
            results[label] = func(site=site, dry_run=dry_run, **kwargs)
        except FileNotFoundError as exc:
            logger.error("%s import failed: %s", label, exc)
            all_ok = False

    # Leaderboards (from merged stats)
    try:
        logger.info("Importing leaderboard pages...")
        results["leaderboards"] = import_leaderboards(
            site=site,
            stats_path=resolved_data_dir / "stats.jsonl",
            players_path=resolved_data_dir / "players.jsonl",
            dry_run=dry_run,
        )
    except FileNotFoundError as exc:
        logger.error("Leaderboard import failed: %s", exc)
        all_ok = False

    # Attendance statistics (from all seasons' fixtures)
    try:
        logger.info("Importing attendance statistics...")
        results["attendance"] = import_attendance(
            site=site, seasons=seasons, dry_run=dry_run,
        )
    except FileNotFoundError as exc:
        logger.error("Attendance import failed: %s", exc)
        all_ok = False

    # Competition season pages
    try:
        logger.info("Importing competition pages...")
        results["competitions"] = import_competition_pages(
            site=site, seasons=seasons, dry_run=dry_run,
        )
    except FileNotFoundError as exc:
        logger.error("Competition pages import failed: %s", exc)
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
@click.option("--spiders", default=None, help="Run only these spiders (comma-separated, e.g., 'stats' or 'squad,player')")
@click.option("--skip-scrape", is_flag=True, help="Skip the scraping step")
@click.option("--skip-normalize", is_flag=True, help="Skip the normalization step")
@click.option("--skip-merge", is_flag=True, help="Skip the merge step")
@click.option("--skip-import", is_flag=True, help="Skip the wiki import step")
@click.option("--wiki-url", envvar="WIKI_URL", default=None, help="MediaWiki site URL (or set WIKI_URL env var)")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(season, seasons, spiders, dry_run, skip_scrape, skip_normalize, skip_merge, skip_import, wiki_url, verbose):
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

    # Parse --spiders filter
    spider_filter = None
    if spiders:
        valid_names = {name for name, _ in ALL_SPIDERS} | {name for name, _ in CLUB_SPIDERS}
        spider_filter = {s.strip() for s in spiders.split(",")}
        unknown = spider_filter - valid_names
        if unknown:
            logger.error("Unknown spider(s): %s (valid: %s)", ", ".join(unknown), ", ".join(sorted(valid_names)))
            sys.exit(1)

    start_time = time.time()
    logger.info(
        "Wiki7 pipeline starting (seasons=%s, dry_run=%s, multi_season=%s)",
        season_list, dry_run, multi_season,
    )
    errors = []

    # Step 1: Scrape (per season + club-level)
    if not skip_scrape:
        logger.info("=" * 60)
        logger.info("STEP 1: SCRAPING (%d seasons)", len(season_list))
        logger.info("=" * 60)
        for s in season_list:
            logger.info("--- Scraping season %s ---", s)
            if not run_scrape(s, only=spider_filter):
                errors.append(f"Scraping failed for season {s}")
                logger.error("Scraping failed for season %s. Continuing with next...", s)

        # Club-level spiders (run once, not per-season)
        club_filter = spider_filter
        if club_filter:
            club_names = {name for name, _ in CLUB_SPIDERS}
            club_filter = club_filter & club_names
        if club_filter is None or club_filter:
            logger.info("--- Scraping club-level data ---")
            if not run_club_scrape(only=club_filter):
                errors.append("Club-level scraping failed")
                logger.error("Club-level scraping failed")
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
