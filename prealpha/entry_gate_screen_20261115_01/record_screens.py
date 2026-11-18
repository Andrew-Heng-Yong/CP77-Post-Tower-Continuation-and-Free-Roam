"""Preserve user-supplied console images and their bounded transcription."""
import hashlib
import json
import shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    output=HERE/'observations_01'
    if output.exists():
        raise RuntimeError('Fresh evidence required')
    images=[Path('C:/Users/Ayong/AppData/Local/Temp/codex-clipboard-4d6949a6-cb4d-4cee-8b00-ebf6635d2301.png'),
            Path('C:/Users/Ayong/AppData/Local/Temp/codex-clipboard-81e1d7a6-ec4b-41c4-a29e-1d8d6805388f.png')]
    entries=json.loads((HERE/'sources_01/inventory.json').read_bytes())['entries']
    output.mkdir()
    captures=[]
    for i,path in enumerate(images,1):
        dest=output/f'screen_{i:02}.png'
        before=sha(path)
        shutil.copyfile(path,dest)
        assert sha(dest)==sha(path)==before
        captures.append({'source':str(path),'copy':str(dest),'sha256':before})
    rows=[]
    for entry in entries:
        rows.append({'id':entry['id'],'title':entry['title'],'family':entry['family'],
                     'ready':1,'permit':1,'issued':1,'finished':0,'fault':0,
                     'currentMatch':True,'safe':True,
                     'screen_01_entered':None if entry['family']=='S28' else int(entry['id'] not in {'mq016_bartmoss','wst_ep1_09','sts_ep1_12_pickup'}),
                     'screen_02_entered':int(entry['id'] not in {'mq016_bartmoss','wst_ep1_09','sts_ep1_12_pickup'}),
                     'screen_02_journal':'Inactive (1)'})
    result={'status':'USER_SUPPLIED_LIVE_CONSOLE_SCREEN','captures':captures,
            'screen_01':{'checked':27,'listed':9,'tokensBlocked':False,'postTowerReady':True},
            'screen_02':{'facts':{'wst_ep1_09_active':0,'wst_ep1_02_active':0,'mq015_active':0}},
            'entries':rows,'limits':['Current-session screenshots are separate from the earlier MS32 saved snapshot.',
                'Issued/Entered, safe/currentMatch and fault=0 are diagnostic fields, not gameplay PASS.',
                'Only five indexed fresh-entry families were screened. Three user/policy exclusions remain outside this screen.',
                'No new game interaction, elapsed-time test, completion, payout or reload was established by these commands.']}
    (output/'observation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Preserved two exact screenshots; nine candidates transcribed; all journals Inactive.')

if __name__=='__main__':
    main()
