"""Bind both stock Heavy Hearts block providers without changing the staged payloads."""

from pathlib import Path

from prepare import AUDIT, HERE, checked, read, sha, write
from verify_changes import PACK_PLAN as ORIGINAL, VERIFY

PACK_PLAN = HERE / 'pack_inputs_02.json'
BLOCK = r'base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock'


def main():
    assert not PACK_PLAN.exists()
    plan = read(ORIGINAL)
    assert plan['verification_sha256'] == sha(VERIFY)
    capture = checked(AUDIT / 'encounter_audit/capture_01/providers.json',
                      'D2196CCF63FCC7545696AFE4B9073A7613A2F8B2FDCAD669FB8C2964C79BA34F')
    stock = {r['archive']: r['sha256'] for r in read(capture)['providers']
             if r['depot'] == BLOCK and r['tag'] == 'hh_native_block'}
    assert {Path(p).name for p in stock} == {'basegame_3_nightcity.archive', 'ep1_1_nightcity.archive'}
    provider, = (r for r in plan['providers'] if r['depot'] == BLOCK)
    assert provider['archives'] == {p: h for p, h in stock.items() if Path(p).name == 'ep1_1_nightcity.archive'}
    provider['archives'] = stock
    plan.update(original_pack_plan_sha256=sha(ORIGINAL), provider_capture_sha256=sha(capture))
    write(PACK_PLAN, plan)


if __name__ == '__main__':
    main()
