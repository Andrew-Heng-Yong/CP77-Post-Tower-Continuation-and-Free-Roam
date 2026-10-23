"""Reuse the tested safe startup and read-only logger, with a frozen site list."""
from plan_b0_special_services import ROOT,OUT,read
import json
def main():
    c=read(OUT/'cohort.json');sites=c['sites']
    source=(ROOT/'redscript/PTFR_B0_Claire/ClaireDriver.reds').read_text()
    source=source.replace('PTFR.B0Claire','PTFR.B0SpecialServices').replace('ClaireDriver','SpecialServiceDriver').replace('ClaireTick','SpecialServiceTick')
    start=source.index('  private func Eligible(');end=source.index('  private func Safe(',start)
    common=' &&\n      '.join(f'q.GetFact(n"{k}") == {v}' for k,v in c['common_guards'].items())
    methods='  private func Eligible(q: ref<QuestsSystem>) -> Bool {\n    return '+common+' && q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRB0SP_Suspended") == 0;\n  }\n'
    methods+='  private func Site(q: ref<QuestsSystem>, enabled: CName, ready: CName, active: CName, excluded: CName, gate: CName, extra: Bool, commit: Bool) -> Bool {\n    if !extra || q.GetFact(gate) <= 0 || q.GetFact(enabled) != 0 || q.GetFact(ready) != 1 || q.GetFact(active) != 0 || q.GetFact(excluded) != 0 { return false; }\n    if commit { q.SetFact(enabled, 1); }\n    return true;\n  }\n'
    methods+='  private func Sites(q: ref<QuestsSystem>, commit: Bool) -> Bool {\n    let pending = false;\n'
    for s in sites:
        p=s['prefix'];extra=' && '.join(f'q.GetFact(n"{x}") > 0' for x in s['extra_positive'])
        methods+=f'    pending = this.Site(q, n"{p}Enabled", n"{p}Ready", n"{p}OwnerActive", n"{p}Excluded", n"{s["gate"]}", {extra}, commit) || pending;\n'
    methods+='    return pending;\n  }\n'
    source=source[:start]+methods+source[end:]
    start=source.index('    if IsDefined(q) {',source.index('  public func Poll('));end=source.index('    this.Schedule(epoch);',start)
    source=source[:start]+'''    if IsDefined(q) && this.Eligible(q) && this.Sites(q, false) {
      let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
      if IsDefined(player) && this.Safe(player) { this.Sites(q, true); }
    }
'''+source[end:]
    source=source.replace('// Startup only. All local crossings, scene looping and eligibility are native.','// Five-second pending-enable check; safety queried once only if an eligible site needs enablement.\n// Native owners perform all approach, scene and departure work; no distance polling.')
    out=ROOT/'redscript/PTFR_B0_SpecialServices';out.mkdir(exist_ok=True)
    (out/'SpecialServiceDriver.reds').write_text(source)
    logger=(ROOT/'diagnostics/PTFR_B0_Claire/init.lua').read_text()
    names=list(c['common_guards'])+['PTFRBASE_Suspended','PTFRB0SP_Suspended']
    for s in sites:
        names += [s['gate']]+s['extra_positive']+[s['prefix']+v for v in ['Ready','Enabled','Excluded','OwnerActive','OwnerStarts','Entries','Exits','SceneRequests']]
        names += s['scene_audit']['facts']
    names=list(dict.fromkeys(names))
    start=logger.index('local names=');end=logger.index('\nlocal file',start)
    logger=logger[:start]+'local names='+json.dumps(names).replace('[','{',1)[:-1]+'}'+logger[end:]
    start=logger.index('function M.Observe(');end=logger.index('function M.Finish()',start)
    obs='local sites={\n'+',\n'.join('{key='+json.dumps(s['key'])+',label='+json.dumps(s['label'])+',prefix='+json.dumps(s['prefix'])+',gate='+json.dumps(s['gate'])+'}' for s in sites)+'\n}\n'
    obs+='''function M.Observe(label)
  local s=state();log('OBSERVE',s,label or 'manual')
  if not s.loaded then print('[PTFR SPECIAL] Player not loaded');return s end
  for _,site in ipairs(sites)do
    local f,p=s.facts,site.prefix
    print('[PTFR SPECIAL] '..site.label..' gate='..f[site.gate]..' E='..f[p..'Enabled']..' owner='..f[p..'OwnerActive']..' entries/exits/requests='..f[p..'Entries']..'/'..f[p..'Exits']..'/'..f[p..'SceneRequests'])
  end
  return s
end
'''
    logger=logger[:start]+obs+logger[end:]
    logger=logger.replace('Claire-v1','SpecialServices-v1').replace('PTFR CLAIRE','PTFR SPECIAL').replace('claire_service_','special_services_')
    out=ROOT/'diagnostics/PTFR_B0_SpecialServices';out.mkdir(exist_ok=True)
    (out/'init.lua').write_text(logger)
    print('Rendered startup-only enabling and automatic read-only diagnostics for',len(sites),'sites')
if __name__=='__main__':main()
