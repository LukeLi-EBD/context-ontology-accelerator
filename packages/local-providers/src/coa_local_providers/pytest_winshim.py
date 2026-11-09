"""import shim for the Windows ``resource`` module, as a pytest plugin.

Load it before collection so upstream modules import cleanly on Windows:

    python -m pytest ... -p coa_local_providers.pytest_winshim

The upstream test files are not modified.
"""

from coa_local_providers.win_compat import ensure_resource_module

ensure_resource_module()
