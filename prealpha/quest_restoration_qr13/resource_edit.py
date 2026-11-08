"""Coordinator handle-aware additive JSON editing; no I/O or game APIs."""
import copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/parity_audit'))
from model import Resource
from common import value
class Edit:
 def __init__(self,doc):
  self.doc=doc;self.r=Resource(doc);assert not self.r.errors;self.next=max(map(int,self.r.handles),default=0)+1
 def h(self,data):
  r={'HandleId':str(self.next),'Data':data};self.next+=1;return r
 def graph(self,path):
  g=self.r.d(self.doc['Data']['RootChunk']['graph'])
  for part in path.split('/')[1:]:g=self.r.d(self.node(g,int(part))['phaseGraph'])
  return g
 def node(self,g,i):return next(self.r.d(n)for n in g['nodes']if self.r.d(n)['id']==i)
 def clone(self,x,source,skip=()):
  if isinstance(x,list):return [self.clone(v,source,skip)for v in x]
  if not isinstance(x,dict):return x
  if 'HandleId'in x or'HandleRefId'in x:
   d=source.d(x)
   return self.h(self.clone(d,source,skip))if d is not None else copy.deepcopy(x)
  return {k:self.clone(v,source,skip)for k,v in x.items()if k not in skip}
 def add(self,g,payload,sockets):
  n=copy.deepcopy(payload);n['sockets']=[self.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':name},'type':kind,'connections':[]})for name,kind in sockets]
  g['nodes'].append(self.h(n));return n
 def socket(self,n,name):
  for h in n['sockets']:
   s=h.get('Data')or self.r.d(h)
   if value(s['name'])==name:return h.get('HandleId',h.get('HandleRefId')),s
  raise KeyError((n['id'],name))
 def link(self,a,s,b,t):
  x,sd=self.socket(a,s);y,td=self.socket(b,t)
  c=self.h({'$type':'graphGraphConnectionDefinition','source':{'HandleRefId':x},'destination':{'HandleRefId':y}})
  sd['connections'].append(c);td['connections'].append({'HandleRefId':c['HandleId']})
 def fact(self,name,value=0,comparison='Equal'):
  return self.h({'$type':'questFactsDBCondition','type':self.h({'$type':'questVarComparison_ConditionType','comparisonType':comparison,'factName':name,'value':value})})
 def journal(self,path,cls,state):
  return self.h({'$type':'questJournalCondition','type':self.h({'$type':'questJournalEntryState_ConditionType','inverted':0,'path':self.h({'$type':'gameJournalPath','className':{'$type':'CName','$storage':'string','$value':cls},'editorPath':'','fileEntryIndex':1,'realPath':path}),'state':state})})
 def logic(self,operation,conditions):return self.h({'$type':'questLogicalCondition','operation':operation,'conditions':conditions})
 def ordered(self):
  r=Resource(self.doc);seen=set()
  def order(x):
   if isinstance(x,list):return [order(v)for v in x]
   if not isinstance(x,dict):return x
   if 'HandleId'in x or'HandleRefId'in x:
    k=r.hid(x)
    if k not in r.handles:return x
    if k in seen:return {'HandleRefId':k}
    seen.add(k);return {'HandleId':k,'Data':order(r.handles[k])}
   return {k:order(v)for k,v in x.items()}
  return order(self.doc)
STANDARD=[('CutDestination','CutDestination'),('In','Input'),('Out','Output')]
