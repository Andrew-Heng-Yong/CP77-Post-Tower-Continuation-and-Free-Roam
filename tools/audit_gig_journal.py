"""Read-only game-resource research: join vanilla gig journal IDs to English titles.

Only generated research JSON is written. No game, save, build or runtime writes.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/gig_restoration'
JOURNAL = OUT / 'journal_sources/json/base/journal/cooked_journal.journal.json'
LOCALIZATION = ROOT / 'research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json'

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    journal, localization = read(JOURNAL), read(LOCALIZATION)
    assert journal['Header']['GameVersion'] == 2310
    entries = localization['Data']['RootChunk']['root']['Data']['entries']
    localized = {str(e['primaryKey']): e['femaleVariant'] for e in entries}
    rows = []
    def visit(wrapper, ancestry):
        value = wrapper.get('Data', wrapper)
        key = value.get('id', '')
        path = ancestry + ([key] if key else [])
        if value.get('$type') == 'gameJournalQuest' and key.startswith('sts_'):
            loc = value.get('title', {}).get('value', '')
            rows.append({'id':key, 'journal_path':'/'.join(path), 'title_key':loc,
                         'title':localized.get(loc.removeprefix('LocKey#')),
                         'type':value.get('type'), 'district':value.get('districtID')})
        for child in value.get('entries', []): visit(child, path)
    visit(journal['Data']['RootChunk']['entry'], [])
    assert rows and len({r['id'] for r in rows}) == len(rows)
    result = {'scope':'base cooked journal sts_ entries, not a live availability census or complete all-gig catalogue',
              'sources':{str(p.relative_to(ROOT)):sha(p) for p in (JOURNAL,LOCALIZATION)},
              'game_writes':0, 'save_writes':0, 'count':len(rows), 'quests':rows}
    (OUT/'journal_titles.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'count':len(rows),'candidates':[r for r in rows if r['title'] and
          any(x in r['title'] for x in ('Playing for Keeps','Many Ways','Lack of Empathy','Guinea Pigs','Serial Suicide','Dirty Biz'))]},indent=2))

if __name__ == '__main__': main()
