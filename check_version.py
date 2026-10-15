"""Update release.json only when the US Google Play listing reports a newer version.

If the third-party Google Play reader fails, reports a nonnumeric version, or
returns a version not newer than release.json, the feed is left unchanged.
"""

import json
import re
from pathlib import Path

from google_play_scraper import app

GAME_PACKAGE = 'com.MadOut.BIG'
FEED = Path('release.json')
VERSION_PATTERN = re.compile(r'^[0-9]+(?:\.[0-9]+){1,3}$')


def parse_version(value):
    if not isinstance(value, str) or not VERSION_PATTERN.fullmatch(value.strip()):
        raise ValueError(f'Unsupported version value: {value!r}')
    return tuple(int(part) for part in value.strip().split('.'))


def main():
    existing = json.loads(FEED.read_text(encoding='utf-8'))
    old = existing.get('version')
    old_parts = parse_version(old)

    # Source is the Google Play listing, NOT random mod APK download websites.
    try:
        listing = app(GAME_PACKAGE, lang='en', country='us')
    except Exception as exc:
        print(f'Google Play reader unavailable; leaving the feed unchanged: {exc}')
        return
    found_package = listing.get('appId')
    if found_package and found_package != GAME_PACKAGE:
        raise ValueError(f'Unexpected package: {found_package}')

    latest = listing.get('version')
    print(f'GitHub feed version: {old}')
    print(f'Google Play reader version: {latest!r}')
    try:
        new_parts = parse_version(latest)
    except ValueError as exc:
        print(f'Cannot trust this version response; leaving the feed unchanged: {exc}')
        return

    # Pad missing components: 21.20 and 21.20.0 mean the same version.
    width = max(len(new_parts), len(old_parts))
    new_normalized = new_parts + (0,) * (width - len(new_parts))
    old_normalized = old_parts + (0,) * (width - len(old_parts))

    # Never downgrade the feed or commit when nothing has changed.
    if new_normalized <= old_normalized:
        print('No newer valid version. Leaving release.json unchanged.')
        return

    existing['version'] = latest.strip()
    # A version detection is NOT an AI source-code or compatibility review.
    existing['reviewStatus'] = 'not-reviewed'
    FEED.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Newer version detected: {old} -> {latest}. Updated release.json.')


if __name__ == '__main__':
    main()
