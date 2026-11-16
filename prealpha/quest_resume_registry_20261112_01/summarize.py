"""Publish the bounded registry and explicit follow-up queue in the task folder."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import sqlite3
from prepare import HERE,ROOT,read,sha,write

def main():
    index=HERE/'registry_02';routes=HERE/'routes_02';out=HERE/'report_01'
    assert not out.exists();out.mkdir()
    summary=read(index/'summary.json');records=read(index/'registry.json')['records'];route=read(routes/'summary.json')
    verify=read(index/'verification.json');corpus=read(index/'corpus_verification.json')
    assert verify['status']=='PASS_BOUNDED_STRUCTURAL_CHECKS' and corpus['status']=='PASS_STRUCTURAL_AGREEMENT'
    db=sqlite3.connect((index/'registry.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    rd=sqlite3.connect((routes/'routes.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);rd.row_factory=sqlite3.Row
    providers={r['rid']:dict(r) for r in db.execute('SELECT rid,depot,role,sha256,status FROM resources')}
    roots={r['ordinal']:dict(r) for r in rd.execute('SELECT * FROM roots')}
    boundary_review=[]
    for b in route['boundaries']:
        result={**b,'classification':'SOURCE_INTERFACE_REVIEW_REQUIRED'}
        if b['kind']=='INPUT_UNRESOLVED':
            rid=b['rid'];g=b['graph']
            result['provider']=providers[rid]
            if g=='scene' and b['entry']=='Prefetch':
                result['classification']='PREFETCH_CONTROL_INPUT_NOT_AN_AUTHORED_SCENE_ENTRY'
                result['limit']='The caller has a lifecycle control input; the trace does not simulate prefetch/acknowledgement semantics.'
            elif '/' in g and not g.startswith('embedded/'):
                parent,nid=g.rsplit('/',1)
                p=db.execute('SELECT parameters_json FROM nodes WHERE rid=? AND graph=? AND id=?',(rid,parent,int(nid))).fetchone()
                child=list(db.execute('SELECT type FROM nodes WHERE rid=? AND graph=?',(rid,g)))
                edges=db.execute('SELECT COUNT(*) FROM edges WHERE rid=? AND graph=?',(rid,g)).fetchone()[0]
                params=json.loads(p[0]) if p else {}
                external=params.get('phaseResource',{}).get('DepotPath',{}).get('$value','')
                result['inline_shape']={'nodes':len(child),'edges':edges,'types':sorted({r[0] for r in child}),'external_phase':external}
                if external and external.lower() not in ('0','none') and edges==0 and all(r[0] in ('questInputNodeDefinition','questOutputNodeDefinition') for r in child):
                    result['classification']='EMPTY_INLINE_SHELL_WITH_EXTERNAL_PHASE_REFERENCE'
                    result['limit']='Keep the external call and empty parsed shell distinct; serialized-presence and engine selection are not inferred from default JSON objects.'
        elif b['kind']=='CALL_PROVIDER_UNRESOLVED':
            rid=b['rid'];g=b['graph']+'/'+str(b['node'])
            child=db.execute('SELECT COUNT(*) FROM nodes WHERE rid=? AND graph=?',(rid,g)).fetchone()[0]
            result['provider']=providers[rid];result['inline_child_nodes']=child
            if child>2:
                result['classification']='INLINE_HELPER_BODY_PRESENT_STANDALONE_REFERENCE_ABSENT'
                result['limit']='A missing named external resource does not erase the connected inline helper. Native source provides the body; runtime precedence and ownership remain separate.'
            elif any(x['depot']==b['target'] for x in summary['provider_collisions']):
                result['classification']='DIFFERING_STOCK_PROVIDER_PAYLOADS'
        elif b['kind']=='DEFAULT_INPUT_AMBIGUOUS':
            result['classification']='ARCHIVEXL_DEFAULT_INPUT_SOURCE_LEAD'
            result['lead']='Local ArchiveXL QuestPhase Extension.cpp connects new phases through In1; binding this source to the installed DLL remains unqualified.'
        boundary_review.append(result)
    extra=[]
    for r in route['uncatalogued_connected_quest_roots']:
        rs=sorted({i for s in r['sites'] for i in s['root_ordinals']})
        depots=[roots[i]['depot'] for i in rs]
        family='PREREQUISITE_REFERENCE'
        if any('\\ncpd_scanners_n2\\' in p for p in depots):family='INSTALLED_NCPD_SCANNER_FAMILY'
        elif any('\\cyberpsycho_p1\\' in p for p in depots):family='INSTALLED_CYBERPSYCHO_FAMILY'
        elif r['classification']=='SCOPE_REVIEW_REQUIRED':family='OTHER_INSTALLED_WRITE_PATH_REVIEW'
        extra.append({**r,'family':family,'registered_owners':[{'ordinal':i,'depot':roots[i]['depot']} for i in rs],
                      'admission_change_authorized':False})
    selected=[r for r in records if r['selection']=='INCLUDE']
    by_routes={r['id']:r for r in route['quest_routes']}
    coverage=[]
    for r in records:
        coverage.append({'id':r['id'],'title':r['title'],'scope':r['selection'],'category':r['category'],
          'journal_root':r['journal_root'],'snapshot_index':r['snapshot_index'],
          'authored_phase_objective_paths':len(r['stages']),
          'native_resource_ids':r['native_journal_resources'],
          'registered_owner_candidates':by_routes[r['id']]['root_ordinals'],
          'condition_sites':r['feature_counts'].get('PREDICATE',0),'choice_sites':r['feature_counts'].get('CHOICE',0),
          'logical_join_sites':r['feature_counts'].get('LOGICAL_JOIN',0),'fanout_sites':r['feature_counts'].get('FANOUT',0),
          'reward_inventory_sites':r['feature_counts'].get('REWARD_OR_INVENTORY',0),
          'support_status':'SOURCE_BINDINGS_INDEXED; actual actor/prefab/lease lifecycle unqualified',
          'resume_contract_status':'NOT_YET_REVIEWED_OR_IMPLEMENTED'})
    write(out/'coverage.json',{'schema':1,'rows':coverage,'additional_installed_and_prerequisite_roots':extra,
      'limits':['Source paths are not combinations of live objective states.','A reward/item site is not proof of a once-only receipt.',
                'Conditional static reachability is not gameplay, admission or saved ownership proof.']})
    write(out/'boundary_review.json',{'rows':boundary_review,'counts':dict(Counter(r['classification'] for r in boundary_review)),
      'unresolved_provider_collisions':summary['provider_collisions'],
      'journal_decode':read(HERE/'evidence_03/journal_fallback.json')})
    lines=['# Restoration registry — source inventory','',
      '12 November 2026. Current baseline: QP2_QUEST_HISTORY_AUTOLOAD. This is a source inventory for the mid-progress resume feature.',
      '',f"The selected roster contains {len(selected)} jobs: 80 gigs and 80 side/minor jobs. Every selected job has native journal references, a connected journal site under a registered PTFR root, and indexed phase/objective references. The selected jobs have {sum(len(r['stages']) for r in selected)} distinct authored phase/objective paths. This count includes native, edited and definition-only paths; it is not a count of safe resume stages.",
      '', 'The registry separately retains all 15 SEPARATE_SCOPE activity/reward records and 52 EXCLUDE records. Additional connected journal roots are listed in coverage.json with their installed activity family or prerequisite role. No entry is admitted by this inventory.',
      '', '## Snapshot reconciliation','',
      'The installed 158-row snapshot lacks Love Rollercoaster, Shape of a Pony and Career Opportunities. It retains The Prophet’s Song as a historical row despite that quest’s exclusion from new admission. Retaining a history row is not itself an admission defect. Preserve existing indices and saved identities when designing the next schema.',
      '', '## Evidence and validation','',
      '- All 51 Core files and 26 required dependencies match the installed manifest. The source capture observed no archive size/timestamp changes.',
      '- 15,741 graph/journal providers were captured across installed archives. 7,121 exports were reused only after current payload and export hash matches; 8,617 were decoded. The remaining three provider records are explicit decode failures.',
      f"- {len(roots)} PTFR registrations were traced through caller-selected phase/scene inputs. All 160 selected jobs have a connected journal site in this structural MAY analysis. Conditions, return feasibility and concurrent timing are unsolved.",
      f"- The separate existing audit parser agrees on graph/node/edge structure for all {corpus['resources']} compared PTFR and selected-native providers. Edge multiplicity is preserved. Thirteen inventory/readback checks passed; ten graph fixtures and four caller-input fixtures passed.",
      '', '## Remaining step 1 work','',
      'The full semantic stage registry is still in progress. The source index now supports that review without recapturing the game:',
      '', '- Classify valid parallel-objective combinations, optional outcomes and earned stage-entry predicates per quest.',
      '- Bind each stage to its original owner hierarchy, the existing mod owner, required actor/support lifecycle and reward receipts. Current records retain exact source locations rather than asserting live ownership.',
      '- Review the remaining input/interface cases in boundary_review.json, including empty inline shells, scene prefetch inputs, a named reference with a connected inline helper, and differing native provider payloads.',
      '- Close base-journal definition coverage. Both locally available decoders fail on the current base cooked journal’s gameJournalQuestMapPin.mappinData. The older cached journal has different raw bytes and was rejected. EP1 journal definitions and base/EP1 graph references are indexed. The separate q303 concert scene failure is outside the approved post-Tower quest scope.',
      '', 'No game resources, scripts, saves, facts, admission gates or deployment were changed. No gameplay qualification is claimed.',
      '', '## Selected quest index','',
      '| Quest | Native ID | Phase/objective paths | Connected owner candidates | Snapshot index |',
      '| --- | --- | ---: | ---: | ---: |']
    for r in sorted((r for r in coverage if r['scope']=='INCLUDE'),key=lambda r:r['title'].lower()):
        lines.append(f"| {r['title']} | `{r['id']}` | {r['authored_phase_objective_paths']} | {len(r['registered_owner_candidates'])} | {r['snapshot_index'] if r['snapshot_index'] is not None else 'absent'} |")
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    pins={str(p.relative_to(HERE)):sha(p) for p in [index/'registry.sqlite3',index/'registry.json',index/'summary.json',index/'verification.json',index/'corpus_verification.json',routes/'routes.sqlite3',routes/'summary.json',out/'coverage.json',out/'boundary_review.json',out/'REPORT.md']}
    write(out/'manifest.json',{'files':pins,'tools':{p.name:sha(p) for p in HERE.glob('*.py')},
      'scope':'Read-only source inventory plus workspace analysis outputs'})
    checkpoint={'step':1,'status':'IN_PROGRESS_SEMANTIC_STAGE_REVIEW_REMAINS','registry':'registry_02','routes':'routes_02','report':'report_01/REPORT.md',
      'selected_jobs':160,'selected_authored_phase_objective_paths':sum(len(r['stages']) for r in selected),
      'all_selected_have_connected_source_journal_sites':True,'report_manifest_sha256':sha(out/'manifest.json'),
      'next':'Use indexed graph contexts to review stage combinations, owner/support dependencies and reward receipts. Keep boundary classifications and source limits explicit.'}
    write(HERE/'checkpoint.json',checkpoint)
    print(json.dumps({'selected':160,'stage_paths':checkpoint['selected_authored_phase_objective_paths'],
      'boundary_classes':dict(Counter(r['classification'] for r in boundary_review)),
      'additional_roots':dict(Counter(r['family'] for r in extra))},indent=2))

if __name__=='__main__':main()
