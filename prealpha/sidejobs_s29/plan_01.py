"""Source-bound entry recipes: normal ports, scoped branches and current native gates."""
from common import *
scope=read(ROOT/'research/sidejobs_s29/scope_01.json'); selected={x['id']:x for x in scope['targets']}
minor=r'base\quest\minor_quests\minorquests.questphase'
side=r'base\quest\side_quests\sidequests.questphase'
world=r'ep1\openworld\world_stories\ep1_world_stories.questphase'
jobs=[]
def add(ident,dep,entry='In1',parent=None,child=None,start=0,subset=None,start_node=None,start_socket=None,root_ids=None):
    ids=[ident] if ident!='sq023_hit_order' else ['sq023_hit_order','sq023_bd_passion','sq023_real_passion']
    job=dict(id=ident,journal_ids=ids,title=selected[ident]['title'],native=dep,input=entry,
             tag='PTFRS29_'+ident,subset=subset,start_node=start_node,start_socket=start_socket,
             parent=None)
    if parent:
        gs=graphset(parent);g=gs['root'];ns={n['id']:n for n in g['nodes']}
        edges=[e for e in g['edges'] if e[2]!=child or e[3]==entry]
        keep=(ancestors(edges,{child})&descendants(edges,start)) if root_ids is None else set(root_ids)|{start,child}
        assert child in keep and start in keep
        job['parent']=dict(depot=parent,graph='root',input_node=start,child=child,ids=sorted(keep-{start}),
                           edges=[e for e in edges if e[0] in keep and e[2] in keep and e[2]!=start])
    elif subset:
        g=graphset(dep)['root'];assert start_node in subset
        job['selected_edges']=[e for e in g['edges'] if e[0] in subset and e[2] in subset]
    resources,missing=closure([dep]);job['closure']=resources;job['missing']=missing
    jobs.append(job)

for ident,child,stem in [('mq016_bartmoss',5,'mq016_bartmoss'),('mq017_streetkid',22,'mq017_streetkid'),('mq018_writer',37,'mq018'),('mq028_stalker',41,'mq028'),('mq036_overload',33,'mq036_overload'),('mq040_biosculpt',49,'mq040_biosculpt'),('mq042_nomad',24,'mq042_nomad')]:
    prefix=ident[:5];add(ident,f'base\\quest\\minor_quests\\{prefix}\\{stem}.questphase',parent=minor,child=child)
add('sq023_hit_order',r'base\quest\side_quests\sq023\sq023.questphase',parent=side,child=59,start=67)
add('mq059_freedom',r'base\quest\minor_quests\mq059\mq059.questphase',parent=r'base\quest\minor_quests\mq059\mq059.quest',child=7)
add('mq060_nitro',r'base\quest\minor_quests\mq060\mq060.questphase',entry='Start',parent=r'base\quest\minor_quests\mq060\mq060.quest',child=4)
add('mq058_semimaru_crystalcoat',r'base\quest\minor_quests\mq058\mq058.questphase',entry='Start Quest')
# Native external vehicle/prerequisite admission for the new Eagles entry.
jobs[-1]['native_entry_condition']={'depot':r'base\quest\bugfixing\quest_bugfixing.questphase','graph':'root/3','node':100}

# Venus starts at the original invitation delay; the Pickup's money reward,
# Gilchrist branch, corpse conclusions and apartment/Nibbles content are not replayed.
dep=r'base\quest\main_quests\prologue\q003\phases\q003_stout.questphase';g=graphset(dep)['root']
keep=descendants(g['edges'],146)
add('q003_stout',dep,subset=sorted(keep),start_node=146,start_socket='In')

# Retain the native messages -> resurgence -> resolution chain after Epistrophy.
# The scan-return reward node124 is deliberately outside this branch.
dep=r'base\quest\side_quests\sq025\sq025.questphase';g=graphset(dep)['root'];keep=descendants(g['edges'],134)
assert 124 not in keep and 79 not in keep
add('sq025b_delamain_insurgence',dep,subset=sorted(keep),start_node=134,start_socket='In1')

# Corrosion's breadcrumb is independent of the equipped-Canto reactions owner.
add('q305_postcontent',r'ep1\quest\main_quests\q305\phases\q305_12_haunted_weapon.questphase',subset=[4,5,6,9],start_node=5,start_socket='In')
add('wst_ep1_09',r'ep1\openworld\world_stories\wst_ep1_09\wst_ep1_09.questphase',parent=world,child=9)
add('sts_ep1_12_pickup',r'ep1\openworld\world_stories\wst_ep1_02\wst_ep1_02.questphase',parent=world,child=2)
assert len(jobs)==16 and set(x for j in jobs for x in j['journal_ids'])==set(selected)
pins={}
for j in jobs:
    deps=set(j['closure'])|{j['native']}
    if j['parent']:deps.add(j['parent']['depot'])
    if j.get('native_entry_condition'):deps.add(j['native_entry_condition']['depot'])
    for d in deps:
        for k,h in [('raw','sha256'),('json','json_sha256')]:pins[INDEX[d][k]]=INDEX[d][h]
write('plan_01.json',dict(status='ENTRY_RECIPES_FOR_REVIEW_NOT_BUILT',jobs=jobs,source_pins=pins,
    limitations=['Native child graphs still require presentation/service and freshness review.',
                 'No live quest completion or save-resume claim.']))
print('Planned',len(jobs),'owners /',sum(len(j['journal_ids']) for j in jobs),'journals')
print('Missing',sorted(set(d for j in jobs for d in j['missing'])))
