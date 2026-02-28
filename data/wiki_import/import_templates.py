"""Create/update Cargo table definition templates and season summary pages."""

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

DEFAULT_PLAYERS_PATH = Path(__file__).resolve().parent.parent / "data_pipeline" / "output" / "players.jsonl"
DEFAULT_TRANSFERS_PATH = Path(__file__).resolve().parent.parent / "data_pipeline" / "output" / "transfers.jsonl"

# Hapoel Beer Sheva related keywords for detecting incoming/outgoing transfers
HBS_KEYWORDS = ("hapoel beer sheva", "beer sheva", "h. beer sheva", "hapoel be'er sheva")


CARGO_TABLES = {
    "Template:Cargo/Player": {
        "table": "players",
        "fields": {
            "tmk_id": "String",
            "name_english": "String",
            "name_hebrew": "String",
            "birth_date": "Date",
            "birth_place": "String",
            "nationality": "List (,) of String",
            "main_position": "String",
            "current_squad": "Boolean",
            "current_jersey_number": "Integer",
            "homegrown": "Boolean",
            "retired": "Boolean",
        },
    },
    "Template:Cargo/Transfer": {
        "table": "transfers",
        "fields": {
            "player_id": "String",
            "season": "String",
            "transfer_date": "String",
            "from_club": "String",
            "to_club": "String",
            "fee": "String",
            "loan": "Boolean",
        },
    },
    "Template:Cargo/MarketValue": {
        "table": "market_values",
        "fields": {
            "player_id": "String",
            "value_date": "String",
            "value": "String",
            "team": "String",
        },
    },
    "Template:Cargo/Match": {
        "table": "matches",
        "fields": {
            "competition": "String",
            "matchday": "String",
            "match_date": "String",
            "match_time": "String",
            "venue": "String",
            "opponent": "String",
            "result": "String",
            "system_of_play": "String",
            "attendance": "String",
        },
    },
}


def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _render_template(template_name: str, **kwargs) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**kwargs)


def _load_jsonl(path: Path) -> list:
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((mwclient.errors.APIError, ConnectionError)),
    reraise=True,
)
def _edit_page(site: mwclient.Site, title: str, content: str, summary: str) -> bool:
    page = site.pages[title]
    if page.exists:
        existing = page.text()
        if _content_hash(existing.strip()) == _content_hash(content.strip()):
            logger.debug("Page '%s' is unchanged, skipping", title)
            return False
    page.save(content, summary=summary)
    logger.info("Saved page: %s", title)
    return True


def _build_cargo_template(table_name: str, fields: dict) -> str:
    """Build Cargo table declaration wikitext."""
    lines = ["<noinclude>", f"This template defines the Cargo table '''{ table_name }'''.", ""]
    lines.append("{{#cargo_declare:")
    lines.append(f"_table={table_name}")
    for field_name, field_type in fields.items():
        lines.append(f"|{field_name}={field_type}")
    lines.append("}}")
    lines.append("</noinclude>")
    lines.append("<includeonly>")
    lines.append("{{#cargo_store:")
    lines.append(f"_table={table_name}")
    for field_name in fields:
        lines.append(f"|{field_name}={{{{{{{field_name}|}}}}}}")
    lines.append("}}")
    lines.append("</includeonly>")
    return "\n".join(lines)


def import_cargo_templates(
    site: Optional[mwclient.Site] = None,
    dry_run: bool = False,
) -> dict:
    summary = {"created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []}

    for title, config in CARGO_TABLES.items():
        try:
            content = _build_cargo_template(config["table"], config["fields"])

            if dry_run:
                logger.info("[DRY RUN] Would create/update Cargo template: %s (%d chars)", title, len(content))
                summary["created"] += 1
                continue

            if site is None:
                raise RuntimeError("site is required when dry_run=False")

            page = site.pages[title]
            if page.exists:
                existing = page.text()
                if _content_hash(existing.strip()) == _content_hash(content.strip()):
                    summary["skipped"] += 1
                    continue
                _edit_page(site, title, content, summary=f"Updated Cargo table template: {title}")
                summary["updated"] += 1
            else:
                _edit_page(site, title, content, summary=f"Created Cargo table template: {title}")
                summary["created"] += 1

        except (mwclient.errors.APIError, ConnectionError, RuntimeError) as exc:
            logger.error("Failed to create Cargo template '%s': %s", title, exc)
            summary["failed"] += 1
            summary["errors"].append({"page": title, "error": str(exc)})

    logger.info(
        "Cargo template import: %d created, %d updated, %d skipped, %d failed",
        summary["created"], summary["updated"], summary["skipped"], summary["failed"],
    )
    return summary


def import_squad_page(
    site: Optional[mwclient.Site] = None,
    season: str = "2024",
    players_path: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    resolved_players = players_path or DEFAULT_PLAYERS_PATH
    players = _load_jsonl(resolved_players)

    content = _render_template("squad_table.j2", season=season, players=players)
    title = f"Squad {season}"

    summary = {"created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []}

    try:
        if dry_run:
            logger.info("[DRY RUN] Would create/update page: %s (%d chars)", title, len(content))
            summary["created"] += 1
            return summary

        if site is None:
            raise RuntimeError("site is required when dry_run=False")

        page = site.pages[title]
        if page.exists:
            existing = page.text()
            if _content_hash(existing.strip()) == _content_hash(content.strip()):
                summary["skipped"] += 1
                return summary
            _edit_page(site, title, content, summary=f"Updated squad page for season {season}")
            summary["updated"] += 1
        else:
            _edit_page(site, title, content, summary=f"Created squad page for season {season}")
            summary["created"] += 1

    except (mwclient.errors.APIError, ConnectionError, RuntimeError) as exc:
        logger.error("Failed to create squad page: %s", exc)
        summary["failed"] += 1
        summary["errors"].append({"page": title, "error": str(exc)})

    return summary


def import_transfer_page(
    site: Optional[mwclient.Site] = None,
    season: str = "2024",
    players_path: Optional[Path] = None,
    transfers_path: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    resolved_players = players_path or DEFAULT_PLAYERS_PATH
    resolved_transfers = transfers_path or DEFAULT_TRANSFERS_PATH

    players = _load_jsonl(resolved_players)
    transfers = _load_jsonl(resolved_transfers)

    name_map = {p["id"]: p["name_english"] for p in players}

    season_transfers = [t for t in transfers if t.get("season", "").startswith(season[:4])]

    incoming = []
    outgoing = []
    for t in season_transfers:
        t["player_name"] = name_map.get(t.get("player_id"), t.get("player_id", "Unknown"))
        to_club = (t.get("to_club") or "").lower()
        from_club = (t.get("from_club") or "").lower()

        if any(kw in to_club for kw in HBS_KEYWORDS):
            incoming.append(t)
        elif any(kw in from_club for kw in HBS_KEYWORDS):
            outgoing.append(t)

    content = _render_template(
        "transfer_table.j2",
        season=season,
        incoming=incoming,
        outgoing=outgoing,
    )
    title = f"Transfers {season}"

    summary = {"created": 0, "updated": 0, "skipped": 0, "failed": 0, "errors": []}

    try:
        if dry_run:
            logger.info("[DRY RUN] Would create/update page: %s (%d chars)", title, len(content))
            summary["created"] += 1
            return summary

        if site is None:
            raise RuntimeError("site is required when dry_run=False")

        page = site.pages[title]
        if page.exists:
            existing = page.text()
            if _content_hash(existing.strip()) == _content_hash(content.strip()):
                summary["skipped"] += 1
                return summary
            _edit_page(site, title, content, summary=f"Updated transfer page for season {season}")
            summary["updated"] += 1
        else:
            _edit_page(site, title, content, summary=f"Created transfer page for season {season}")
            summary["created"] += 1

    except (mwclient.errors.APIError, ConnectionError, RuntimeError) as exc:
        logger.error("Failed to create transfer page: %s", exc)
        summary["failed"] += 1
        summary["errors"].append({"page": title, "error": str(exc)})

    return summary
