"""Run current beta validation."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("test_release_020_cleanup_02.py")),run_name="__main__")
