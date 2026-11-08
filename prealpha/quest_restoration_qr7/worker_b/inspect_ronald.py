from lib import *
if __name__=='__main__':
 O=H/'inspection_01';assert not O.exists();O.mkdir();rows=read(H/'readback_01/manifest.json');M={r['depot']:Resource(read(r['json'])).normalize()for r in rows if r['status']=='EXPORTED'};save(O/'models.json',M)
 out=[]
 for d,gps in [(RN,['root','root/11','root/12']),(BO,['root','root/5'])]:
  for gp in gps:
   if gp not in M[d]['graphs']:continue
   g=M[d]['graphs'][gp];out.append('\nRESOURCE '+d+' '+gp+' PF '+str(M[d]['root_prefabs'])+'\nEDGES '+str(g['edges']))
   for i,n in g['nodes'].items():out.append(i+' '+n['type']+' '+json.dumps(n['payload'],ensure_ascii=False))
 (O/'controllers.txt').write_text('\n'.join(out),encoding='utf-8')
 sc={}
 for d in [NS,BS]:
  g=M[d]['graphs']['scene'];sel=['920','839','1451','3863','1485','2974','2972','2978','3040','1750','1755'];sc[d]={'entries':g['entries'],'nodes':{i:g['nodes'][i]for i in sel if i in g['nodes']},'outgoing':{i:[e for e in g['edges']if e[0]==i]for i in sel if i in g['nodes']},'incoming':{i:[e for e in g['edges']if e[2]==i]for i in sel if i in g['nodes']}}
 save(O/'enrollment_choice.json',sc)
 print('Native news root/11',len(M[RN]['graphs']['root/11']['nodes']),'nodes; scoped inspection saved')
