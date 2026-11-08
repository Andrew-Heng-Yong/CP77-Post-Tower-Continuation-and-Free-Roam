from model import *
b=read('prealpha/phone_support_ph1/candidate_03/build_01.json')
for c in b['contracts']: print(c['contact'],type(c['source']['native_initializer_bindings']).__name__,c['init_node'],c['cleanup_phase'])
