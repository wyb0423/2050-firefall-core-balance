#!/usr/bin/env python3
"""Check the state-war-goal Infamy overrides against an installed vanilla build."""

import sys
from pathlib import Path


def block(text: str, anchor: str) -> str:
    start = text.index(anchor)
    brace = text.index("{", start)
    depth = 0
    for index, character in enumerate(text[brace:], brace):
        depth += character == "{"
        depth -= character == "}"
        if depth == 0:
            return text[start : index + 1]
    raise AssertionError(f"unclosed block: {anchor}")


def normalized_infamy(text: str, scale_key=None):
    infamy = block(text, "infamy = {")
    if scale_key:
        scale_position = infamy.index(scale_key)
        scale_start = infamy.rfind("multiply = {", 0, scale_position)
        infamy = infamy.replace(block(infamy[scale_start:], "multiply = {"), "", 1)
    return [line.strip() for line in infamy.splitlines() if line.strip()]


def check(name: str, vanilla_path: Path, scale_key: str, factor: str, minimum: str) -> None:
    override_path = Path(__file__).parents[1] / "common/war_goal_types/ffpa_state_wargoal_infamy.txt"
    override = block(override_path.read_text(), f"INJECT:{name} = {{")
    vanilla = vanilla_path.read_text()

    assert normalized_infamy(override, scale_key) == normalized_infamy(vanilla), (
        f"{name}: formula differs from vanilla beyond the intended multiplier"
    )
    scale_position = override.index(scale_key)
    minimum_position = override.index('desc = "INFAMY_MINIMUM_VALUE"')
    assert scale_position < minimum_position, f"{name}: multiplier must precede the minimum"
    assert f"value = {factor}" in override[scale_position:minimum_position]
    assert f"value = {minimum}" in override[minimum_position:]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} VANILLA_CONQUER_STATE VANILLA_RETURN_STATE")
    check("conquer_state", Path(sys.argv[1]), "FFPA_CONQUER_STATE_INFAMY_SCALE", "0.85", "5")
    check("return_state", Path(sys.argv[2]), "FFPA_RETURN_STATE_INFAMY_SCALE", "0.70", "2")
    assert max(5 * 0.85, 5) == 5 and max(20 * 0.85, 5) == 17
    assert max(2 * 0.70, 2) == 2 and max(10 * 0.70, 2) == 7
    print("state war-goal Infamy overrides match vanilla plus the intended reductions")
