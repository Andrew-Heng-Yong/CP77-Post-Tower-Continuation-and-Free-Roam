from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
if __name__=='__main__':
 S=Store();S.load(r'base\quest\main_quests\prologue\q003\scenes\q003_07a_final_corp.scene');write(H/'finalcorp_inputs.json',S.pins);print(S.pins)
