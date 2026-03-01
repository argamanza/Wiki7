"""Auto-translate English values to Hebrew in the mapping YAML.

Runs after generate_mapping_stub.py creates the YAML with empty values,
and before the user manually reviews. Uses deep-translator (free Google Translate)
to pre-fill translations for positions, nationalities, clubs, and player names.

Usage:
    python -m data_pipeline.auto_translate_hebrew [--mapping-path PATH]

Workflow:
    1. generate_mapping_stub.py  ->  mappings.he.yaml (empty values)
    2. auto_translate_hebrew.py  ->  mappings.he.yaml (auto-filled values)
    3. User reviews & fixes bad translations
    4. apply_hebrew_mapping.py   ->  players.he.jsonl (final output)
"""

import logging
import time
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent / "output" / "merged" / "mappings.he.yaml"

# Delay between API calls to avoid rate limiting (seconds)
TRANSLATE_DELAY = 0.3


def _translate_batch(texts: list[str], src: str = "en", dest: str = "he") -> list[str]:
    """Translate a list of texts from English to Hebrew using Google Translate.

    Returns translations in the same order. On failure, returns original text.
    """
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source=src, target=dest)
    results = []
    for text in texts:
        try:
            translated = translator.translate(text)
            results.append(translated if translated else text)
            time.sleep(TRANSLATE_DELAY)
        except Exception as exc:
            logger.warning("Translation failed for '%s': %s", text, exc)
            results.append(text)
    return results


def auto_translate(mapping_path: Path | None = None, dry_run: bool = False) -> dict:
    """Auto-fill empty Hebrew values in the mapping YAML.

    Only fills entries where the Hebrew value is empty/None.
    Preserves any existing manual entries.

    Returns a summary dict with counts of translations per category.
    """
    resolved_path = mapping_path or DEFAULT_MAPPING_PATH

    if not resolved_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as f:
        mapping = yaml.safe_load(f) or {}

    summary = {"positions": 0, "nationalities": 0, "clubs": 0, "names": 0}

    for category in ("positions", "nationalities", "clubs", "names"):
        section = mapping.get(category, {})
        empty_keys = [k for k, v in section.items() if not v]

        if not empty_keys:
            logger.info("No empty entries in '%s', skipping", category)
            continue

        logger.info("Auto-translating %d entries in '%s'...", len(empty_keys), category)

        if dry_run:
            summary[category] = len(empty_keys)
            continue

        translations = _translate_batch(empty_keys)

        for key, translated in zip(empty_keys, translations):
            if translated and translated != key:
                section[key] = translated
                summary[category] += 1
                logger.debug("  %s -> %s", key, translated)
            else:
                logger.debug("  %s -> (no translation)", key)

    if not dry_run:
        with open(resolved_path, "w", encoding="utf-8") as f:
            yaml.dump(mapping, f, allow_unicode=True, sort_keys=False)
        logger.info("Updated mapping saved to %s", resolved_path)

    logger.info(
        "Auto-translation summary: %d positions, %d nationalities, %d clubs, %d names",
        summary["positions"], summary["nationalities"], summary["clubs"], summary["names"],
    )
    return summary


def main():
    """CLI entry point for auto-translation."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Auto-translate Hebrew mapping values")
    parser.add_argument(
        "--mapping-path", type=Path, default=None,
        help=f"Path to mappings.he.yaml (default: {DEFAULT_MAPPING_PATH})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    auto_translate(mapping_path=args.mapping_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
