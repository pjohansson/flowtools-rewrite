import numpy as np
import warnings

def average_data(*data, atol=1e-3, rtol=1e-05):
    """Return a sample average of several plain maps.

    Note that flows ('U', 'V') are mass averaged and that the temperature
    ('T') is number averaged.

    Relative and absolute tolerances are used to ascertain that the input
    map coordinates are identical for each map. These can be controlled by
    the keyword arguments 'atol' and 'rtol'.

    Args:
        data (dict): List of dict's with data read from a simple data map,
            with fields ('X', 'Y', 'M', 'N', 'T', 'U', 'V').

    Keyword Args:
        atol (float): Absolute tolerance for the coordinate check.

        rtol (float): Relative tolerance for the coordinate check.

    Returns:
        dict: An averaged record. Empty if no data was input.

    Raises:
        ValueError: If coordinates of all input data are not identical.

    """

    def init_with_coords(data):
        coords = {l: data[0][l] for l in ('X', 'Y')}
        for d in data[1:]:
            for l in ('X', 'Y'):
                # Check that input coordinates of all maps match each other
                # An absolute tolerance value is used but might not be the
                # best solution, better might be for the caller to assert
                # that the coordinates match sufficiently before trying
                # to average the maps. Then again floating point comparisons
                # are what they are so it's probably best to keep it.
                assert (np.isclose(coords[l], d[l], atol=atol, rtol=rtol).all())
        return coords

    def get_sum_weights():
        weights = ('N', 'M')
        return {w: np.sum([d[w] for d in data], 0) for w in weights}

    def get_avg(field):
        return np.mean([d[field] for d in data], 0)

    def get_weighted_avg(field, weight):
        weighted_sum = np.sum([d[field]*d[weight] for d in data], 0)

        # A warning will be raised if any summed weight is 0. Catch that
        # warning, then set all nan-results to 0. 
        with warnings.catch_warnings(record=True):
            weighted_avg = weighted_sum/sum_weights[weight]

        return np.nan_to_num(weighted_avg)

    if list(data) == []:
        return {}

    try:
        avg_data = init_with_coords(data)
    except AssertionError:
        raise ValueError("coordinates of data to average does not match for all maps")

    sum_weights = get_sum_weights()

    avg_data['M'] = get_avg('M')
    avg_data['N'] = get_avg('N')
    avg_data['U'] = get_weighted_avg('U', 'M')
    avg_data['V'] = get_weighted_avg('V', 'M')
    avg_data['T'] = get_weighted_avg('T', 'N')

    return avg_data


def combine_bins(data, info, nx, ny):
    """Combines bins of input data and returns it and a new info dict.

    Note that flows ('U', 'V') are mass averaged and that the temperature
    ('T') is number averaged.

    Args:
        data (dict): Dict with data read from a simple data map,
            with fields ('X', 'Y', 'M', 'N', 'T', 'U', 'V').

        info (dict): Information for input data. See
            strata.dataformats.read.read_data_file for more information.

        nx, ny (int): Number of bins to combine along x and y respectively.

    Returns:
        (dict, dict): The combined bin data and information.

    """

    # Construct new grid, keeping in mind that the origin points
    # are the mid-points of each bin which means that we have to
    # correct for that in the origin calculation.
    # This is pretty simple math but basically we take n-1
    # steps of 0.5 times the original spacing to the right,
    # since this brings us to the middle of the first n cells.
    shape = [info['shape'][0] // nx, info['shape'][1] // ny]
    spacing = [info['spacing'][0] * nx, info['spacing'][1] * ny]
    origin = [x0 + 0.5*dx*(num - 1)
        for x0, dx, num in zip(info['origin'], info['spacing'], (nx, ny))]
    num_bins = shape[0]*shape[1]

    new_info = {
        'origin': origin,
        'spacing': spacing,
        'shape': shape,
        'num_bins': num_bins
    }

    x, y = [np.linspace(x0, x0 + dx*(num-1), num)
        for x0, dx, num in zip(origin, spacing, shape)]
    xs, ys = np.meshgrid(x, y, indexing='ij')

    new_data = { 'X': xs.ravel(), 'Y': ys.ravel() }

    labels_and_weights = ('N', None), ('M', None), ('T', 'N'), ('U', 'M'), ('V', 'M')
    for label, weight in labels_and_weights:
        ds = data[label].reshape(info['shape'])
        new_data[label] = np.zeros(xs.shape)

        try:
            ws = data[weight].reshape(info['shape'])
        except KeyError:
            ws = None

        for i in range(shape[0]):
            for j in range(shape[1]):
                if ws is weight:
                    new_data[label][i, j] = np.sum(ds[nx*i:nx*(i+1), ny*j:ny*(j+1)])
                else:
                    try:
                        new_data[label][i, j] = np.average(ds[nx*i:nx*(i+1), ny*j:ny*(j+1)],
                            weights=ws[nx*i:nx*(i+1), ny*j:ny*(j+1)])
                    except ZeroDivisionError:
                        new_data[label][i, j] = 0.0

        new_data[label].resize((num_bins, ))

    return new_data, new_info
