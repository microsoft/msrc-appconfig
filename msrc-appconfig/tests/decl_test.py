import msrc.appconfig.decl  # type: ignore


def test_decls():
    assert len(msrc.appconfig.decl.get_installed_decl().values()) >= 1
    assert len(msrc.appconfig.decl.get_installed_decl().values()) >= 1
    assert msrc.appconfig.decl.get_installed_decl.cache_info().hits >= 1
    assert msrc.appconfig.decl.get_installed_decl.cache_info().misses == 1
