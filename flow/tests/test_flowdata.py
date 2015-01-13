import numpy as np
import pytest
from flow.flow import *

def test_set_data():
    xs = np.arange(9)
    ys = np.arange(5)

    x, y = np.meshgrid(xs, ys, indexing='ij')
    u = np.sin(x)**2
    v = -np.cos(3*y)

    flow = FlowData({'X': x, 'Y': y, 'U': u, 'V': v})

    # Check property getters
    assert (np.array_equal(flow.X, x.ravel()))
    assert (np.array_equal(flow.Y, y.ravel()))
    assert (np.array_equal(flow.U, u.ravel()))
    assert (np.array_equal(flow.V, v.ravel()))

    # Check data structure
    assert (np.array_equal(flow.data['X'], flow.X))
    assert (np.array_equal(flow.data['Y'], flow.Y))
    assert (np.array_equal(flow.data['U'], flow.U))
    assert (np.array_equal(flow.data['V'], flow.V))

    # Check the set properties
    assert (set(flow.properties) == set(['X', 'Y', 'U', 'V']))

def test_set_as_list():
    X = np.arange(5).tolist()

    flow = FlowData({'f0': X})
    assert (type(flow.get_data('f0')) == np.ndarray)
    assert (np.array_equal(X, flow.data['f0']))
    assert (set(flow.properties) == set(['f0']))

def test_set_empty():
    X = np.arange(0)
    flow = FlowData({'X': X})

def test_oddlists_error():
    X = np.arange(5)
    Y = np.arange(10)

    with pytest.raises(ValueError) as excinfo:
        flow = FlowData({'X': X, 'Y': Y})
    assert ("added array_like objects not all of equal size" in str(excinfo.value))

def test_infer_homogenous_dtype():
    types = ('float32', 'float64', 'int')
    for dtype in types:
        X = np.arange(5, dtype=dtype)
        flow = FlowData({'X': X})

        assert (np.array_equal(flow.X, X))
        assert (flow.X.dtype == dtype)

def test_infer_heterogenous_dtype():
    X = np.arange(5, dtype='int')
    Y = np.arange(5, dtype='float32')

    flow = FlowData({'X': X, 'Y': Y})
    assert (flow.X.dtype == 'int')
    assert (flow.Y.dtype == 'float32')
    assert (np.array_equal(flow.X, X))
    assert (np.array_equal(flow.Y, Y))

def test_set_simple_dtype():
    X = np.arange(5, dtype='int')
    Y = np.arange(5, dtype='float64')
    flow = FlowData({'X': X, 'Y': Y}, dtype='float32')

    assert (flow.X.dtype == 'float32')
    assert (flow.Y.dtype == 'float32')
    assert (np.array_equal(flow.X, X))
    assert (np.array_equal(flow.Y, Y))

def test_set_complex_dtype():
    X = np.arange(5)
    Y = np.arange(5)
    dtype = [('X', 'float32'), ('Y', 'int32')]

    flow = FlowData({'X': X, 'Y': Y}, dtype=dtype)

    assert (flow.X.dtype == 'float32')
    assert (flow.Y.dtype == 'int32')
    assert (np.array_equal(flow.X, X))
    assert (np.array_equal(flow.Y, Y))
