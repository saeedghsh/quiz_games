"""Automatically found by pytest and adds the path to root.

With the entry points we execute with -m and things are OK.
But pytest fails at adding the root to python path, so we enforce it via this file.
"""

import os
import sys

project_root_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root_path)
