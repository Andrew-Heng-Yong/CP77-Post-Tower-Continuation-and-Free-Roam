"""Preserve the third user console result separately from the first two screens."""
import hashlib
import json
import shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    output=HERE/'observations_02'
    if output.exists():
        raise RuntimeError('Fresh evidence required')
    source=Path('C:/Users/Ayong/AppData/Local/Temp/codex-clipboard-f1af38d9-4296-4887-bdf0-fd5946f654e2.png')
    original=source.read_bytes()
    output.mkdir()
    copy=output/'screen_03.png'
    shutil.copyfile(source,copy)
    assert source.read_bytes()==copy.read_bytes()==original
    result={'status':'USER_SUPPLIED_LIVE_ELIGIBILITY_CHECK','source':str(source),'copy':str(copy),
            'sha256':hashlib.sha256(original).hexdigest().upper(),
            'facts':{'haunted_weapon_recipe_acquired':0,'haunted_deck_recipe_acquired':0,
                     'porsche_911_930_turbo_cabriolet_owned':0,'sts_ep1_07_all_agents_defeated':0},
            'journals':{'sts_ep1_07':'Inactive (1)','sts_ep1_12':'Failed (4)'},
            'limits':['Live getter evidence only; no new progression, elapsed-time or spawn test.',
                      'No save, fact, journal, owner, item or timer changes.']}
    (output/'observation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Preserved screen 03: four zero facts, Roads Inactive, Treating Symptoms Failed.')

if __name__=='__main__':
    main()
