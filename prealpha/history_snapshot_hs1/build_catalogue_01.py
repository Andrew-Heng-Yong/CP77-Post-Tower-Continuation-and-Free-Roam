"""Read installed catalogues into a new immutable snapshot catalogue. No game writes."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent
W=H.parent.parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
OUT=H/'candidate_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def block(s,pattern):
 m=re.search(pattern,s);assert m,pattern
 start=m.end();level=1;quoted=False;escaped=False
 for i in range(start,len(s)):
  c=s[i]
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  else:
   level+=(c=='{')-(c=='}')
   if level==0:return s[start:i]
 raise AssertionError(pattern)
def body(s,name):return block(s,r'\bfunc\s+'+name+r'\([^)]*\)[^{]*\{')
def array_expr(s):
 m=re.search(r'(\[(?:\s*(?:"(?:[^"\\]|\\.)*"|-?\d+)\s*,?)*\])',s,re.S)
 assert m,s[:180]
 return json.loads(m.group(1))
def values(s,name,i=None):
 b=body(s,name)
 if i is not None:
  m=re.search(r'if\s+i\s*==\s*'+str(i)+r'\s*\{',b)
  if m:b=block(b,r'if\s+i\s*==\s*'+str(i)+r'\s*\{')
  elif re.search(r'if\s+i\s*==',b):
   if re.search(r'let empty:\s*array<\w+>;\s*return empty;\s*$',b):return []
   raise AssertionError((name,i))
 m=re.search(r'return\s+\w+\.(\w+)\(\);',b)
 if m:return values(s,m.group(1))
 if '[' in b:
  a=array_expr(b)
  return a[i] if i is not None and re.search(r'return\s+\w+\[i\]',b) else a
 m=re.search(r'return\s+("(?:[^"\\]|\\.)*");',b)
 if m:return json.loads(m.group(1))
 if re.search(r'let empty:\s*array<\w+>;\s*return empty;',b):return []
 raise AssertionError((name,i,b[:100]))
def q(v):return json.dumps(v,ensure_ascii=True,separators=(',',':'))
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8',newline='\n')

if __name__=='__main__':
 assert not OUT.exists(),'Use a successor directory'
 policy=W/'research/gig_restoration/lore_whitelists_v6_1_dependencies.json'
 selected=[x for x in json.loads(policy.read_text())['decision_registry'] if x['decision']=='INCLUDE']
 assert len(selected)==158
 rows={x['id']:{'id':x['id'],'title':x['title'],'category':x['category'],'root':x['journal_path'],
       'journals':[[x['journal_path'],'gameJournalQuest']],'facts':[],'u9':False,'u9_paths':[],'u9_facts':[],'u9_terminal':[], 'sources':[]} for x in selected}
 sources={str(policy):sha(policy)}
 specs=[('PTFR_PreAlpha/PTFR_NativeGigsU9/NativeGigDataU9.generated.reds','NativeGigDataU9','Facts'),
        ('TowerContinued_Gigs_U10/GigsU10.reds','GigDataU10','FactNames'),
        ('TowerContinued_SideJobs_S2/SideJobsS2.reds','SideJobFailureDataS21','FactNames')]
 specs += [(f'TowerContinued_SideJobs_S{n}/SideJobsS{n}.reds',f'SideJobDataS{n}','FactNames') for n in [22,23,24,25,27,28]]
 for rel,cls,facts in specs:
  p=G/'r6/scripts'/rel; sources[str(p)]=sha(p)
  s=block(p.read_text(encoding='utf-8-sig'),r'public abstract class '+cls+r'\s*\{')
  count=int(re.search(r'return (\d+);',body(s,'Count')).group(1))
  for i in range(count):
   ident=values(s,'IDs')[i] if re.search(r'func IDs\(',s) else values(s,'ID',i)
   if ident not in rows:continue
   row=rows[ident]
   paths=values(s,'DetailPaths' if cls=='SideJobFailureDataS21' else 'Paths',i)
   classes=values(s,'DetailClasses' if cls=='SideJobFailureDataS21' else 'Classes',i)
   fs=values(s,facts,i)
   assert len(paths)==len(classes),(cls,ident)
   row['sources'].append([rel,cls,i])
   for pair in zip(paths,classes):
    pair=list(pair)
    if pair not in row['journals']:row['journals'].append(pair)
   for name in fs:
    if name not in row['facts']:row['facts'].append(name)
   if cls=='NativeGigDataU9':
    assert row['root']==paths[0],ident
    row['u9']=True;row['u9_paths']=paths;row['u9_facts']=fs;row['u9_terminal']=values(s,'TerminalFacts',i)
    for name in row['u9_terminal']:
     if name not in row['facts']:row['facts'].append(name)
 # Keep the genuine prerequisite observation distinct from its accepted fallback.
 family=rows['sts_wbr_hil_06']
 family['journals'].append(['quests/main_quest/act_01/q103_warhead','gameJournalQuest'])
 for n in ['q103_done','q103_rogue_done']:
  if n not in family['facts']:family['facts'].append(n)
 rows=list(rows.values())
 assert sum(r['u9'] for r in rows)==72
 # JSON fragments in generated source can safely quote only validated identities.
 for row in rows:
  assert re.fullmatch(r'[A-Za-z0-9_]+',row['id'])
  for value in [v for j in row['journals'] for v in j]+row['facts']:
   assert '"' not in value and '\\' not in value and all(ord(c)>=32 for c in value),value
 fingerprint=hashlib.sha256(q(rows).encode()).hexdigest().upper()
 out=['module PTFR.HistorySnapshotHS1','public abstract class SnapshotDataHS1 {',
      f'  public static func Count() -> Int32 {{ return {len(rows)}; }}',
      f'  public static func Fingerprint() -> CName {{ return n"{fingerprint}"; }}']
 methods={'ID':lambda r:r['id'],'Root':lambda r:r['root'],
          'Paths':lambda r:[j[0] for j in r['journals']], 'Classes':lambda r:[j[1] for j in r['journals']],
          'Facts':lambda r:r['facts'],
          'U9StateIndices':lambda r:[r['journals'].index([p,'gameJournalQuest' if p==r['root'] else next(j[1] for j in r['journals'] if j[0]==p)]) for p in r['u9_paths']],
          'U9FactIndices':lambda r:[r['facts'].index(f) for f in r['u9_facts']+r['u9_terminal']],
          'MetadataJSON':lambda r:q({'id':r['id'],'title':r['title'],'journals':r['journals'],'fact_names':r['facts'],'coverage':'installed_catalogue' if r['sources'] else 'selected_root_only'})}
 for name,fn in methods.items():
  vals=[fn(r) for r in rows];typ='array<Int32>' if name.endswith('Indices') else ('array<String>' if isinstance(vals[0],list) else 'String')
  out.append(f'  public static func {name}(i: Int32) -> {typ} {{')
  for i,v in enumerate(vals):out.append(f'    if i == {i} {{ return SnapshotDataHS1.{name}{i}(); }}')
  out.append('    return '+('[]' if typ.startswith('array') else '""')+';\n  }')
  for i,v in enumerate(vals):out.append(f'  private static func {name}{i}() -> {typ} {{ return {q(v)}; }}')
 out+=['  public static func Index(id: String) -> Int32 { let i=0; while i<SnapshotDataHS1.Count() { if Equals(id,SnapshotDataHS1.ID(i)) { return i; }; i+=1; }; return -1; }','}']
 package=OUT/'package/r6/scripts/TowerContinued_HistorySnapshot_HS1'
 write(package/'SnapshotDataHS1.reds','\n'.join(out)+'\n')
 write(OUT/'catalogue.json',json.dumps({'schema':1,'fingerprint':fingerprint,'rows':rows,'source_pins':sources},indent=2)+'\n')
 print(json.dumps({'rows':len(rows),'u9':72,'root_only':sum(not r['sources'] for r in rows),'journals':sum(len(r['journals']) for r in rows),'facts':sum(len(r['facts']) for r in rows),'fingerprint':fingerprint}))
