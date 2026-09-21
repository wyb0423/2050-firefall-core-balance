#!/usr/bin/env python3
"""Source merge and formula checks, not an emulation of native AI decisions."""
import argparse
import itertools
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def parse(path):
    text = path.read_text(encoding='utf-8-sig')
    tokens = re.findall(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#"]+', text)
    result, stack = [], []
    current = result
    for token in tokens:
        if token.startswith('#'):
            continue
        if token == '{':
            child = []
            current.append(child)
            stack.append(current)
            current = child
        elif token == '}':
            assert stack, path
            current = stack.pop()
        else:
            current.append(token)
    assert not stack, path
    return result


def entries(block):
    i = 0
    while i < len(block):
        key, op = block[i:i+2]
        i += 2
        if op in ('>', '<', '!', '?') and block[i] == '=':
            op += '='
            i += 1
        yield key, op, block[i]
        i += 1


def mapping(block):
    return {key: value for key, op, value in entries(block) if op == '='}


def merged(roots):
    # Resolve same-relative-path shadowing before applying targeted top-level
    # replacements and whole-child-table INJECT operations used by this stack.
    files = {}
    for root in roots:
        for p in sorted((root / 'common/ai_strategies').glob('*.txt')):
            files[p.name] = p
    db = {}
    for name, p in sorted(files.items()):
        for key, op, value in entries(parse(p)):
            mode, sep, target = key.partition(':')
            if not sep:
                db[key] = mapping(value)
            elif mode == 'INJECT':
                assert target in db, (p, target)
                db[target].update(mapping(value))
            elif mode == 'REPLACE':
                assert target in db, (p, target)
                db[target] = mapping(value)
            else:
                raise AssertionError((p, key))
    return db


def condition(block, state):
    result = []
    for key, op, value in entries(block):
        if key in ('OR', 'AND'):
            children = [condition([k, o, v], state) for k, o, v in entries(value)]
            result.append(any(children) if key == 'OR' else all(children))
        elif key == 'ig:ig_industrialists':
            result.append(state['industrialists'])
        elif key == 'exists':
            assert value == 'ig:ig_industrialists'
            result.append(state['industrialists'])
        elif key in ('has_game_rule', 'has_strategy', 'has_law_or_variant'):
            result.append(value in state[key])
        elif key == 'is_ai':
            result.append(state[key] == value)
        else:
            assert op == '>=', (key, op)
            result.append(state[key] >= float(value))
    return all(result)


def calc(block, state):
    result, matched = 0, False
    for key, op, value in entries(block):
        if key == 'if':
            matched = condition(mapping(value)['limit'], state)
            if matched:
                result = calc(['value', '=', str(result)] + value[3:], state)
        elif key == 'else':
            if not matched:
                result = calc(['value', '=', str(result)] + value, state)
        else:
            assert op == '=', (key, op)
            v = calc(value, state) if isinstance(value, list) else state[value] if value in state else float(value)
            if key == 'value': result = v
            elif key == 'add': result += v
            elif key == 'subtract': result -= v
            elif key == 'multiply': result *= v
            elif key == 'divide': result /= v
            elif key == 'min': result = max(result, v)
            elif key == 'max': result = min(result, v)
            else: raise AssertionError(key)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'techres', 'firefall'):
        p.add_argument('--' + name + '-root', type=Path, required=True)
    args = p.parse_args()
    roots = [args.game_root, args.techres_root, args.firefall_root]
    before, after = merged(roots), merged(roots + [ROOT])
    targets = {'ai_strategy_resource_expansion': {'weight', 'building_group_weights'},
               'ai_strategy_industrial_expansion': {'weight', 'building_group_weights'},
               'ai_strategy_default': {'wanted_construction_output'}}
    own = mapping(parse(ROOT / 'common/ai_strategies/zzzz_ffpa_ai_development.txt'))
    for target, allowed in targets.items():
        assert set(mapping(own['INJECT:' + target])) == allowed
        for field in allowed:
            assert after[target][field] == mapping(own['INJECT:' + target])[field]
        if target != 'ai_strategy_default':
            assert {k: v for k, v in after[target].items() if k not in allowed} == {k: v for k, v in before[target].items() if k not in allowed}
    # Existing colonial and claim-reclamation injections must survive unchanged.
    for name in ('zzzz_ffpa_colonial_region_stances.txt', 'zzzz_ffpa_claim_reclamation_strategy.txt'):
        for key, _, value in entries(parse(ROOT / 'common/ai_strategies' / name)):
            for field, content in mapping(value).items():
                assert after[key.removeprefix('INJECT:')][field] == content
    for literacy, powerful in itertools.product((0, .1, .2, .4, .6, .8, 1), (False, True)):
        state = {'literacy_rate': literacy, 'industrialists': powerful}
        resource = calc(after['ai_strategy_resource_expansion']['weight'], state)
        industry = calc(after['ai_strategy_industrial_expansion']['weight'], state)
        assert 22.5 <= resource <= 37.5 and 30 <= industry <= 55.000001
        assert industry > resource > 0
    # Holding real economic inputs equal yields one target for every country.
    construction = after['ai_strategy_default']['wanted_construction_output']
    text = str(construction)
    assert all(x not in text for x in ('country_rank', 'country_definition', 'geographic_region', 'has_journal_entry', 'mandate_of_heaven'))
    for pool, population, income, traditional, expense, strategy in itertools.product((0, 2500, 3250, 7500, 15000), (100000, 2000000, 10000000), (0, 50000), (False, True), (0, .5, 1), (False, True)):
        state = dict(gdp=2000000, investment_pool_income=pool, total_population=population, fixed_income=income,
                     diplomatic_pact_expense_ratio=expense, has_game_rule=set(), is_ai='yes',
                     has_strategy={'ai_strategy_industrial_expansion'} if strategy else set(),
                     has_law_or_variant={'law_type:law_traditionalism'} if traditional else set())
        expected = 10 + max(0, (pool-2500)/750) + min(200, income/5000) + min(100, population/2000000)
        expected += 10 if population >= 2000000 else 0
        expected *= 1.25 if strategy else 1
        expected *= .5 if traditional else 1
        expected = max(2, expected*(1-expense))
        assert abs(calc(construction, state)-expected) < 1e-8
    supply = parse(ROOT / 'common/scripted_triggers/ffpa_ai_supply_triggers.txt')
    assert set(mapping(supply)) == {'kai_has_high_supply'}
    assert 'mg:$GOODS$' in str(supply) and 'market_goods_cheaper' in str(supply)
    defines = mapping(mapping(parse(ROOT / 'common/defines/zzzz_ffpa_ai_development_defines.txt'))['NAI'])
    base = mapping(mapping(parse(args.game_root / 'common/defines/00_ai.txt'))['NAI'])
    assert len(defines) == 4
    for key, value in defines.items():
        assert float(base[key]) < float(value) <= 1, key
    # No new timers, state interfaces, forced switching or production changes.
    assert not any(word in str(own) for word in ('set_variable', 'set_strategy', 'activate_production_method', 'every_country'))
    print('PASS: upstream child-table merge, preserved claim/colonial rules, 14 strategy and 360 construction scenarios; four native defines')


if __name__ == '__main__':
    main()
