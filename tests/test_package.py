from __future__ import annotations

import importlib.metadata

import ari_sxn_common as m


def test_version():
    assert importlib.metadata.version("ari_sxn_common") == m.__version__
