"""Render guarded batch enabling and read-only durable diagnostics."""
import json
from plan_b0_story_services import ROOT,OUT,read
def main():
    c=read(OUT/'cohort.json');sites=c['sites']
    s=(ROOT/'redscript/PTFR_B0_SpecialServices/SpecialServiceDriver.reds').read_text()
    s=s.replace('PTFR.B0SpecialServices','PTFR.B0StoryServices').replace('SpecialServiceDriver','StoryServiceDriver').replace('SpecialServiceTick','StoryServiceTick').replace('PTFRB0SP_Suspended','PTFRB0ST_Suspended')
    a=s.index('    return ',s.index('  private func Eligible('));b=s.index('\n  }',a)
    s=s[:a]+'    return '+' &&\n      '.join(f'q.GetFact(n"{k}") == {v}' for k,v in c['common_guards'].items())+' && q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRB0ST_Suspended") == 0;'+s[b:]
    a=s.index('    pending = this.Site(');b=s.index('    return pending;',a)
    lines=[]
    for site in sites:
        p=site['prefix'];lines.append(f'    pending = this.Site(q, n"{p}Enabled", n"{p}Ready", n"{p}OwnerActive", n"{p}Excluded", n"{site["gate"]}", true, commit) || pending;\n')
    s=s[:a]+''.join(lines)+s[b:]
    dest=ROOT/'redscript/PTFR_B0_StoryServices';dest.mkdir(exist_ok=True);(dest/'StoryServiceDriver.reds').write_text(s)
    lua=(ROOT/'diagnostics/PTFR_B0_StoryZane/init.lua').read_text()
    names=list(c['common_guards'])+['PTFRBASE_Suspended','PTFRB0ST_Suspended']
    for site in sites:
        names += [site['gate']]+[site['prefix']+x for x in ['Ready','Enabled','Excluded','OwnerActive','OwnerStarts','Entries','Exits','SceneRequests']]+site['scene_audit']['facts']
    a=lua.index('local names=');b=lua.index('local file,',a)
    lua=lua[:a]+'local names='+json.dumps(list(dict.fromkeys(names))).replace('[','{',1)[:-1]+'}\n'+lua[b:]
    lua=lua.replace('PTFR ZANE','PTFR STORY SERVICES').replace("'zane_'","'story_services_'")
    # Include position for correlating native entry/exit, not for gameplay driving.
    lua=lua.replace("local parts={'label='", "local pos=p:GetWorldPosition()\n local parts={'x='..pos.x,'y='..pos.y,'z='..pos.z,'label='")
    dest=ROOT/'diagnostics/PTFR_B0_StoryServices';dest.mkdir(exist_ok=True);(dest/'init.lua').write_text(lua)
    print('Rendered S3 driver and automatic TSV logger')
if __name__=='__main__':main()
