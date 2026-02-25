"""Import match report data into MediaWiki as wiki pages."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

import jinja2
import mwclient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

DEFAULT_MATCHES_PATH = Path(__file__).resolve().parent.parent / "tmk-scraper" / "output" / "matches.json"


def _load_json(path: Path) -> list:
    """Load a JSON array file."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def _content_hash(text: str) -> str:
    """Return an MD5 hex digest of the given text for change detection."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _render_template(template_name: str, **kwargs) -> str:
    """Render a Jinja2 template with the given context."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**kwargs)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((mwclient.errors.APIError, ConnectionError)),
    reraise=True,
)
def _edit_page(site: mwclient.Site, title: str, content: str, summary: str) -> bool:
    """Create or update a wiki page. Returns True if the page was changed."""
    page = site.pages[title]
    if page.exists:
        existing = page.text()
        if _content_hash(existing.strip()) == _content_hash(content.strip()):
            logger.debug("Page '%s' is unchanged, skipping", title)
            return False
    page.save(content, summary=summary)
    logger.info("Saved page: %s", title)
    return True


def _match_page_title(match: dict) -> str:
    """Generate a wiki page title for a match report.

    Format: "YYYY-MM-DD vs Opponent (Competition)"
    Falls back to simpler formats if data is missing.
    """
    date = match.get("date", "Unknown Date")
    opponent = match.get("opponent", "Unknown")
    competition = match.get("competition", "")

    # Clean up the date — Transfermarkt uses various formats
    title = f"{date} vs {opponent}"
    if competition:
        title += f" ({competition})"

    # Sanitize for MediaWiki title constraints
    title = title.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    title = title.replace("#", "").replace("|", "-")
    return title


def import_matches(
    site: Optional[mwclient.Site] = None,
    matches_path: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    """Import all match report pages into MediaWiki.

    Args:
        site: An authenticated mwclient.Site instance (None for dry-run).
        matches_path: Path to matches.json from the match spider.
        dry_run: If True, just preview changes without writing.

    Returns:
        A summary dict with counts of created, updated, skipped, and failed pages.
    """
    resolved_path = matches_path or DEFAULT_MATCHES_PATH
    matches = _load_json(resolved_path)

    summary = {"created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []}

    for match in matches:
        title = _match_page_title(match)
        try:
            content = _render_template("match_report.j2", match=match)

            if dry_run:
                logger.info("[DRY RUN] Would create/update page: %s (%d chars)", title, len(content))
                summary["created"] += 1
                continue

            if site is None:
                raise RuntimeError("site is required when dry_run=False")

            page = site.pages[title]
            if page.exists:
                existing = page.text()
                if _content_hash(existing.strip()) == _content_hash(content.strip()):
                    logger.debug("Page '%s' unchanged, skipping", title)
                    summary["skipped"] += 1
                    continue
                _edit_page(site, title, content, summary=f"Updated match report: {title}")
                summary["updated"] += 1
            else:
                _edit_page(site, title, content, summary=f"Created match report: {title}")
                summary["created"] += 1

        except (mwclient.errors.APIError, ConnectionError, RuntimeError) as exc:
            logger.error("Failed to import match '%s': %s", title, exc)
            summary["failed"] += 1
            summary["errors"].append({"page": title, "error": str(exc)})

    logger.info(
        "Match import complete: %d created, %d updated, %d skipped, %d failed",
        summary["created"], summary["updated"], summary["skipped"], summary["failed"],
    )
    return summary
