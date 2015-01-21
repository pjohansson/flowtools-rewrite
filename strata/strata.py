import click
from click import argument as add_argument
from click import option as add_option
from click import group as create_group
import numpy as np

from strata.average import average
from strata.convert import convert

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


def set_none_to_inf(kwargs, label='end'):
    if kwargs[label] == None:
        kwargs[label] = np.inf
