"""Exercise the serialized admission gates and compare the staged English lip mappings."""
import json
from pathlib import Path
import sys
import prepare as m

sys.path.insert(0,str(m.ROOT.parent/"phone_support_ph1"))
import model


def fnv(path):
    h=14695981039346656037
    for byte in path.encode():
        h=(h^byte)*1099511628211 & 0xffffffffffffffff
    return str(h)


def main():
    c=m.read(m.WORK/"contract_02.json")
    cooked=m.WORK/"cook_02/readback"
    graph=model.model(cooked/(m.ENTRY+".json"))["root"]
    gate=graph["nodes"][65008]["condition"]["conditions"]
    admitted={v["factName"]:v["value"] for g in gate for v in m.walk(g) if v.get("$type")=="questVarComparison_ConditionType"}
    journal, = [v for g in gate for v in m.walk(g) if v.get("$type")=="questJournalEntryState_ConditionType"]
    assert journal["state"]=="Inactive" and journal["path"]["realPath"]==m.JOURNAL
    def passes(delta=None, state="Inactive"):
        facts=admitted | (delta or {})
        return state==journal["state"] and all(facts[n]==v for n,v in admitted.items())
    assert passes()
    for key in c["facts"]:
        assert not passes({key:1}), key
    for n in ("Active","Succeeded","Failed"):
        assert not passes(state=n)
    for k,v in ((m.TAG+"_Permit",0),(m.TAG+"_Issued",1),(m.TAG+"_Entered",1),(m.TAG+"_Finished",1),
                ("PostTowerFreeRoamActive",0),("q307_ep1_killed",0),("q307_main_game_killed",0),("q307_active",1)):
        assert not passes({k:v})
    def root(p): return m.read(p)["Data"]["RootChunk"]
    source=root(m.WORK/"lipmap_comparison/original.json");old=root(m.WORK/"lipmap_comparison/installed.json")
    new=root(cooked/r"towercontinued\sidejob_repair_sr1\en-us.lipmap.json")
    assert len(new["scenePaths"])==len(new["sceneEntries"])==len(old["scenePaths"])+3
    assert old=={k:(v[:len(old[k])] if k in ("scenePaths","sceneEntries") else v) for k,v in new.items()}
    rows=[]
    for scene in c["presentation"]:
        if fnv(scene) not in source["scenePaths"]:
            assert scene.endswith("mq061_12_kabuki_scene_haze_body.scene") and fnv(m.PREFIX+scene) not in new["scenePaths"]
            continue
        i=source["scenePaths"].index(fnv(scene));j=new["scenePaths"].index(fnv(m.PREFIX+scene))
        assert j>=len(old["scenePaths"]) and source["sceneEntries"][i]==new["sceneEntries"][j]
        rows.append(Path(scene).name)
    assert len(rows)==3
    result={"status":"PASS","closed_on_all_progress_facts":len(c["facts"]),"closed_journal_states":["Active","Succeeded","Failed"],
            "preserved_lip_mappings":len(old["scenePaths"]),"additional_matching_lip_mappings":rows,"mode":"serialization fixtures"}
    m.write(m.ROOT/"candidate_01/gate_and_lipmap_fixtures.json",result)
    print(json.dumps(result))


if __name__=="__main__":
    main()
