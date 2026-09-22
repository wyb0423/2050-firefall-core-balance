#!/usr/bin/env python3
"""Generate and check sparse starting borders for selected Firefall survivors."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "common/history/states/zzzz_ffpa_sparse_survivor_borders.txt"
PROVINCE = re.compile(r"(?<![A-Za-z0-9_])x([0-9A-Fa-f]{6})(?![A-Za-z0-9_])")

CONFIG = {
    "STATE_ALASKA": {
        "target": "WAK",
        "receiver": "M32",
        "expected_count": 1028,
        "hubs": {"city": "D82BF2", "port": "F423DB", "wood": "17211C"},
        "keep": (
            "D82BF2", "2BABD1", "7CF944", "D43DAE", "F2C82C",
            "F423DB", "5C9007", "63A92C",
            "17211C", "1608A2", "829FA5", "83CBFA",
        ),
    },
    "STATE_YUKON_TERRITORY": {
        "target": "WAK",
        "receiver": "M32",
        "expected_count": 384,
        "hubs": {"city": "354974", "wood": "3A98AA"},
        "keep": (
            "354974", "07A351", "194BA1", "44D809", "518E76", "D97D42",
            "3A98AA", "0FBE18", "116717", "44F2F1", "8C71ED", "DD4100", "FF6D40",
        ),
    },
    "STATE_GREENLAND": {
        "target": "WGL",
        "receiver": "N12",
        "expected_count": 349,
        "hubs": {"city": "31F2A9", "port": "5B326C", "wood": "C13204"},
        "keep": (
            "31F2A9", "4D47A2", "AAE5ED", "18820A", "8EAFCB",
            "5B326C", "1BAB17", "82F13A",
            "C13204", "3C81BD", "B6A165", "8C64F5",
        ),
    },
    "STATE_ARAUCANIA": {
        "target": "WPT",
        "receiver": "K14",
        "expected_count": 114,
        "hubs": {"city": "D7C0DF", "port": "553B3F", "wood": "0D35DB"},
        "keep": (
            "D7C0DF", "397FCF", "9820A3", "D2FCCD", "029AC8",
            "553B3F", "EFB409", "592AB4",
            "0D35DB", "B2743E", "A86344",
        ),
    },
    "STATE_PATAGONIA": {
        "target": "WPT",
        "receiver": "K14",
        "expected_count": 241,
        "hubs": {"city": "8E85EB", "port": "B64102", "wood": "C9478C"},
        "keep": (
            "8E85EB", "94AA52", "8A9598", "12C24F", "D493AE",
            "B64102", "D882F4", "DDD3D2",
            "C9478C", "55453C", "5A1CFA", "1F55C5",
        ),
    },
    "STATE_ULIASTAI": {
        "target": "WMN",
        "receiver": "L00",
        "expected_count": 273,
        "hubs": {"city": "59D6A8", "wood": "0D2595"},
        "keep": (
            "59D6A8", "3CD081", "C3E251", "7AC27E", "54E6E1", "4C4F45",
            "0D2595", "00C508", "814B74", "F04D6E", "9F24AA", "8680E7", "8F4336",
        ),
    },
    "STATE_URGA": {
        "target": "WMN",
        "receiver": "L00",
        "expected_count": 261,
        "hubs": {"city": "441F74", "wood": "F35C78"},
        "keep": (
            "441F74", "42A076", "414B37", "DBDC22", "36C485", "A67C97",
            "F35C78", "412B0B", "9936EC", "233F02", "56D487", "32D33D", "6B2F41",
        ),
    },
}


def state_region_provinces(directory: Path, state: str, hubs: dict[str, str]) -> list[str]:
    anchor = re.compile(rf"^\s*{state}\s*=\s*\{{", re.MULTILINE)
    matches = []
    for path in sorted(directory.glob("*.txt")):
        text = path.read_text(encoding="utf-8-sig")
        match = anchor.search(text)
        if not match:
            continue
        provinces = re.search(
            r"\bprovinces\s*=\s*\{([^}]*)\}", text[match.end():], re.DOTALL
        )
        assert provinces, f"{state} has no provinces block in {path}"
        for hub, expected in hubs.items():
            actual = re.search(
                rf"^\s*{hub}\s*=\s*\"?x([0-9A-Fa-f]{{6}})\"?",
                text[match.end():],
                re.MULTILINE,
            )
            assert actual and actual.group(1).upper() == expected, (
                f"{state} {hub} hub changed"
            )
        matches.append(PROVINCE.findall(provinces.group(1)))
    assert len(matches) == 1, f"expected one {state} definition, found {len(matches)}"
    result = [province.upper() for province in matches[0]]
    assert len(result) == len(set(result)), f"duplicate province in {state}"
    return result


def source_owner_provinces(directory: Path, state: str, owner: str) -> set[str]:
    state_anchor = re.compile(rf"^\s*s:{state}\s*=\s*\{{", re.MULTILINE)
    next_state = re.compile(r"^\s*s:STATE_[A-Za-z0-9_-]+\s*=\s*\{", re.MULTILINE)
    matches = []
    for path in sorted(directory.glob("*.txt")):
        text = path.read_text(encoding="utf-8-sig")
        match = state_anchor.search(text)
        if not match:
            continue
        tail = text[match.end():]
        following = next_state.search(tail)
        state_block = tail[:following.start()] if following else tail
        owned = re.search(
            rf"\bcreate_state\s*=\s*\{{\s*country\s*=\s*c:{owner}\s*"
            r"owned_provinces\s*=\s*\{([^}]*)\}",
            state_block,
            re.DOTALL,
        )
        assert owned, f"{owner} no longer owns {state} in {path}"
        matches.append({province.upper() for province in PROVINCE.findall(owned.group(1))})
    assert len(matches) == 1, f"expected one history entry for {state}, found {len(matches)}"
    return matches[0]


def assert_country_type(country_definitions: str, tag: str, expected: str) -> None:
    block = re.search(
        rf"^{tag}\s*=\s*\{{.*?(?=^[A-Z0-9_-]+\s*=\s*\{{|\Z)",
        country_definitions,
        re.MULTILINE | re.DOTALL,
    )
    assert block and re.search(
        rf"\bcountry_type\s*=\s*{expected}\b", block.group(0)
    ), f"Firefall {tag} must remain {expected}"


def render_state(state: str, receiver: str, provinces: list[str]) -> list[str]:
    lines = [
        f"\ts:{state} = {{",
        "\t\tcreate_state = {",
        f"\t\t\tcountry = c:{receiver}",
        "\t\t\towned_provinces = {",
    ]
    for index in range(0, len(provinces), 12):
        lines.append("\t\t\t\t" + " ".join(f"x{x}" for x in provinces[index:index + 12]))
    lines.extend(("\t\t\t}", "\t\t}", "\t}"))
    return lines


def render(firefall_root: Path) -> str:
    metadata = json.loads(
        (firefall_root / ".metadata/metadata.json").read_text(encoding="utf-8-sig")
    )
    assert metadata["id"] == "alter_time_2050_fire_falls", "wrong Firefall root"

    country_definitions = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in sorted((firefall_root / "common/country_definitions").glob("*.txt"))
    )
    for target in {config["target"] for config in CONFIG.values()}:
        assert_country_type(country_definitions, target, "recognized")
    for receiver in {config["receiver"] for config in CONFIG.values()}:
        assert_country_type(country_definitions, receiver, "decentralized")

    state_regions = firefall_root / "map_data/state_regions"
    state_history = firefall_root / "common/history/states"
    remainders = {}
    all_seen = set()
    for state, config in CONFIG.items():
        provinces = state_region_provinces(state_regions, state, config["hubs"])
        assert len(provinces) == config["expected_count"], (
            f"{state} province count changed: {len(provinces)}"
        )
        source = source_owner_provinces(state_history, state, config["target"])
        assert source == set(provinces), f"{config['target']} no longer owns all of {state}"
        keep = config["keep"]
        assert len(keep) == len(set(keep)), f"duplicate retained province in {state}"
        assert set(config["hubs"].values()) <= set(keep), f"functional hub missing from {state}"
        assert set(keep) <= set(provinces), f"retained province missing from {state}"
        assert not all_seen.intersection(provinces), f"province shared by target states"
        all_seen.update(provinces)
        remainders[state] = [province for province in provinces if province not in keep]

    assert len(all_seen) == 2650
    assert sum(len(config["keep"]) for config in CONFIG.values()) == 86
    assert sum(map(len, remainders.values())) == 2564

    lines = [
        "# Generated by scripts/generate_sparse_survivor_borders.py.",
        "# Decentralized countries receive the wilderness; survivors keep functional hub clusters.",
        "STATES = {",
    ]
    for index, (state, config) in enumerate(CONFIG.items()):
        if index:
            lines.append("")
        lines.append(
            f"\t# {config['target']} keeps {len(config['keep'])} of "
            f"{config['expected_count']} provinces; {config['receiver']} receives the remainder."
        )
        lines.extend(render_state(state, config["receiver"], remainders[state]))
    lines.extend(("}", ""))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firefall_root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(args.firefall_root)

    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8-sig")
        assert actual.replace("\r\n", "\n") == expected, f"regenerate {OUTPUT}"
        print("Sparse survivor borders match Firefall: 86 of 2650 provinces retained")
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8", newline="\r\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
