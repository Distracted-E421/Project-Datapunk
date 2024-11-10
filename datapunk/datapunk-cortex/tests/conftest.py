# datapunk/datapunk-cortex/tests/conftest.py
import pytest
import sys
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)