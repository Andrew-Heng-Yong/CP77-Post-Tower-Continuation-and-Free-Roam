from common import *
import collections,binascii

def provider_ambiguity(depot,providers,comparison_candidates):
 return {'depot':depot,'providers':providers,'comparison_candidates':comparison_candidates}
def registration_collisions(registrations,native_ids):
 ids=collections.defaultdict(list)
 for r in registrations:ids[binascii.crc_hqx((r['path']+':'+r['input_node']).encode(),65535)].append(r)
 return [{'id':i,'entries':rs,'native_collision':i in native_ids} for i,rs in ids.items() if len(rs)>1 or i in native_ids]
def unresolved(refs,available):return sorted(set(refs)-set(available))
def superseded(actual,corrected):return [{'depot':d,'expected':h,'actual':actual.get(d)} for d,h in corrected.items() if actual.get(d)!=h]
def studio_gaps(required,owned):return sorted(set(required)-set(owned))
def phone_contract(producers,readers,ack_writers,protocols=None):
 results=[]
 for fact,sites in sorted(producers.items()):
  ack='holo_'+re.sub(r'^(?:holo|audio)_','',fact).replace('_activate','_done')
  contract=(protocols or {}).get(fact);ack=contract['ack'] if contract else ack;required=protocols is None or bool(contract) or bool(readers.get(ack))
  results.append({'request':fact,'producers':sites,'listeners':readers.get(fact,[]),'expected_ack':ack,'ack_writers':ack_writers.get(ack,[]),'ack_waiters':readers.get(ack,[]),'native_protocol':contract,'ack_requirement':'PROVED' if required else 'UNKNOWN','missing_listener':not readers.get(fact),'missing_ack':required and not ack_writers.get(ack)})
 return results
def cleanup_gap(counter_facts,cleanup_read_facts):return sorted(set(counter_facts)-set(cleanup_read_facts))
