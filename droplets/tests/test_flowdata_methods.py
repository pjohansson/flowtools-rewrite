import numpy as np
import pytest

from droplets.flow import FlowData


def test_flowdata_set_lims():
    # Cut system data along x
    xlim = (2., 5.)

    x = np.arange(8)
    y = np.arange(6)

    xs, ys = np.meshgrid(x, y)
    cs = np.random.sample(xs.shape)

    # Get indices
    inds = (xs >= xlim[0]) & (xs <= xlim[1])

    info = {
        'bin_size': (1., 1.),
        'shape': (8, 6),
        'size': (
            (0., 7.),
            (0., 5.)
        ),
        'num_bins': xs.size
    }

    # Cut out values of X
    flow = FlowData(('X', xs.ravel()), ('Y', ys.ravel()), ('C', cs.ravel()),
            info=info)
    flow_lims = flow.lims('X', xlim[0], xlim[1])

    # Shape and size is no longer valid information
    # since the resulting grid could be unstructured
    assert np.array_equal((1., 1.), flow_lims.bin_size)
    assert (None, None) == flow_lims.shape
    assert ((None, None), (None, None)) == flow_lims.size
    assert 4*6 == flow_lims.num_bins

    # Check that values are good
    assert np.array_equal(cs[inds].ravel(), flow_lims.data['C'])
    assert flow.data.dtype == flow_lims.data.dtype


def test_flowdata_set_lims_none():
    xlim = (None, None)

    x = np.arange(8)
    xs, ys = np.meshgrid(x, x)
    cs = np.random.sample(xs.shape)

    flow = FlowData(('X', xs.ravel()), ('Y', ys.ravel()), ('C', cs.ravel()))
    flow_lims = flow.lims('X', *xlim)

    assert np.array_equal(xs.ravel(), flow_lims.data['X'])
    assert np.array_equal(ys.ravel(), flow_lims.data['Y'])
    assert np.array_equal(cs.ravel(), flow_lims.data['C'])


def test_flowdata_set_lims_badlabel():
    vlim = (None, None)

    xs = np.arange(8)
    ys = np.arange(8)
    cs = np.random.sample(8)

    flow = FlowData(('X', xs), ('Y', ys), ('C', cs))

    with pytest.raises(KeyError) as exc:
        flow_lims = flow.lims('none', *vlim)
        assert "FlowData object has no data with input label" in exc


def test_flowdata_set_lims_badlims():
    xlim = ('a', 'b')

    xs = np.arange(8)
    ys = np.arange(8)
    cs = np.random.sample(8)

    flow = FlowData(('X', xs), ('Y', ys), ('C', cs))

    with pytest.raises(TypeError) as exc:
        flow_lims = flow.lims('X', *xlim)
        assert "bad input limits" in exc

