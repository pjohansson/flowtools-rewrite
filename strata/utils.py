import numpy as np
import os
import warnings

"""Utilities for interacting with data files."""


def gen_filenames(base, end=np.inf, **kwargs):
    """Generates a number of file names from a base.

    Joins the input base and extension with a five-digit integer
    signifying the file number ('%s%05d%s').

    Args:
        base (str): Base of data map files.

    Keyword Args:
        begin (int, default=1): First data map number.

        end (int, default=inf): Final data map number. Can be input
            as the second positional argument.

        ext (str, default='.dat'): File extension.

    Yields:
        str: File name.

    """

    num = kwargs.pop('begin', 1)
    ext = kwargs.pop('ext', '.dat')

    try:
        while num <= end:
            yield '%s%05d%s' % (base, num, ext)
            num += 1
    except TypeError:
        err = ("TypeError: can not create filename from base %r, number %r, end %r, extension %r."
            % (base, num, end, ext))
        raise TypeError(err)


def find_datamap_files(base, **kwargs):
    """Generates data map file names found at input path base.

    If the keyword 'group' is specified file names are yielded as
    bundled lists of input length. If not enough files are found to
    fill a group the remainder is cut off and not yielded.

    Finds file names by joining the file name base and extension with
    a five-digit integer signifying the map number ('%s%05d%s').

    Args:
        base (str): Base of data map files.

    Keyword Args:
        begin (int, default=1): First data map numbering to read.

        end (int, default=inf): Final data map numbering to read.

        group (int, default=1): Yield the file names bundled in groups
            of this length.

        rolling (bool, default=False): Use a rolling average over the files.

        ext (str, default='.dat'): File extension.

    Yields:
        str, list(str): Found file names in singles or bundles.

    """

    def yield_singles(base, begin, end, ext):
        files_found = False

        for filename in gen_filenames(base, begin=begin, end=end, ext=ext):
            if os.access(filename, os.F_OK) == True:
                files_found = True
                yield filename
            else:
                if files_found == False:
                    warnings.warn(
                            "No files with base {!r} beginning at number {} were found".format(base, begin), UserWarning
                        )

                break

    def yield_groups(base, begin, end, ext):
        group_end = begin + group - 1

        while group_end <= end:
            files = list(yield_singles(base, begin, group_end, ext))

            if len(files) == group:
                yield files
                if rolling:
                    begin += 1
                    group_end += 1
                else:
                    begin += group
                    group_end += group
            else:
                break

    args = [
            kwargs.pop('begin', 1),
            kwargs.pop('end', np.inf),
            kwargs.pop('ext', '.dat')
            ]
    group = kwargs.pop('group', None)
    rolling = kwargs.pop('rolling', False)

    try:
        if group == None:
            yield from yield_singles(base, *args)
        else:
            yield from yield_groups(base, *args)
    except TypeError as err:
        print(err)
        return None


def find_singles_to_singles(base, output, **fopts):
    """Find input file names and generates with output file names.

    Used to easily read from and write to file groups.

    Args:
        base (str): Base path to input files.

        output (str): Base path to output files.

    Keyword Args:
        begin (int, default=1): First data map numbering to read.

        end (int, default=inf): Final data map numbering to read.

        ext (str, default='.dat'): File extension.

        outext (str, default=ext): Output file extension.

    Yields:
        str, str: 2-tuple with input and corresponding output paths.

    """

    out_fopts = fopts.copy()
    try:
        out_fopts['ext'] = fopts['outext']
    except KeyError:
        out_fopts['ext'] = fopts.get('ext', '.dat')

    out = gen_filenames(output, **out_fopts)
    for path in find_datamap_files(base, **fopts):
        yield path, next(out)


def find_groups_to_singles(base, output, group=1, rolling=False, **kwargs):
    """Groups input file names and return with a single file name.

    Finds file names at input path and bundle in groups of input length,
    then yield together with a generated single file name. Used to easily
    access multiple files in bundles, and output data from each bundle to
    a separate file.

    Output numbering of files will largely be compensated by the input
    frame numbering as K = ceil(N/M) where N is the first number of
    the current bundle and M is the bundle size.

    Args:
        base (str): Base path to input files.

        output (str): Base path to output files.

    Keyword Args:
        begin (int, default=1): First data map numbering to read.

        end (int, default=inf): Final data map numbering to read.

        group (int, default=1): Group input files in bundles of this length.
            Can be input as the third positional argument.

        rolling (bool, default=False): Use a rolling average over the files.

        ext (str, default='.dat'): Input file extension.

        outext (str, default=ext): Output file extension, defaults to input.

    Yields:
        (str's, str): 2-tuple with a list of input paths and their
            corresponding output path as values.

    """

    opts = pop_fileopts(kwargs)

    if rolling:
        begin_out_num = opts['begin']
    else:
        begin_out_num = np.ceil(opts['begin']/group)

    output_gen = gen_filenames(output, begin=begin_out_num, ext=opts['outext'])
    input_gen = find_datamap_files(base, group=group, rolling=rolling, **opts)
    for input_group in input_gen:
        yield input_group, next(output_gen)


def pop_fileopts(kwargs):
    """Pop common options pertaining to file reading from dict.

    The pop'd options are returned as a dict, set to default values.

    Keyword Args:
        begin (int, default=1): First data map number.

        end (int, default=inf): Final data map number. Can be input
            as the second positional argument.

        ext (str, default='.dat'): File extension.

        outext (str, default=ext): Output file extension, defaults to input.

    Return:
        dict: Input options with set or default values.

    """

    fopts = {
            'begin': kwargs.pop('begin', 1),
            'end': kwargs.pop('end', np.inf),
            'ext': kwargs.pop('ext', '.dat')
            }

    fopts['outext'] = kwargs.get('outext', fopts['ext'])

    return fopts


def prepare_path(func):
    """Wrapper for file output: Prepare a path for writing.

    Ensures that the directory exists and backs up a possible conflicting
    file. Such a file is backed up by appending pounds and a number to
    the name: '#%s.%d#'.

    Input arguments are passed on to the decorated function, the exception
    being the keyword argument _pp_verbose detailed below.

    Args:
        path (str): Path to prepare, must be the first positional argument.

    Keyword Args:
        _pp_verbose (bool, default=True): Whether or not to print information
            about a performed backup.

    """

    def prepare_path_wrapper(*args, **kwargs):
        def prepare_directory(path):
            directory, filename = os.path.split(path)
            if directory == "":
                directory = "."
            if not os.path.exists(directory):
                os.makedirs(directory)

            return directory, filename

        def backup_conflict(path):
            i = 1
            backup = path
            while os.path.exists(backup):
                new_file = '#%s.%d#' % (filename, i)
                backup = os.path.join(directory, new_file)
                i += 1

            if backup != path:
                os.rename(path, backup)
                if verbose:
                    print("Backed up '%s' to '%s'." % (path, backup))

        path = args[0]
        verbose = kwargs.pop('_pp_verbose', True)
        directory, filename = prepare_directory(path)
        backup_conflict(path)

        return func(*args, **kwargs)

    return prepare_path_wrapper


def decorate_graph(func):
    """Wrapper for decorating a figure.

    Creates a new figure window and sets options described below.

    Keyword Args:
        title (str, default=''): Title of graph.

        xlabel, ylabel (str, default=''): Axis labels.

        xlim, ylim (2-tuples, default=None): Limits of axes.

        axis (str, default=None): Set axis scaling.

        colorbar (bool, default=False): Draw a colour bar in the figure.

        colormap (str, default=None): Set a colour map.

        legend (bool, default=False): Show a legend.

        loglog (bool, default=False): Set both axes to logarithmic scale.

        save_fig (path, default=None): Save figure to path.

        dpi (int, default=150): Save figure with this dpi.

        show (bool, default=True): Show the graph.

        no_axis(bool, default=False): Hide the graph axis elements.

        clf (bool, default=True): Clear figure when finished.

    """

    import matplotlib.pyplot as plt

    def graph_wrapper(*args, **kwargs):
        def pop_figure_kwargs(kwargs):
            key_defaults = (
                    (['title', 'xlabel', 'ylabel'], ''),
                    (['xlim', 'ylim', 'save_fig', 'axis', 'colormap', 'cbarlabel', 'cbarticks', 'cbarticklabels'], None),
                    (['show', 'clf'], True),
                    (['loglog', 'colorbar', 'legend', 'noaxis', 'transparent'], False),
                    (['dpi'], 150)
            )

            fargs = {}
            for keys, default in key_defaults:
                for k in keys:
                    fargs[k] = kwargs.pop(k, default)

            return fargs

        fargs = pop_figure_kwargs(kwargs)
        func(*args, **kwargs)

        plt.title(fargs['title'])
        plt.xlabel(fargs['xlabel'])
        plt.ylabel(fargs['ylabel'])

        if fargs['loglog']:
            plt.xscale('log')
            plt.yscale('log')

        if fargs['axis']:
            plt.axis(fargs['axis'])

        plt.xlim(fargs['xlim'])
        plt.ylim(fargs['ylim'])

        if fargs['colormap'] != None:
            try:
                plt.set_cmap(fargs['colormap'])
            except ValueError as err:
                print(err)

        if fargs['colorbar']:
            from mpl_toolkits.axes_grid1 import make_axes_locatable

            ax = plt.gca()
            mappable = ax.get_children()[0]

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", "5%", pad="3%")

            cbar = plt.colorbar(mappable, cax=cax)

            if fargs['cbarlabel']:
                cbar.set_label(fargs['cbarlabel'])

            if fargs['cbarticks']:
                cbar.set_ticks(fargs['cbarticks'])

            if fargs['cbarticklabels']:
                cbar.set_ticklabels(fargs['cbarticklabels'])

        if fargs['legend']:
            plt.legend()

        if fargs['noaxis']:
            fig = plt.gcf()

            for ax in fig.axes:
                ax.set_axis_off()

        plt.tight_layout()

        if fargs['save_fig'] != None:
            plt.savefig(fargs['save_fig'], dpi=fargs['dpi'], transparent=fargs['transparent'])

        if fargs['show']:
            plt.show()

        if fargs['clf']:
            plt.clf()

        return None

    return graph_wrapper


def static_variable(variable, value):
    """Add a static variable to a function."""

    def wrapper(func):
        setattr(func, variable, value)
        return func

    return wrapper


def write_module_header(file, module, title):
    """Write a module creation header with title to input file."""

    import inspect
    import strata
    import time

    time_str = time.strftime('%c', time.localtime())
    header = (
            "# %s\n"
            "# \n"
            "# Created by module: %s\n"
            "# Creation date: %s\n"
            "# Using module version: %s\n"
            "# \n"
            % (title, module, time_str, strata.strata.version))

    with open(file, 'w') as fp:
        fp.write(header)
