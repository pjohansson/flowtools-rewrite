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
        'spacing': (1., 1.),
        'shape': (8, 6),
        'origin': (0., 0.),
        'num_bins': xs.size
    }

    # Cut out values of X
    flow = FlowData(('X', xs.ravel()), ('Y', ys.ravel()), ('C', cs.ravel()),
            info=info)
    flow_lims = flow.lims('X', xlim[0], xlim[1])

    # Shape and size is no longer valid information
    # since the resulting grid could be unstructured
    assert np.array_equal((1., 1.), flow_lims.spacing)
    assert (None, None) == flow_lims.shape
    assert (None, None) == flow_lims.origin
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


def test_flowdata_cut_system():
    # Cut system data along x
    xlim = (2., 5.)
    ylim = (1., 3.)

    x = np.arange(8)
    y = np.arange(6)

    xs, ys = np.meshgrid(x, y)
    cs = np.random.sample(xs.shape)

    # Get indices
    inds = (xs >= xlim[0]) & (xs <= xlim[1]) & (ys >= ylim[0]) & (ys <= ylim[1])

    info = {
        'spacing': (1., 1.),
        'shape': (8, 6),
        'origin': (0., 0.),
        'num_bins': xs.size
    }

    # Cut out values of X
    flow = FlowData(('X', xs.ravel()), ('Y', ys.ravel()), ('C', cs.ravel()),
            info=info)
    flow_lims = flow.cut(xlim=xlim, ylim=ylim)

    # We should know the final size and shape of the system
    assert np.array_equal((1., 1.), flow_lims.spacing)
    assert (4, 3) == flow_lims.shape
    assert (2., 1.) == flow_lims.origin
    assert 4 * 3 == flow_lims.num_bins

    # Check that values are good
    assert np.array_equal(cs[inds].ravel(), flow_lims.data['C'])
    assert flow.data.dtype == flow_lims.data.dtype


def test_flowdata_copy():
    xs = np.arange(8)
    info = {
        'spacing': (1., 1.),
        'origin': (0., 0.),
        'shape': (8, 1),
        'num_bins': 8
    }

    flow = FlowData(('x', xs), info=info)
    copy = flow.copy()

    assert flow.data is not copy.data
    assert np.array_equal(flow.data, copy.data)
    assert np.array_equal(flow.spacing, copy.spacing)
    assert np.array_equal(flow.origin, copy.origin)
    assert np.array_equal(flow.shape, copy.shape)
    assert flow.num_bins == copy.num_bins


def test_flowdata_translate_data():
    xs = np.random.sample(10)

    flow = FlowData(('x', xs))

    trans = 1.

    assert np.array_equal(xs+trans, flow.translate('x', trans).data['x'])
    assert np.array_equal(xs, flow.data['x'])


def test_flowdata_translate_bad_label():
    xs = np.random.sample(10)
    flow = FlowData(('x', xs))

    with pytest.raises(KeyError) as exc:
        flow.translate('nolabel', 1.)


def test_flowdata_translate_cannot_broadcast():
    xs = np.random.sample(10)
    flow = FlowData(('x', xs))

    trans = [1., 2.]

    with pytest.raises(ValueError) as exc:
        flow.translate('x', trans)

def test_flowdata_size():
    xs = np.random.sample(10)
    shape = (3, 5)
    spacing = (0.1, 0.2)

    flow = FlowData(('x', xs), info={'shape': shape, 'spacing': spacing})

    dx, dy = flow.size()

    assert (dx == shape[0] * spacing[0])
    assert (dy == shape[1] * spacing[1])

    flow = FlowData(('x', xs), info={'shape': shape})
    assert (None == flow.size())

    flow = FlowData(('x', xs), info={'spacing': spacing})
    assert (None == flow.size())

    flow = FlowData(('x', xs), info={})
    assert (None == flow.size())
