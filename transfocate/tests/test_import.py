def test_import_automated_checkout():
    import transfocate.automated_checkout

    # NOTE: this is a no-op to mark the import as used
    assert transfocate.automated_checkout is not None
