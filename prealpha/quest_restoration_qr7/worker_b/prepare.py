from lib import *
E=read(W/'prealpha/quest_restoration_qr6/source_epoch_00.json');C=Path(E['candidate']);I=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
if __name__=='__main__':
 p=H/'raw_inputs_01.json';assert not p.exists();pins=read(W/'prealpha/quest_restoration_qr6/blockers/ronald_01/source_pins.json');by={r['depot']:r for r in pins}
 for q in ['sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12']:
  d='towercontinued\\native_gigs_u9\\'+q+'_entry.questphase';r=I[d];by[d]={'depot':d,'raw':str(C/'archive_source'/Path(d.replace('\\','/'))),'raw_sha256':E['source_resources'][d],'json':r['json'],'json_sha256':sha(r['json'])}
 for r in by.values():
  if r['depot'].startswith('towercontinued'):r['raw']=str(C/'archive_source'/Path(r['depot'].replace('\\','/')));assert E['source_resources'][r['depot']]==r['raw_sha256']
  assert sha(r['raw'])==r['raw_sha256'];assert sha(r['json'])==r['json_sha256']
 save(p,list(by.values()));save(H/'baseline.json',{'epoch':str(W/'prealpha/quest_restoration_qr6/source_epoch_00.json'),'sha256':sha(W/'prealpha/quest_restoration_qr6/source_epoch_00.json'),'candidate':str(C),'inputs':len(by),'scope':'Read-only native/current input preparation; no shared production modification'})
 print('Prepared',len(by),'pinned resources')
