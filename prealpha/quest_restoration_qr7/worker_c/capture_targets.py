"""Select only the four quests and startup ancestors needed by eight UNKNOWNs."""
from prepare import ROOT,HERE,read,write,sha

def main():
    out=HERE/'targets_01.json'
    assert not out.exists()
    baseline=read(HERE/'baseline_01/baseline.json')
    epoch=read(baseline['epoch'])
    sources=[ROOT/'prealpha'/p for p in (
        'quest_restoration_qr6/groups/B01/verification_01/source_pins.json',
        'quest_restoration_qr6/groups/B01/additional_exports_01/manifest.json',
        'quest_restoration_qr6/groups/B01/standalone_exports_01/manifest.json',
        'quest_restoration_qr6/groups/B02/verification_02/source_pins.json',
        'quest_restoration_qr5/groups/G06/verification_02/source_pins.json',
        'quest_restoration_qr5/groups/G18/raw_exports_01/manifest.json',
    )]
    targets={}
    for source in sources:
        for row in read(source):
            d=row.get('depot','')
            if not (any(x in d for x in ('mq060','mws_wat_08','sts_std_rcr_02','voodoo_boot','q304_slider_stash')) or d in (
                r'base\quest\cyberpunk2077.questphase', r'base\quest\bugfixing.questphase',
                r'base\quest\bugfixing\quest_bugfixing.questphase')): continue
            raw=row.get('raw',row.get('binary')); expected=row.get('raw_sha256',row.get('sha256'))
            if d in epoch['source_resources']:
                raw=str(__import__('pathlib').Path(epoch['candidate'])/'archive_source'/d.replace('\\','/'))
                expected=epoch['source_resources'][d]
            assert sha(raw)==expected,(d,raw)
            targets[d]={'depot':d,'raw':raw,'raw_sha256':expected,'source_manifest':str(source),
                'source_manifest_sha256':sha(source),'old_json':row.get('json'),'old_json_sha256':row.get('json_sha256')}
    # Every effective target is included, including companion maps/native copies.
    for row in baseline['source_pins']:
        d=row['depot']
        if d not in targets:
            targets[d]={'depot':d,'raw':row['path'],'raw_sha256':row['sha256'],
                'source_manifest':baseline['epoch'],'source_manifest_sha256':baseline['epoch_sha256']}
    write(out,{'epoch':baseline['epoch'],'epoch_sha256':baseline['epoch_sha256'],
        'targets':list(targets.values()),'prior_manifest_pins':[{'path':str(p),'sha256':sha(p)} for p in sources]})
    print({'targets':len(targets),'path':str(out)})

if __name__=='__main__':main()
