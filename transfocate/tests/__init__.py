__all__ = ['test_transfocate']

from . import test_transfocate

# Create a Transfocator with a few inserted lenses
transfocator = test_transfocate.transfocator()
test_transfocate.insert(transfocator.prefocus_mid)
test_transfocate.insert(transfocator.tfs_02)
