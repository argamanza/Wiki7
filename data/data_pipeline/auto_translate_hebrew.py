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
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent / "output" / "merged" / "mappings.he.yaml"

TRANSLATE_DELAY = 0.1
MAX_WORKERS = 5

_LATIN_TO_HEBREW = {
    "a": "א", "b": "ב", "c": "ק", "d": "ד", "e": "א", "f": "פ",
    "g": "ג", "h": "ה", "i": "י", "j": "ג'", "k": "ק", "l": "ל",
    "m": "מ", "n": "נ", "o": "ו", "p": "פ", "q": "ק", "r": "ר",
    "s": "ס", "t": "ט", "u": "ו", "v": "ו", "w": "ו", "x": "קס",
    "y": "י", "z": "ז",
}

_DIGRAPHS = {
    "sh": "ש", "ch": "צ'", "th": "ת", "tz": "צ", "zh": "ז'",
    "ph": "פ", "kh": "ח",
}


def _transliterate_to_hebrew(text: str) -> str:
    """Phonetic transliteration from Latin script to Hebrew characters.
    Used as fallback when Google Translate returns the input unchanged.
    """
    parts = []
    for word in text.split():
        hebrew_word = []
        i = 0
        lower = word.lower()
        while i < len(lower):
            if i + 1 < len(lower) and lower[i:i+2] in _DIGRAPHS:
                hebrew_word.append(_DIGRAPHS[lower[i:i+2]])
                i += 2
            elif lower[i] in _LATIN_TO_HEBREW:
                hebrew_word.append(_LATIN_TO_HEBREW[lower[i]])
                i += 1
            else:
                hebrew_word.append(word[i])
                i += 1
        parts.append("".join(hebrew_word))
    return " ".join(parts)


def _is_latin(text: str) -> bool:
    """Check whether text is predominantly Latin script."""
    latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 0x0250)
    alpha_chars = sum(1 for c in text if c.isalpha())
    return alpha_chars > 0 and latin_chars / alpha_chars > 0.5


def _translate_one(text: str, src: str = "en", dest: str = "iw") -> str:
    """Translate a single text to Hebrew. Falls back to transliteration."""
    from deep_translator import GoogleTranslator

    try:
        translator = GoogleTranslator(source=src, target=dest)
        translated = translator.translate(text)
        if not translated or translated == text:
            if _is_latin(text):
                translated = _transliterate_to_hebrew(text)
                logger.debug("  Transliterated: %s -> %s", text, translated)
            else:
                translated = text
        time.sleep(TRANSLATE_DELAY)
        return translated
    except Exception as exc:
        logger.warning("Translation failed for '%s': %s", text, exc)
        if _is_latin(text):
            return _transliterate_to_hebrew(text)
        return text


def _translate_batch(texts: list[str], src: str = "en", dest: str = "iw") -> list[str]:
    """Translate texts to Hebrew using concurrent Google Translate requests.

    Uses ThreadPoolExecutor for parallel translation (5 workers by default).
    Falls back to phonetic transliteration when Google returns the input unchanged.
    Uses 'iw' (legacy ISO 639 code) because deep-translator/Google requires it over 'he'.
    """
    if not texts:
        return []

    results = [""] * len(texts)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(_translate_one, text, src, dest): i
            for i, text in enumerate(texts)
        }
        done = 0
        total = len(texts)
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()
            done += 1
            if done % 50 == 0:
                logger.info("  Translated %d/%d...", done, total)
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

    summary = {"positions": 0, "nationalities": 0, "clubs": 0, "competitions": 0, "names": 0}

    for category in ("positions", "nationalities", "clubs", "competitions", "names"):
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

    if not dry_run:
        with open(resolved_path, "w", encoding="utf-8") as f:
            yaml.dump(mapping, f, allow_unicode=True, sort_keys=False)
        logger.info("Updated mapping saved to %s", resolved_path)

    logger.info(
        "Auto-translation summary: %d positions, %d nationalities, %d clubs, %d competitions, %d names",
        summary["positions"], summary["nationalities"], summary["clubs"],
        summary["competitions"], summary["names"],
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
