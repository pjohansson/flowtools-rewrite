import numpy as np

from droplets.average import get_combined_grid, transfer_data
from droplets.flow import FlowData


def downsample_flow_data(flow, num_combine,
        coord_labels=('X', 'Y'), weights=[],
        xlim=(None, None), ylim=(None, None)):
    """Downsample input data by combining bins.

    The input data is downsampled by summing data values when
    combining the bins. Data types can be averaged by weighing
    against another value by supplying a list of tuples in
    (label, weight) format. If the weighting sums to zero in
    an area the result is returned as zero.

    The bins are combined in positive directions starting at
    index (0, 0). If the final number of bins does not evenly
    divide the starting number, some bins will be cut from the
    system in the direction of positive x and y.

    The system can be limited along x and y by supplying limits
    as 2-tuples for the keyword arguments `xlim` and `ylim`.
    Since combining datamaps is a very expensive operation
    (in this implementation) this can have a significant impact
    on the speed of the operation.

    Args:
        flow (FlowData): Object to downsample. Must have a `shape`
                and `spacing` attached as metadata.

        num_combine (2-tuple): Number of bins to combine along x and y.

    Keyword args:
        coord_labels (2-tuple, default=('X', 'Y'): Record labels for coordinates.

        weights (label, weight): A list of 2-tuples with labels of data
            and weights to calculate a weighted mean for.

        xlim/ylim (2-tuple): System limits to combine bins within.

    Returns:
        FlowData: A new object with downsampled grid.

    """

    # Cut system
    flow = _cut_system_limits(flow, xlim, ylim, coord_labels)

    # Create grid to average onto
    info = _get_downscaled_grid_info(flow, num_combine, coord_labels)
    coords = _get_downscaled_grid_coords(info)

    # Resample onto grid
    resampled_flow = _combine_bins(coords, flow, num_combine, info,
            coord_labels, weights)

    return FlowData(*resampled_flow, info=info)


def supersample_flow_data(flow, factor, coord_labels=('X', 'Y'), weights=[]):
    """Supersample input data by splitting bins into [factor] smaller ones.

    Data types can be averaged by weighing
    against another value by supplying a list of tuples in
    (label, weight) format. If the weighting sums to zero in
    an area the result is returned as zero.

    Args:
        flow (FlowData): Object to downsample. Must have a `shape`
                and `spacing` attached as metadata.

        factor (int): Factor of bin splitting.

    Keyword args:
        coord_labels (2-tuple, default=('X', 'Y'): Record labels for coordinates.

        weights (label, weight): A list of 2-tuples with labels of data
            and weights to calculate a weighted mean for.

    Returns:
        FlowData: A new object with downsampled grid.

    """

    if factor in (None, 1):
        return flow.copy()

    flow = flow.copy()
    flow.sort(coord_labels=coord_labels)

    info = _get_superscaled_grid_info(flow, factor, coord_labels)
    xs, ys = _get_superscaled_grid_coords(info)

    xl, yl = coord_labels
    nx, ny = info['shape']

    grid_data = flow.data.reshape(ny // factor, nx // factor)

    data_labels = set(flow.properties) - set(coord_labels)

    finer_grid_data = _transfer_data_to_finer_grid(
        grid_data, xs, ys, factor, coord_labels, data_labels
    )

    resampled_data = _supersample_data_on_grid(
        finer_grid_data, factor, data_labels, weights
    )

    data = [(l, resampled_data[l]) for l in resampled_data.dtype.names]

    supersampled_flow = FlowData(*data, info=info)

    return supersampled_flow

def _supersample_data_on_grid(data, factor, data_labels, weights):
    resampled_data = data.copy()
    ny, nx = data.shape

    weight_labels = [l for l, _ in weights]
    non_weighted_labels = [l for l in data_labels if l not in weight_labels]

    for (l, w) in weights:
        data[l] *= data[w]

    n = factor - 1

    for i in range(ny):
        i0 = max(0, i - n)
        i1 = i + n + 1

        for j in range(nx):
            j0 = max(0, j - n)
            j1 = j + n + 1

            bins = data[i0:i1, j0:j1]


            for l in non_weighted_labels:
                resampled_data[i, j][l] = np.mean(bins[l])

            for (l, w) in weights:
                value = np.sum(bins[l])
                total_weight = np.sum(bins[w])

                if total_weight != 0.0:
                    resampled_data[i, j][l] = value / total_weight
                else:
                    resampled_data[i, j][l] = 0.0

    return resampled_data

def _transfer_data_to_finer_grid(data, xs, ys, n, coord_labels, data_labels):
    finer_data = np.empty_like(xs, dtype=data.dtype)

    xl, yl = coord_labels
    ny, nx = data.shape

    for i in range(ny):
        i0 = i * n
        i1 = (i + 1) * n

        for j in range(nx):
            j0 = j * n
            j1 = (j + 1) * n

            for l in data_labels:
                value = data[i, j][l]
                finer_data[i0:i1, j0:j1][l] = value

    finer_data[xl] = xs
    finer_data[yl] = ys

    return finer_data


def _combine_bins(coords, flow, num_combine, info, coord_labels, weights):
    # Create container for result and add coords data
    data = np.zeros(coords[0].shape, dtype=flow.data.dtype)

    for l, cs in zip(coord_labels, coords):
        data[l] = cs

    # Sort input data in same order as the new grid
    # and reshape to 2D array
    coords_order = [coord_labels[i] for i in (1, 0)]
    shape = [flow.shape[i] for i in (1, 0)]
    reshaped_input = np.reshape(np.sort(flow.data, order=coords_order),
                                shape)

    # Get data labels, keep labels to be weighed separate
    weighted_labels = [l for l, _ in weights]
    data_labels = [l for l in data.dtype.names
                   if l not in list(coord_labels) + weighted_labels]

    nx, ny = num_combine

    for i, row in enumerate(data):
        for j, col in enumerate(row):
            inds_x, inds_y = (slice(n*k, n*(k+1))
                              for n, k in [(nx, j), (ny, i)])

            for l, w in weights:
                # The result should be zero if no weighting data is found
                try:
                    data[l][i,j] = np.average(reshaped_input[l][inds_y, inds_x],
                                              weights=reshaped_input[w][inds_y, inds_x])
                except ZeroDivisionError:
                    data[l][i,j] = 0.

            for l in data_labels:
                data[l][i,j] = np.sum(reshaped_input[l][inds_y, inds_x])

    return [(l, data[l].ravel()) for l in data.dtype.names]


def _cut_system_limits(flow, xlim, ylim, coord_labels):
    def get_cut_indices_of_axis(lims, label):
        vmin = -np.inf if lims[0] == None else lims[0]
        vmax =  np.inf if lims[1] == None else lims[1]

        return (flow.data[label] >= vmin) & (flow.data[label] <= vmax)

    xl, yl = coord_labels

    inds = get_cut_indices_of_axis(xlim, xl) & get_cut_indices_of_axis(ylim, yl)
    data = flow.data[inds]

    shape = [len(np.unique(data[l])) for l in coord_labels]
    origin = [np.min(data[l]) for l in coord_labels]

    info = {
        'shape': shape,
        'origin': origin,
        'spacing': flow.spacing,
        'num_bins': shape[0]*shape[1]
    }

    return FlowData(*[(l, data[l]) for l in flow.data.dtype.names], info=info)


def _get_downscaled_grid_info(flow, num_combine, coord_labels):
    new_spacing = [v*n for v, n in zip(flow.spacing, num_combine)]
    new_shape = [v//n for v, n in zip(flow.shape, num_combine)]
    new_origin = [o + 0.5*(new_s - s)
              for o, s, new_s in zip(flow.origin, flow.spacing, new_spacing)]

    info = {
        'spacing': new_spacing,
        'shape': new_shape,
        'origin': new_origin,
        'num_bins': new_shape[0]*new_shape[1]
    }

    return info


def _get_downscaled_grid_coords(info):
    x, y = (o + dx*np.arange(n) for o, dx, n in
            zip(info['origin'], info['spacing'], info['shape']))

    return np.meshgrid(x, y)


def _get_superscaled_grid_info(flow, n, coord_labels):
    xl, yl = coord_labels

    shape = [v * n for v in flow.shape]
    spacing = [v / n for v in flow.spacing]

    origin = np.min(flow.data[xl]), np.min(flow.data[yl])

    info = {
        'spacing': spacing,
        'shape': shape,
        'origin': origin,
        'num_bins': shape[0] * shape[1],
    }

    return info


def _get_superscaled_grid_coords(info):
    x, y = (x0 + dx * np.arange(nx) for x0, dx, nx in
            zip(info['origin'], info['spacing'], info['shape']))

    return np.meshgrid(x, y)
