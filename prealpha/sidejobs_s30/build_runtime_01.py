"""Append S30 admission to the existing consolidated S29 script file."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'prealpha/full_consolidation_v1/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
text=src.read_text(encoding='utf-8')
assert text.count('module PTFR.SideJobsS29')==1
start=text.index('public struct SideJobSampleS29 {')
end=text.index('public abstract class SideJobDataS29 {')
system=text[start:end].replace('SideJobsS29','SideJobsS30').replace('SideJobSampleS29','SideJobSampleS30').replace('SideJobTickS29','SideJobTickS30').replace('SideJobDataS29','SideJobDataS30')
system=system.replace('PTFR.SideJobsS30.SideJobsS30','PTFR.SideJobsS29.SideJobsS30')
a=system.index('  // The S25 fresh owner starts')
b=system.index('  private func Common()',a)
system=system[:a]+system[b:]
system=system.replace('    this.AdoptS25DelamainPhone();\n','')
a=system.index('  private func FreshOwner(i: Int32) -> Bool {')
b=system.index('  private func Ready(i: Int32)',a)
system=system[:a]+'''  private func FreshOwner(i: Int32) -> Bool {
    // These three IDs were outside HS1's original selected snapshot. The
    // complete journal/fact/vehicle beginning is checked on two settled ticks.
    return this.Own(i, "Ready") == 1 && this.Own(i, "Revision") == 1 && this.Own(i, "Issued") == 0 &&
      this.Own(i, "Entered") == 0 && this.Own(i, "Finished") == 0 && this.Own(i, "Fault") == 0;
  }
'''+system[b:]
system=system.replace('Side jobs S29: nativeEntries=','Side jobs S30: nativeEntries=').replace('No S29 entry for ','No S30 entry for ').replace('Side job S29 ','Side job S30 ')
generator=ROOT/'prealpha/sidejobs_s28/runtime/generate_03.py'
spec=importlib.util.spec_from_file_location('gen',generator);gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
rows=json.loads((ROOT/'prealpha/sidejobs_s30/prepared_01/contracts.json').read_text(encoding='utf-8'))['jobs']
data=gen.data_source(rows).replace('SideJobDataS28','SideJobDataS30')
out=ROOT/'prealpha/sidejobs_s30/serialized_01/PTFR_SideJobsS29.reds'
out.write_text(text+'\n// Three earned native entries added in S30; Motorbreath remains held.\n'+system+data,encoding='utf-8')
assert out.read_text(encoding='utf-8').startswith(text)
print('runtime',len(rows),'entries',out.stat().st_size,'bytes')
