"""Read-only native source inspection for exceptional U9 gigs."""
import json
from catalog_gig_rollout_r2 import ROOT, read, sha, value, walk
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

def graphs(relative):
    r=SafeResource(read(ROOT/relative))
    return flatten(r,r.obj['Data']['RootChunk'])

class AuditResource(SafeResource):
    """Audit only: enumerate valid edges and separately record native null ends.

    Some stock graphs retain orphan socket connections; they are not rewritten.
    """
    def __init__(self,obj):
        super().__init__(obj);self.orphan_edges=[]
    def edges(self,g):
        nodes=self.nodes(g);owners={};result=set()
        for n in nodes.values():
            for h in n['sockets']:
                s=self.d(h);owners[id(s)]=(n['id'],value(s['name']))
        for n in nodes.values():
            for h in n['sockets']:
                s=self.d(h)
                for ch in s['connections']:
                    c=self.d(ch);src=self.d(c['source']);dest=self.d(c['destination'])
                    if id(src)!=id(s):continue
                    if id(src) not in owners or id(dest) not in owners:
                        self.orphan_edges.append(dict(source=owners.get(id(src)),destination_owner=owners.get(id(dest)),destination_is_null=dest is None));continue
                    result.add((*owners[id(src)],*owners[id(dest)]))
        return result

if __name__=='__main__':
    import sys
    if len(sys.argv)>1:
        path=sys.argv[1]
        wanted=sys.argv[2:]
        for g in graphs(path):
            if wanted and g['path'] not in wanted:continue
            print(g['path'])
            for n in g['nodes']:print(json.dumps(n))
            print('EDGES',json.dumps(g['edges']))
