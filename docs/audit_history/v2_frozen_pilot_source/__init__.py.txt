"""GraphVOI, Team Orbit. Only public observations enter policy inference."""
from pathlib import Path
import sys

# Vendored, pinned BSD-licensed blossom solver; no installation/network at runtime.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'vendor'))
