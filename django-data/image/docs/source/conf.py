# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import django
import subprocess

git_lfs_version = "v2.9.0"

project_path = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'image.settings'
django.setup()

# Workaround modified to install and execute git-lfs on Read the Docs
# https://github.com/readthedocs/readthedocs.org/issues/1846#issuecomment-477184259
injecttool_dir = subprocess.getoutput('git rev-parse --show-toplevel')

# I want to install git-lfs here
bin_dir = os.path.join(injecttool_dir, "bin")

if not os.path.exists(bin_dir):
    os.mkdir(bin_dir)

# add a new path to PATH environment variable
os.environ['PATH'] += ":%s" % (bin_dir)

# this will be the directory where git lfs will be installed
git_lfs_path = '%s/.git/lfs' % (injecttool_dir)

if not os.path.exists(git_lfs_path):
    os.system(
        'wget -P {dest}/ https://github.com/git-lfs/git-lfs'
        '/releases/download/'
        '{version}/git-lfs-linux-amd64-{version}.tar.gz'.format(
            version=git_lfs_version,
            dest=bin_dir))

    os.system(
            'tar xvfz {path}/git-lfs-linux-amd64-{version}.tar.gz'
            ' -C {path}'.format(
                version=git_lfs_version,
                path=bin_dir))

    # test the system
    os.system('git-lfs ls-files')

    # make lfs available in current repository
    os.system('git-lfs install')

else:
    print("Git lfs already configured. Skipping")

if os.path.exists(os.path.join(bin_dir, "git-lfs")):
    # download content from remote
    os.system('git-lfs fetch')

    # make local files to have the real content on them
    os.system('git-lfs checkout')


# -- Project information -----------------------------------------------------

project = 'IMAGE-InjectTool'
copyright = '2019, Paolo Cozzi'
author = 'Paolo Cozzi'

# The full version, including alpha/beta/rc tags
release = 'v0.9.7.dev0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'celery.contrib.sphinx'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst', '.md']

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# document __init__ class method
# https://stackoverflow.com/questions/5599254/how-to-use-sphinxs-autodoc-to-document-a-classs-init-self-method
def skip(app, what, name, obj, skip, options):
    if name == "__init__":
        return False
    return skip


def setup(app):
    app.connect("autodoc-skip-member", skip)


# Link to other projects’ documentation
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.6', None),
    'django': (
        'http://docs.djangoproject.com/en/dev/',
        'https://docs.djangoproject.com/en/dev/_objects/'),
    'celery': ('http://celery.readthedocs.org/en/latest/', None),
    'pyUSIrest': ('https://pyusirest.readthedocs.io/en/latest/', None),
    }


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'nature'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
