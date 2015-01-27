import click
from click import argument as add_argument
from click import option as add_option
from click import group as create_group
import numpy as np

from strata.average import average
from strata.convert import convert
from strata.spreading import spreading

"""Command line utility to invoke the functionality of strata."""


# Main functionality
@create_group()
def strata():
    """Tools for reading and analysing files of flow data."""
    pass


# Average wrapper
@strata.command(name='average', short_help='Sample average data files.')
@add_argument('base', type=str)
@add_argument('output', type=str)
@add_argument('group', type=click.IntRange(1, None))
@add_option('-b', '--begin', default=1, type=click.IntRange(0, None),
        help='Begin reading from BASE at this number. (1)')
@add_option('-e', '--end', default=None, type=click.IntRange(0, None),
        help='End reading from BASE at this number. (None)')
@add_option('--ext', default='.dat',
        help='Read and write using this file extension. (.dat)')
def average_cli(base, output, group, **kwargs):
    """Sample average files at BASE path in bundles of size GROUP
    and write to files at OUTPUT base.

    File names are generated by joining the base path and extension with
    a five-digit integer signifying file number ('%s%05d%s').

    """

    set_none_to_inf(kwargs)
    average(base, output, group, **kwargs)


# Convert wrapper
@strata.command(name='convert', short_help='Convert data files to another format.')
@add_argument('base', type=str)
@add_argument('output', type=str)
@add_option('--ftype',
        type=click.Choice(['simple', 'simple_plain']), default='simple',
        help='Format to convert files into. (simple)')
@add_option('-b', '--begin', default=1, type=click.IntRange(0, None),
        help='Begin reading from BASE at this number. (1)')
@add_option('-e', '--end', default=None, type=click.IntRange(0, None),
        help='End reading from BASE at this number. (None)')
@add_option('--ext', default='.dat',
        help='Read and write using this file extension. (.dat)')
def convert_cli(base, output, **kwargs):
    """Convert files at BASE path to another data file format
    and write to files at OUTPUT base.

    File names are generated by joining the base path and extension with
    a five-digit integer signifying file number ('%s%05d%s').

    """

    set_none_to_inf(kwargs)
    convert(base, output, **kwargs)


# Spreading wrapper
@strata.command(name='spreading',
        short_help='Find the spreading radius per time for a droplet.')
@add_argument('base', type=str)
@add_argument('floor', type=float)
@add_option('-o', '--output', type=click.Path(), default=None,
        help='Write the collected data to disk.')
@add_option('-dt', '--delta_t', 'dt', default=1.,
    help='Time difference between data map files. (1)')
@add_option('-co', '--cutoff', type=float, default=None,
        help='Boundary bins require this much mass. (0)')
@add_option('-ir', '--include_radius', default=1.,
        help='Boundary bins search for neighbours within this radius. (1 nm)')
@add_option('-nb', '--num_bins', default=1,
        help='Boundary bins require this many neighbours.')
@add_option('-b', '--begin', default=1, type=click.IntRange(0, None),
        help='Begin reading from BASE at this number. (1)')
@add_option('-e', '--end', default=None, type=click.IntRange(0, None),
        help='End reading from BASE at this number. (None)')
@add_option('--ext', default='.dat',
        help='Read using this file extension. (.dat)')
@add_option('-v', '--verbose', default=False, is_flag=True,
        help='Verbose output: Print spreading to stdout.')
def spreading_cli(base, floor, **kwargs):
    """Find the spreading radius r(t) at height FLOOR for input files at BASE.

    The radius is calculated by finding the outermost bins fulfilling set
    criteria to be considered parts of the droplet. For each considered bin
    in the bottom-most layer which has more mass than a set cut-off, a
    search is made for similarly filled bins within a set radius. If the
    number of filled bins within this radius surpasses the final requirement,
    the bin is considered to be connected to the main droplet. The left- and
    rightmost of these bins in the selected layer are taken as the droplet
    spreading edges from which the radius is calculated.

    Read data files must have data fields corresponding to coordinates
    and mass.

    File names are generated by joining the base path and extension with
    a five-digit integer signifying file number ('%s%05d%s').

    """

    verbose = kwargs.pop('verbose')

    set_none_to_inf(kwargs)
    kwargs['floor'] = floor
    data = spreading(base, **kwargs)

    if verbose:
        print("Time (ps) Radius (nm)")
        for time, radius in data:
            print("%.3f %.3f" % (time, radius))


def set_none_to_inf(kwargs, label='end'):
    if kwargs[label] == None:
        kwargs[label] = np.inf
