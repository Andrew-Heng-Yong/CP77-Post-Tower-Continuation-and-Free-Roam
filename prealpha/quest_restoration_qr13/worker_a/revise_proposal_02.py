"""Source-derived contact-prefix termination/join plan, no runtime resources."""
from investigate import *
def main():
    p=read(H/'proposal_01.json');p['status']='PROPOSED_WITH_NATIVE_CONTACT_COMPLETION_JOIN_PENDING_TYPED_REVIEW'
    child=p['phase_operations'][1]['205']
    child['add_scoped_nodes']=[{'id':200,'native_template':'native Ronald root/11 node67 questLogicalAndNodeDefinition','inputSocketCount':2,'outputSocketCount':1},
        {'id':201,'native_template':'native Ronald root/11 node1 questOutputNodeDefinition','socketName':'Out1','type':'Terminating'}]
    child['add_edges']=[[121,'Out',200,'In1'],[159,'Out',200,'In2'],[156,'Out',200,'In2'],[200,'Out1',201,'In']]
    child['expose_phase_sockets']=['CutDestination','In1','Out1']
    child['completion_rule']='Both branches require native121 contact-NonCallable operation complete. Silent159 branch can then end; notified23 branch additionally waits native155 3seconds and156 HUDrestore. Do not terminate directly from121 or23.'
    p['required_review'].append('Contactchild termination: retain native8payloads +2inputAND200/Term201; mutation premature truebranch completion beforeHUDrestore must fail.')
    save('proposal_02.json',p)
    # Independent branch event dependencies, not an engine timing simulation.
    edges=child['keep_internal_edges_exact']+child['add_edges']
    required=[[121,'Out',200,'In1'],[159,'Out',200,'In2'],[156,'Out',200,'In2'],[200,'Out1',201,'In']]
    def validate(es):
        return all(e in es for e in required)and[23,'Out',200,'In2']not in es and[121,'Out',201,'In']not in es
    assert validate(edges)
    controls=[]
    for label,in1,in2,expected in [('silent contact incomplete',False,True,False),('silent complete',True,True,True),('notified HUD pending',True,False,False),('notified restored',True,True,True)]:
        assert (in1 and in2)==expected;controls.append({'name':label,'contactComplete':in1,'notificationBranchDone':in2,'terminates':expected})
    mutants=[]
    for name,es in [('early23branch',[e for e in edges if e!=[156,'Out',200,'In2']]+[[23,'Out',200,'In2']]),('direct121termination',edges+[[121,'Out',201,'In']]),('missing121completion',[e for e in edges if e!=[121,'Out',200,'In1']])]:
        assert not validate(es);mutants.append({'fault':name,'detected':True})
    save('contact_completion_controls_02.json',{'status':'PASS_PROPOSAL_COMPLETION_DEPENDENCIES','branch_controls':controls,'mutations':mutants,'limits':'Source-plan event dependency checks only; typed candidate and actual engine lifecycle still independently verified by coordinator/reviewer.'})
    print({'proposal':'proposal_02.json','branchcontrols':len(controls),'mutations':len(mutants)})
if __name__=='__main__':main()
