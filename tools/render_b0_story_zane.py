"""Generate Zane's startup-only runtime from the validated Claire precedent."""
from audit_b0_story_zane import ROOT

def main():
    template = (ROOT/'redscript/PTFR_B0_Claire/ClaireDriver.reds').read_text()
    text = template.replace('B0Claire', 'B0StoryZane').replace('Claire', 'Zane').replace('PTFRB0CLA_', 'PTFRB0ZAN_').replace('claire_default_on', 'cct_dtn_cloth_01_default_on')
    needle = 'q.GetFact(n"PTFRB0ZAN_Ready") == 1'
    assert text.count(needle) == 1
    text = text.replace(needle, 'q.GetFact(n"PTFRB0ZAN_QuestOwns") == 0 && '+needle)
    out = ROOT/'redscript/PTFR_B0_StoryZane/ZaneDriver.reds'
    out.parent.mkdir(exist_ok=True)
    out.write_text(text)
    print('Rendered startup-only Zane driver; native handover remains authoritative')

if __name__ == '__main__': main()
