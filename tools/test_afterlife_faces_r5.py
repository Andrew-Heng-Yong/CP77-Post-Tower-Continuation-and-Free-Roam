"""Source, policy-model and real redscript compilation checks; not live proof."""
import hashlib
import json
import random
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'
OUT=BASE/'faces_r5'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SRC=ROOT/'redscript/PTFR_Afterlife_Faces_R5'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()

class Model:
    def __init__(self, options, seed):
        self.options=options; self.rng=random.Random(seed); self.rows={}; self.memory={}; self.calls=0
    def key(self,role,name):
        return next((o['face'] for o in self.options if o['role']==role and o['name']==name),0)
    def busy(self,key,entity):
        return any(e!=entity and (r['face']==key or (not r['confirmed'] and r['original']==key)) for e,r in self.rows.items())
    def admit(self,entity,role,current):
        if entity in self.rows: return self.rows[entity]['name']
        preferred=self.memory.get((entity,role), current)
        face=self.key(role,preferred)
        if not face or self.busy(face,entity):
            face=self.key(role,current); preferred=current
        if not face or self.busy(face,entity):
            faces=sorted({o['face'] for o in self.options if o['role']==role and not self.busy(o['face'],entity)})
            if not faces: return None
            face=self.rng.choice(faces)
            preferred=self.rng.choice([o['name'] for o in self.options if o['role']==role and o['face']==face])
        self.rows[entity]={'role':role,'face':face,'original':self.key(role,current),'name':preferred,'confirmed':preferred==current}
        self.memory[(entity,role)]=preferred
        self.calls+=preferred!=current
        return preferred
    def ack(self,entity): self.rows[entity]['confirmed']=True
    def detach(self,entity): del self.rows[entity]
    def invariant(self):
        faces=[r['face'] for r in self.rows.values()]
        assert len(faces)==len(set(faces))

def main():
    catalog=read(OUT/'catalog.json'); options=catalog['options']; roles=catalog['roles']
    assert [r['quantity'] for r in roles]==[17,22,7,4]
    assert catalog['native_community_id']=='16642022925330812742'
    ownership={}
    for option in options:
        assert option['name'] in roles[option['role']]['known_names']
        assert option['head_skin_components'] and option['face']>0
        assert ownership.setdefault(option['face_key'],option['role'])==option['role']
    for role in roles: assert len(role['eligible_faces'])>=role['quantity']
    assert sha(SRC/'FaceCatalogR5.reds')==catalog['catalog_sha256']
    for p,h in catalog['source_hashes'].items(): assert sha(ROOT/p)==h,p
    counts=defaultdict(int)
    # Arbitrary callback order with everyone initially wearing the same role skin.
    for seed in range(500):
        m=Model(options,seed); actors=[(f'{r["role"]}:{i}',r['role']) for r in roles for i in range(r['quantity'])]
        m.rng.shuffle(actors)
        initial={r['role']:next(o['name'] for o in options if o['role']==r['role']) for r in roles}
        for entity,role in actors:
            assert m.admit(entity,role,initial[role]) is not None
            m.invariant(); counts['admissions']+=1
        # Duplicate callbacks must not allocate or dispatch a second time.
        old_calls=m.calls
        for entity,role in actors: m.admit(entity,role,initial[role]); counts['duplicate_callbacks']+=1
        assert m.calls==old_calls
        for entity,role in actors: m.ack(entity)
        saved=dict(m.memory); choices={e:r['name'] for e,r in m.rows.items()}
        # Missing lookup samples do not touch reservations.
        before=dict(m.rows)
        for _ in range(5): m.invariant()
        assert m.rows==before; counts['empty_lookup_preserved']+=1
        # Reload, shuffled arrival order, with the same source IDs.
        m=Model(options,seed+9999); m.memory=saved; m.rng.shuffle(actors)
        for entity,role in actors:
            assert m.admit(entity,role,initial[role])==choices[entity]
            m.ack(entity); m.invariant(); counts['reload_admissions']+=1
        # Confirmed detach, replacement ID, eventual reattachment retains uniqueness.
        entity,role=actors[0]; m.detach(entity)
        assert m.admit(entity+'replacement',role,initial[role]) is not None
        m.ack(entity+'replacement'); m.invariant()
        m.detach(entity+'replacement')
        assert m.admit(entity,role,initial[role]) is not None
        m.ack(entity); m.invariant(); counts['stream_replacement_cycles']+=1
    # Same-face aliases cannot be admitted as two different faces.
    twins=[o for o in options if o['name'].endswith('merc_solo__lvl1_08_1') or o['name'].endswith('merc_solo__lvl1_08_2')]
    assert len(twins)==2 and twins[0]['face']==twins[1]['face']
    m=Model(options,5); m.admit('a',2,twins[0]['name']); m.ack('a'); m.admit('b',2,twins[1]['name']); m.invariant()
    counts['same_face_alias_negative']=1
    # Exhaustion is a non-mutating failure; no duplicate, role substitution or cull.
    m=Model(options,8)
    for i in range(len(roles[2]['eligible_faces'])):
        assert m.admit(str(i),2,'unknown') is not None; m.ack(str(i))
    before=dict(m.rows); assert m.admit('overflow',2,'unknown') is None; assert m.rows==before
    counts['pool_exhaustion_negative']=1

    # Asynchronous engine acknowledgement: old and new faces coexist until ack.
    # A busy pool waits rather than borrowing a face held by an in-flight change.
    for seed in range(200):
        m=Model(options,seed+20000)
        actors=[(f'{r["role"]}:{i}',r['role']) for r in roles for i in range(r['quantity'])]
        m.rng.shuffle(actors)
        current={e:m.rng.choice([o['name'] for o in options if o['role']==role]) for e,role in actors}
        due={}; waiting=dict(actors)
        for tick in range(30):
            for entity in list(due):
                if due[entity]<=tick: m.ack(entity); del due[entity]
            for entity,role in list(waiting.items()):
                if m.admit(entity,role,current[entity]) is not None:
                    del waiting[entity]; due[entity]=tick+4
                m.invariant()
            if not waiting and not due: break
        assert not waiting and not due
        counts['delayed_ack_full_population_trials']+=1
    # Old-face reservation cannot be reused before acknowledgement.
    m=Model(options,3)
    first,second=[o for o in options if o['role']==2][:2]
    assert first['face']!=second['face']
    m.memory[('a',2)]=second['name']; m.admit('a',2,first['name'])
    assert m.busy(first['face'],'b') and m.busy(second['face'],'b')
    m.ack('a'); assert not m.busy(first['face'],'b') and m.busy(second['face'],'b')
    counts['old_face_release_after_ack']=1

    text=(SRC/'AfterlifeFacesR5.reds').read_text()
    forbidden=['SetFact','SetFlat','Teleport','SendCommand','CancelCommand','ChangeEntryState','ActivateCommunity','CreateEntity(','GetEntityList']
    assert not any(t in text for t in forbidden)
    assert text.count('npc.ScheduleAppearanceChange(choice)')==1
    assert text.index('row.requested = true;') < text.index('npc.ScheduleAppearanceChange(choice)')
    for token in ['GetConstAccessToPSObject','GetSpawnerID()','16642022925330812742ul','GetOwnerCommunityEntryName()',
                  'GetFact(FaceCatalogR5.Owned(row.role))','scenes.IsEntityInScene','NPCPuppet.IsInCombat',
                  'row.confirmed','row.age >= 30','row.attachedSeen && !row.actor.IsAttached()',
                  'if row.requested','!FaceCatalogR5.Known','this.system.QueueRequest','system.QueueRequest',
                  'private persistent let memory','OnRestored','return result;','wrappedMethod()']:
        assert token in text,token
    guards={k:int(v) for k,v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)',text)}
    baseline=dict(read(BASE/'idles_r3/manifest.json')['guards'])
    baseline.pop('PTFRAL3_Suspended',None); baseline['PTFRAL5_Suspended']=0
    assert guards==baseline,(guards,baseline)
    def allowed(values): return all(values.get(k,0)==v for k,v in guards.items())
    assert allowed(guards)
    negative_guards=0
    for key, expected in guards.items():
        for wrong in (-1,0,1,2,3):
            if wrong==expected: continue
            mutated=dict(guards); mutated[key]=wrong
            assert not allowed(mutated); negative_guards+=1
    # Verify vanilla ownership getter precedent, rather than invented PS layout.
    vanilla=(ROOT/'research/finalboards_dismissal/decompiled/cyberpunk/NPC/NPCPuppet.script').read_text()
    for token in ['gameEntityStubComponentPS.GetPSComponentName()', 'entityStubPS.GetSpawnerID()', 'entityStubPS.GetOwnerCommunityEntryName()']:
        assert token in vanilla
    result=subprocess.run([str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'compile','-s',str(SRC),
                           '-b',str(GAME/'r6/cache/final.redscripts.modded'),'-o',str(OUT/'test.redscripts')],capture_output=True,text=True)
    output=result.stdout+result.stderr; (OUT/'compile.log').write_text(output)
    assert result.returncode==0 and not re.search(r'(^|\n)ERROR',output) and (OUT/'test.redscripts').is_file(),output
    protected={}
    for r in (BASE/'install_receipt.json', BASE/'population_r2/install_receipt.json',BASE/'idles_r3/install_receipt.json'):
        for p in read(r)['files']: protected[p['relative']]=p['sha256']
    for p,h in protected.items(): assert sha(GAME/p)==h,p
    report={'status':'PASS_R5_OFFLINE_NOT_INSTALLED_NOT_LIVE','policy_model_checks':dict(counts),
            'guard_contracts':len(guards),'negative_guard_cases_enumerated':negative_guards,
            'real_redscript_compilation':True,'compiled_sha256':sha(OUT/'test.redscripts'),
            'catalog_manifest_sha256':sha(OUT/'catalog.json'),
            'builder_sha256':sha(ROOT/'tools/build_afterlife_faces_r5.py'),'validator_sha256':sha(Path(__file__)),
            'files':[{'relative':'r6/scripts/PTFR_Afterlife_Faces_R5/'+p.name,'source':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(SRC.glob('*.reds'))],
            'installed_afterlife_files_unchanged':len(protected),'game_writes':0,
            'limitations':['Post-attachment correction, not a proven pre-render selector',
                           'Native render, initial-frame timing, PS availability and save reload require playtest',
                           'Four exact random community entries only; fixed booth routines/skins not changed',
                           'Source identities do not prove distinct rendered faces under other appearance mods']}
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
