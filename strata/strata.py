import click
from click import argument as add_argument
from click import option as add_option
from click import group as create_group
import numpy as np

from strata.average import average
from strata.convert import convert
from strata.interface.collect import collect_interfaces
from strata.interface.view import view_interfaces
from strata.contact_line_analysis import extract_contact_line_bins
from strata.spreading.collect import collect
from strata.spreading.view import view

"""Command line utility to invoke the functionality of strata."""

def print_version(ctx, param, value):
    import pkg_resources
    version_str = pkg_resources.require("flowfield")[0].version

    if not value or ctx.resilient_parsing:
        return
    click.echo('Version %s' % version_str)
    ctx.exit()

# Main functionality
@create_group()
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
def strata():
    """Tools for reading and analysing files of flow data."""
    pass


# Description of commands
cmd_average = {
        'name': 'average',
        'desc': 'Sample average data files.'
        }
cmd_convert = {
        'name': 'convert',
        'desc': 'Convert data files to another format.'
        }
cmd_contactline = {
        'name': 'contact_line',
        'desc': 'Analyse data around the contact line.'
        }

cmd_interface = {
        'name': 'interface',
        'desc': 'View, average or collect interface data.'
        }
cmd_intcollect = {
        'name': 'collect',
        'desc': 'Find the interface boundary of droplet data.'
        }
cmd_intview = {
        'name': 'view',
        'desc': 'View and average collected interface data.'
}



cmd_spreading = {
        'name': 'spreading',
        'desc': 'View or collect spreading data.'
        }
cmd_collect = {
        'name': 'collect',
        'desc': 'Collect the spreading radius per time for a droplet.'
        }
cmd_view = {
        'name': 'view',
        'desc': 'View data of spreading files.'
        }


# Average wrapper
@strata.command(name=cmd_average['name'], short_help=cmd_average['desc'])
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
@strata.command(name=cmd_convert['name'], short_help=cmd_convert['desc'])
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


# Combined spreading tools for collection and plotting
@strata.group()
def spreading(name=cmd_spreading['name'], short_help=cmd_spreading['desc']):
    """View or collect spreading data of droplets."""
    pass


# Spreading wrapper
@spreading.command(name=cmd_collect['name'], short_help=cmd_collect['desc'])
@add_argument('base', type=str)
@add_argument('floor', type=float)
@add_option('-o', '--output', type=click.Path(), default=None,
        help='Write the collected data to disk.')
@add_option('-dt', '--delta_t', 'dt', default=1.,
    help='Time difference between data map files. (1)')
@add_option('-co', '--cutoff', type=float, default=None,
        help='Boundary bins require this much mass. (0)')
@add_option('-cr', '--cutoff_radius', default=1.,
        help='Boundary bins search for neighbours within this radius. (1 nm)')
@add_option('-cb', '--cutoff_bins', default=1,
        help='Boundary bins require this many neighbours.')
@add_option('-b', '--begin', default=1, type=click.IntRange(0, None),
        help='Begin reading from BASE at this number. (1)')
@add_option('-e', '--end', default=None, type=click.IntRange(0, None),
        help='End reading from BASE at this number. (None)')
@add_option('--ext', default='.dat',
        help='Read using this file extension. (.dat)')
@add_option('-v', '--verbose', default=False, is_flag=True,
        help='Verbose output: Print spreading to stdout.')
def spreading_collect_cli(base, floor, **kwargs):
    """Collect spreading radius r(t) at height FLOOR for input files at BASE.

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
    data = collect(base, **kwargs)

    if verbose:
        print("Time (ps) Radius (nm)")
        for time, radius in data:
            print("%.3f %.3f" % (time, radius))


# Plotting wrapper
@spreading.command(name=cmd_view['name'], short_help=cmd_view['desc'])
@add_argument('files', type=click.Path(exists=True), nargs=-1)
@add_option('-t', '--tau', type=float, default=1., metavar='TAU',
        help='Time scaling factor.')
@add_option('-r', '--radius', 'R', type=float, default=1., metavar='R',
        help='Radius scaling factor.')
@add_option('-rs', '--sync_radius', type=float, default=None,
        help='Synchronise data at this radius. Done after scaling by R. (None)')
@add_option('-o', '--save_fig', type=click.Path(), default=None,
        help='Save figure to path. (None)')
@add_option('-x', '--save_xvg', type=click.Path(), default=None,
        help='Save read data to path. (None)')
@add_option('--show/--noshow', default=True,
        help='Whether or not to draw graph. (True)')
@add_option('--loglog', is_flag=True,
        help='Scale graph axes logarithmically.')
@add_option('--xlim', type=float, nargs=2, default=(None, None),
        metavar='MIN MAX', help='Set limits on the x axis.')
@add_option('--ylim', type=float, nargs=2, default=(None, None),
        metavar='MIN MAX', help='Set limits on the y axis.')
@add_option('--title', default='Droplet spreading',
        help='Figure title.')
@add_option('--xlabel', default='Time (ps)',
        help='Label of x axis.')
@add_option('--ylabel', default='Radius (nm)',
        help='Label of y axis.')
@add_option('--grid/--nogrid', default=False,
        help='Draw background grid in figure.')
def spreading_view_cli(files, **kwargs):
    """View spreading data of input FILES.

    Input files must be in whitespace separated format, the first column
    designating time with all following being their corresponding spreading
    radii.

    The combined data can be saved to disk in an XmGrace compatible format.
    For data output non-existing data at any time point is set to 0.

    """

    view(files, **kwargs)

# Combined interface tools for collectiong and plotting
@strata.group()
def interface(name=cmd_interface['name'], short_help=cmd_interface['desc']):
    """Work with interface data of droplets."""
    pass


# Interface collect wrapper
@interface.command(name=cmd_intcollect['name'], short_help=cmd_intcollect['desc'])
@add_argument('base', type=str)
@add_argument('output', type=str)
@add_option('-com', '--adjust_com', default=True,
        help='Center interface coordinates around the center of mass. (True)')
@add_option('-co', '--cutoff', type=float, default=None,
        help='Boundary bins require this much mass. (0)')
@add_option('-cr', '--cutoff_radius', default=1.,
        help='Boundary bins search for neighbours within this radius. (1 nm)')
@add_option('-cb', '--cutoff_bins', default=1,
        help='Boundary bins require this many neighbours.')
@add_option('-b', '--begin', default=1, type=click.IntRange(0, None),
        help='Begin reading from BASE at this number. (1)')
@add_option('-e', '--end', default=None, type=click.IntRange(0, None),
        help='End reading from BASE at this number. (None)')
@add_option('--ext', default='.dat',
        help='Read using this file extension. (.dat)')
def interface_collect_cli(base, output, **kwargs):
    """Collect the interface boundaries for input files at BASE to OUTPUT.

    The interface is calculated at each height by finding the outermost bins
    fulfilling set criteria to be considered parts of the droplet. For each
    considered bin in the bottom-most layer which has more mass than a set
    cut-off, a search is made for similarly filled bins within a set radius.
    If the number of filled bins within this radius surpasses the final
    requirement, the bin is considered to be connected to the main droplet.
    The left- and rightmost of these bins in the selected layer are taken
    as its boundary cells.

    Read data files must have data fields corresponding to coordinates
    and mass.

    File names are generated by joining the base path and extension with
    a five-digit integer signifying file number ('%s%05d%s').

    """

    set_none_to_inf(kwargs)
    xs, ys = collect_interfaces(base, output, **kwargs)


# Interface viewing wrapper
@interface.command(name=cmd_intview['name'], short_help=cmd_intview['desc'])
@add_argument('base', type=str)
@add_option('-av', '--average', type=click.IntRange(1, None), default=1,
        help='Average interface data in bundles of this size. (1)')
@add_option('-o', '--save_fig', type=str, default=None,
        help='Save figures to base path..')
@add_option('-x', '--save_xvg', type=click.Path(), default='',
        help='Save collected data to disk at base as .xvg file.')
@add_option('--show/--noshow', default=True,
        help='Whether or not to draw graph. (True)')
@add_option('--xlim', type=float, nargs=2, default=(None, None),
        metavar='MIN MAX', help='Set limits on the x axis.')
@add_option('--ylim', type=float, nargs=2, default=(None, None),
        metavar='MIN MAX', help='Set limits on the y axis.')
@add_option('--title', default='Droplet interface',
        help='Figure title.')
@add_option('--xlabel', default='x (nm)',
        help='Label of x axis.')
@add_option('--ylabel', default='y (nm)',
        help='Label of y axis.')
@add_option('-b', '--begin', default=1, type=click.IntRange(0, None),
        help='Begin reading from BASE at this number. (1)')
@add_option('-e', '--end', default=None, type=click.IntRange(0, None),
        help='End reading from BASE at this number. (None)')
@add_option('--ext', default='.xvg',
        help='Read using this file extension. (.xvg)')
def interface_view_cli(base, **kwargs):
    """View the interface boundaries for input files at BASE.

    Optionally averages the interface data over an input bundling length.
    The averaged interfaces can be written to disk as new Grace formatted
    files.

    File names are generated by joining the base path and extension with
    a five-digit integer signifying file number ('%s%05d%s').

    """

    set_none_to_inf(kwargs)
    xs, ys = view_interfaces(base, **kwargs)


# Contact line averaging wrapper
@strata.command(name=cmd_contactline['name'],
        short_help=cmd_contactline['desc'])
@add_argument('base', type=str)
@add_argument('output', type=str)
@add_option('-av', '--average', type=click.IntRange(1, None), default=1,
        help='Sample average the extracted data of these many files.')
@add_option('-ea', '--extract_area', type=float, default=(0., 0.), nargs=2,
        help='Extract area of this size. (0, 0)')
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
        help='Read and write using this file extension. (.dat)')
def cl_average_cli(base, output, **kwargs):
    """Extract the contact line area of files at BASE and write to OUTPUT.

    The contact line area is determined as: For each considered bin
    in the bottom-most layer which has more mass than a set cut-off, a
    search is made for similarly filled bins within a set radius. If the
    number of filled bins within this radius surpasses the final requirement,
    the bin is considered to be connected to the main droplet. The left- and
    rightmost of these bins in the selected layer are taken as the contact
    line edge bins.

    From these bins an area of input extraction size into the bulk is
    included, as well as any cells up to and including the interface
    at each height.

    The data can be sample averaged by supplying a number of files to
    average over. In this case all input files must be of similar coordinate
    grid spacings.

    File names are generated by joining the base path and extension with
    a five-digit integer signifying file number ('%s%05d%s').

    """

    set_none_to_inf(kwargs)
    extract_contact_line_bins(base, output, **kwargs)


def set_none_to_inf(kwargs, label='end'):
    if kwargs[label] == None:
        kwargs[label] = np.inf
