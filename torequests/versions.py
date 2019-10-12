#! coding: utf-8
import platform
import sys

PY2 = (sys.version_info[0] == 2)
PY3 = (sys.version_info[0] == 3)
PY35_PLUS = sys.version_info[0] >= 3 and sys.version_info[1] >= 5

IS_WINDOWS = 'windows' in platform.platform().lower()
IS_LINUX = 'linux' in platform.platform().lower()
