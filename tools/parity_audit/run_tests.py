"""Record reproducible unit + real-corpus mutation results."""
from common import *
import unittest,sys,io
import test_auditor,corpus_tests
o=Path(sys.argv[1]);groups={};suite=unittest.TestSuite()
for name,module in [('literal',test_auditor),('corpus',corpus_tests)]:
 s=unittest.defaultTestLoader.loadTestsFromModule(module);groups[name]=s.countTestCases();suite.addTests(s)
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);log=stream.getvalue();(o/'mutation_tests.log').write_text(log,encoding='utf-8');print(log)
write(o/'mutation_suite.json',{'success':result.wasSuccessful(),'tests_run':result.testsRun,'groups':groups,'failures':[{'test':str(t),'detail':d} for t,d in result.failures],'errors':[{'test':str(t),'detail':d} for t,d in result.errors],'scope':'In-memory faults; independently specified graph edges/reachability, real native JSON, pinned historical hashes and collision values'})
raise SystemExit(0 if result.wasSuccessful() else 1)
