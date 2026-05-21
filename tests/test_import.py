def test_import_package() -> None:
    import bep_reliability_engine
    from bep_reliability_engine import constants

    assert bep_reliability_engine is not None
    assert constants.GRAVITY == 9.81
