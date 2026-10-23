"""Run the actual manual capture under LuaJIT with getter-only native doubles."""
import copy
import json
import sys
from pathlib import Path
from build import HERE, ROOT, read, sha
from analyze import assess
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime


def main(revision):
    out = HERE / "build" / revision
    manifest, data = read(out / "build.json"), read(out / "data.json")
    source = (out / "init.lua").read_text(encoding="utf-8")
    for p, h in manifest["source_pins"].items(): assert sha(ROOT / p) == h, p
    for p, h in manifest["files"].items(): assert sha(out / p) == h, p
    for token in ["SetFact", "ChangeEntryState", "registerForEvent", "Override(", "AutoSave", "LoadSave", "os.execute", "io.popen", "GiveItem", "RemoveItem", "GetItemsForSale", "GetStock(", "FillVendorInventory", "GetVendorObject("]:
        assert token not in source, token
    assert "ItemID.CreateQuery" in source and "ItemID.FromTDBID" not in source
    reports, cases = [], 0

    def run(config=None, custom_data=None, calls=1, action=None):
        nonlocal cases
        cases += 1
        lua = LuaRuntime(unpack_returned_tuples=True)
        def to_py(v):
            if hasattr(v, "items"):
                m = dict(v.items())
                if m and set(m) == set(range(1, len(m)+1)): return [to_py(m[i]) for i in range(1, len(m)+1)]
                return {k: to_py(x) for k,x in m.items()}
            return v
        def encode(v):
            r = to_py(v); reports.append(r); return json.dumps(r)
        lua.globals().pyDecode = lambda t: lua.table_from(json.loads(t), recursive=True)
        lua.globals().pyEncode = encode
        lua.globals().catalogueText = json.dumps(custom_data or data)
        lua.globals().config = lua.table_from(config or {}, recursive=True)
        lua.execute(r'''
          files={['data.json']=catalogueText}; reads=0; writes=0; callbacks=0
          gameJournalEntryState={}; for _,n in ipairs({'Inactive','Active','Succeeded','Failed'}) do gameJournalEntryState[n]={name=n} end
          json={decode=pyDecode,encode=pyEncode}; os={date=function() return '20261017T000000Z' end}
          io={open=function(name,mode)
            if mode=='r' then if config.noData and name=='data.json' then return nil end; if not files[name] then return nil end; return {read=function()return files[name]end,close=function()return true end} end
            assert(mode=='w' and name:match('^capture_s26_[A-Za-z0-9_]+%.json$')); assert(not files[name],'overwrite')
            if config.writeFail then return nil end
            writes=writes+1
            return {write=function(_,t)files[name]=t;return not config.shortWrite end,close=function()return not config.closeFail end}
          end}
          local function deny(_,n) error('Unapproved API '..tostring(n)) end
          identityReads=0
          local player={GetEntityID=function()
            identityReads=identityReads+1
            if config.noHash then return {} end
            return {hash=config.changingHash and identityReads or 'player1'}
          end}
          local q={GetFactStr=function(_,name)
            if config.factError then error('fact failure') end
            if config.badFact then return nil end
            if config.factNaN then return 0/0 end
            return (config.facts and config.facts[name]) or 0
          end}
          local jm={
            HasAnyDelayedStateChanges=function()return config.pending or false end,
            GetEntryByString=function(_,path,class)
              if config.lookupError then error('lookup failure') end
              if config.missing==path then return nil end
              return {path=path,class=class,HasCounter=function()if config.counterError then error('counter error')end;return config.counter or false end}
            end,
            GetEntryState=function(_,e)
              reads=reads+1
              if config.unknown then return {} end
              if config.changing and reads>config.changing then return gameJournalEntryState.Active end
              return gameJournalEntryState[(config.states and config.states[e.path]) or 'Inactive']
            end,
            IsEntryVisited=function()if config.metadataError then error('metadata error')end;return false end,
            IsEntryTracked=function()return false end,
            GetIsObjectiveOptional=function()return false end,
            GetObjectiveCurrentCounter=function()return 3 end,
            GetObjectiveTotalCounter=function()return 7 end
          }
          local ts={GetItemQuantity=function(_,p,id) assert(p==player and id.query); if config.inventoryError then error('inventory unavailable')end; return config.itemQuantity or 0 end}
          setmetatable(jm,{__index=deny});setmetatable(q,{__index=deny});setmetatable(ts,{__index=deny});setmetatable(player,{__index=deny})
          ItemID={CreateQuery=function(id)return {query=true,id=id}end};TweakDBID={new=function(s)return s end}
          Game={GetPlayer=function()if config.noPlayer then return nil end;return player end,
            GetQuestsSystem=function()if config.noSystem then return nil end;return q end,
            GetJournalManager=function()if config.noJournal then return nil end;return jm end,
            GetTransactionSystem=function()if config.noInventory then return nil end;return ts end}
          setmetatable(Game,{__index=deny})
          hooks={};ObserveAfter=function(c,m,f)
            if config.observerError and callbacks==1 then error('registration denied')end
            callbacks=callbacks+1;hooks[c..'.'..m]=f
          end
        ''')
        start=len(reports); module=lua.execute(source)
        assert lua.globals().reads==lua.globals().writes==lua.globals().callbacks==0, 'load did work'
        if action: action(lua,module)
        answers=[module.Capture() for _ in range(calls)]
        return answers,reports[start:],lua

    answers, rs, lua = run()
    assert rs[0]["status"]=="STABLE_READ_ONLY_CAPTURE" and rs[0]["rootCounts"]["Inactive"]==58
    assert rs[0]["restartAuthorized"] is False and rs[0]["nativeWrites"]==rs[0]["saveWrites"]==0
    assert lua.globals().identityReads==4 and rs[0]['first']['player']['value']=='player1', 'fresh wrapper, same entity hash must stay stable'
    assert assess(rs[0])["next_bounded_candidate"]["route"].startswith("UNISSUED_OWNER_REVIEW")
    states={data["jobs"][0]["root"]:"Succeeded",data["jobs"][1]["root"]:"Active",data["jobs"][2]["root"]:"Failed"}
    _, rs, _=run({"states":states,"itemQuantity":1,"facts":{"PTFRS2_MQ032_Issued":1}})
    assert rs[0]["rootCounts"]=={"Inactive":55,"Active":1,"Succeeded":1,"Failed":1,"Unknown":0}
    assert rs[0]["first"]["items"][1]["quantity"]["value"]==1
    assert assess(rs[0])["next_bounded_candidate"]["route"].startswith("SAVED_MOD_OWNER_MIGRATION")
    for conf in [{"pending":True},{"changing":700}]:
        _,rs,_=run(conf); assert rs[0]["status"]=="UNSETTLED_DO_NOT_USE_FOR_ADMISSION"; assert assess(rs[0])["candidates"]==[]
    for conf in [{'changingHash':True},{'noHash':True}]:
        _,rs,_=run(conf);assert rs[0]['status']=='UNSETTLED_DO_NOT_USE_FOR_ADMISSION'
    for conf in [{"missing":data["jobs"][0]["root"]},{"unknown":True},{"lookupError":True}]:
        _,rs,_=run(conf); assert rs[0]["rootCounts"]["Unknown"]>0; assert assess(rs[0])["unknown"]
    for conf in [{"factError":True},{"badFact":True},{"factNaN":True}]:
        _,rs,_=run(conf); assert all(v["status"]=="Unknown" for v in rs[0]["first"]["jobs"][0]["facts"].values()); assert len(assess(rs[0])["unknown"])==58
    for conf in [{"inventoryError":True},{"noInventory":True},{"itemQuantity":-1},{"itemQuantity":0.5}]:
        _,rs,_=run(conf); assert all(i["quantity"]["status"]=="Unknown" for i in rs[0]["first"]["items"])
    _,rs,_=run({"counter":True,"metadataError":True})
    obj=next(j for j in rs[0]["first"]["jobs"][0]["journals"] if j["class"]=="gameJournalQuestObjective")
    assert obj["currentCounter"]["value"]==3 and obj["totalCounter"]["value"]==7 and obj["visited"]["status"]=="Unknown"
    _,rs,_=run({"counterError":True}); obj=next(j for j in rs[0]["first"]["jobs"][0]["journals"] if j["class"]=="gameJournalQuestObjective");assert obj["hasCounter"]["status"]=="Unknown"
    for conf in [{"noPlayer":True},{"noSystem":True},{"noJournal":True},{"noData":True},{"writeFail":True},{"shortWrite":True},{"closeFail":True}]:
        ans,_,_=run(conf); assert ans[0].startswith("S26 capture unavailable;")
    for mutation in ["count","duplicate","root","fact","owner","item","kind"]:
        d=copy.deepcopy(data)
        if mutation=="count":d["jobs"].pop()
        if mutation=="duplicate":d["jobs"][1]["id"]=d["jobs"][0]["id"]
        if mutation=="root":d["jobs"][0]["root"]="bad"
        if mutation=="fact":d["jobs"][0]["facts"].append("bad;fact")
        if mutation=="owner":d["jobs"][0]["owners"][0]["tag"]="bad"
        if mutation=="item":d["items"][0]["id"]="bad"
        if mutation=="kind":d["kind"]="OTHER"
        ans,rs,lua=run(custom_data=d); assert ans[0].startswith("S26 capture unavailable;") and lua.globals().writes==0
    ans,rs,lua=run(calls=3);assert len(set(ans))==lua.globals().writes==3
    sacrum=next(r for r in data["jobs"] if r["id"]=="mq032_sacrum")
    _,rs,_=run({"states":{sacrum["root"]:"Succeeded"},"facts":{"PTFRS2_MQ032_Issued":1}})
    assert assess(rs[0])["next_bounded_candidate"]["route"].startswith("PRESERVE")
    def armed(lua,module):
        assert module.ArmCassius().startswith('Cassius read-only probe armed')
        assert lua.globals().callbacks==3
        assert module.ArmCassius().startswith('Cassius read-only probe armed')
        assert lua.globals().callbacks==3, 'duplicate observers'
    _,rs,lua=run(action=armed)
    assert rs[0]['cassius']['armed'] is False and rs[0]['cassius']['registeredObservers']==3
    def registration_error(lua,module):
        assert module.ArmCassius().startswith('Refused: observer registration failed')
    _,rs,lua=run({'observerError':True},action=registration_error)
    assert rs[0]['cassius']['armed'] is False and rs[0]['cassius']['registeredObservers']==1
    def missing_observe(lua,module):
        lua.globals().ObserveAfter=None
        assert module.ArmCassius().startswith('Refused: ObserveAfter unavailable')
    _,rs,lua=run(action=missing_observe);assert rs[0]['cassius']['registeredObservers']==0
    result={"status":"PASS_LUAJIT_NOT_LIVE","cases":cases,"build_sha256":sha(out/"build.json"),"tester_sha256":sha(Path(__file__)),
            "jobs":58,"journals":manifest["journals"],"facts":manifest["facts"],"native_writes":0,"save_writes":0,"automatic_callbacks":0,
            "limits":"Getter-only doubles; actual native metadata/item binding and gameplay remain live pending; no restart authorized."}
    target=out/"tests.json";assert not target.exists();target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":main(sys.argv[1])
