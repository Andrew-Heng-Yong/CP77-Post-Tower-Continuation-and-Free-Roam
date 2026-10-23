"""New cyberpsycho inventory using the read-only stock parent-slice analyzer."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'prealpha/ncpd_scanner_n1'))
import catalog as journal_catalog

spec = importlib.util.spec_from_file_location('scanner_slice_catalog', ROOT / 'prealpha/ncpd_scanners_n2/catalog.py')
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)
journal_catalog.VARIANTS = {'HuntForPsychoVariant'}
analyzer.OUT = ROOT / 'research/cyberpsycho_p1'

if __name__ == '__main__':
    analyzer.main(sys.argv[1])
