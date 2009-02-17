# -*- coding: utf-8 -*-
#
# BinPac++ documentation build configuration file, created by
# sphinx-quickstart on Mon Nov 10 09:51:42 2008.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

sys.path += ["../python"]
import hilti
from hilti.core import *

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#sys.path.append(os.path.abspath('.'))

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['.templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'hilti'

# General information about the project.
project = u'HILTI'
copyright = u'2008, Robin Sommer'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = hilti.version
# The full version, including alpha/beta/rc tags.
release = hilti.release

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['.build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
#html_style = 'default.css'
html_style = 'sphinxdoc.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['.static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
#html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'HILTIdoc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
  ('hilti', 'hilti.tex', ur'HILTI Documentation',
   ur'Robin Sommer', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

########## Customizations

todo_include_todos=True

import copy

# Turns a signature into a nicely formatted __doc__ string.
def sigToRst(ins):
    def fmt(t, tag):
        if t:
            return " <%s>" % (type.fmtTypeClass(t))
        else:
            return ""
        
    op1 = fmt(ins._op1, "op1")
    op2 = fmt(ins._op2, "op2")
    op3 = fmt(ins._op3, "op3")
    target = fmt(ins._target, "target") 
    if target:
        target += " = "
        
    doc = [".. parsed-literal::", "", "  %s**%s**%s%s%s" % (target, ins._name, op1, op2, op3), ""]
    
#        if ins._op1:
#            doc += ["* Operand 1: %s" % type.name(ins._op1, docstring=True)]
#        
#        if ins._op2:
#            doc += ["* Operand 2: %s" % type.name(ins._op2, docstring=True)]
#
#        if ins._op3:
#            doc += ["* Operand 3: %s" % type.name(ins._op3, docstring=True)]
#
#        if target:
#            doc += ["* Target type: %s" % type.name(ins._target, docstring=True)]
#
    if doc:
        doc += [""]
            
    return doc

# Reformat the instruction signatures.
def reformatSignature(app, what, name, obj, options, signature, return_annotation):
    if what != "class" or not name.startswith("hilti.instructions.") or name.endswith("__init__"):
        return (signature, return_annotation)
    
    str = ""
    sig = obj.myclass._signature
    
    if sig.op1():
        str += "op1, "
    
    if sig.op2():
        str += "op2, "
        
    if sig.op3():
        str += "op3, "
        
    if sig.target():
        str += "target"
        
    return ("(%s)" % str, return_annotation)

# Reformat the __doc__ string to include signature. 
def addSignature(app, what, name, obj, options, lines):
    
    if what != "class" or not name.startswith("hilti.instructions."):
        return 

    # Prepend signature *in place*.
    tmp = copy.deepcopy(lines)
    del lines[:]
    lines += sigToRst(obj._signature)
    lines += tmp

import inspect    
import re

Substitutions = {}

def addSubst(name, role, path, level):
    if name in Substitutions:
        (oname, orole, opath, olevel) = Substitutions[name]
        if olevel <= level:
            # Lowest level wins. 
            return

    Substitutions[name] = (name, role, path, level)

def extractSubstitutions(obj, path, level, recurse):
    global Substitutions

    # Add this module and then just climb down.
    name = obj.__name__.split(".")[-1]
    addSubst(name, "mod", path, level)
    
    if "__all__" in obj.__dict__:
        # Just climb down, 
        for child in obj.__all__:
            extractSubstitutions(obj.__dict__[child], "%s.%s" % (path, child), level + 1, True)
        return 
    
    for (name, value) in inspect.getmembers(obj):

        if name.startswith("_"):
            continue
        
        val_path = "%s.%s" % (path, name)
        role = None

        if inspect.isclass(value):
            role = "class"
                    
        elif inspect.ismodule(value):
            role = "mod"
            
        elif inspect.isfunction(value):
            role = "func"
            
        elif isinstance(value, int) or isinstance(value, str):
            role = "const"

        if role:
            addSubst(name, role, val_path, level + 1)
            
        if inspect.isclass(value):
            extractSubstitutions(value, val_path, level + 1, False)
            
# Expand class references of the form ~foo.
def expandReferences(app, what, name, obj, options, lines):

    def replace(m):
        tag = m.group(1)
        addl = m.group(2)
        
        try:
            (name, role, path, level) = Substitutions[tag]
            
            if addl:
                role = "meth"
            else:
                addl = ""
                
            return ":%s:`~%s%s`" % (role, path, addl)
                
        except KeyError:
            print >>sys.stderr, "warning: ~~%s not in substitution table" % tag
            return m.group(0)
            
    regexp = re.compile(r"~~(\w+)((\.\w+)+)?\b")
    
    for i in range(len(lines)):
        lines[i] = regexp.sub(replace, lines[i])

def expandMarkup(app, what, name, obj, options, lines):

    re_arg = re.compile(r"^\s*([^:]+):\s*([^-]+)-\s*(.*)$")
    re_returns = re.compile(r"^\s*Returns:\s*([^-]+)-\s*(.*)$")
    re_raises = re.compile(r"^\s*Raises:\s*(\S+)$")
    re_note = re.compile(r"^\s*Note:\s*(.*)$")
    re_todo = re.compile(r"^\s*To-?[dD]o:\s*(.*)$")
    
    # We keep a state machine
    FIRST = 1
    TEXT = 2
    ARGS = 3
    RET = 4
    RAISES = 5
    NOTE = 6
    TODO = 7

    state = FIRST
    
    first = []
    text = []
    args = []
    ret = []
    raises = []
    note = []
    todo = []

    newlines = []
    
    for line in lines:
        
        if state == FIRST:
            i = line.find(".")
            if i < 0:
                first += [line]
            else:
                first += [line[0:i+1] + "\n"]
                text += [line[i+1:].strip()]
                state = TEXT
            continue

        next_state = state
        
        m = None
        for (regexp, nst) in [(re_returns, RET), (re_raises, RAISES), (re_arg, ARGS), (re_todo, TODO), (re_note, NOTE)]:
            m = regexp.match(line)
            if m:
                next_state = nst
                break
            
        if not m:
            # Continue current section.
            if state == TEXT:
                text += [line]
                
            elif state == ARGS:
                if line.strip():
                    args[-1] += " " + line.strip()
                
            elif state == RET:
                if line.strip():
                    ret[-1] += " " + line.strip()
                    
            elif state == RAISES:
                if line.strip():
                    raises[-1] += " " + line.strip()
                
            elif state == NOTE:
                note += [line]
                
            elif state == TODO:
                todo += [line]
                
            else:
                assert False

        else:
            # Start new section.
            if next_state == ARGS:
                (id, type, descr) = (m.group(1), m.group(2), m.group(3))
                newlines = ["- %s **%s**: %s" % (type.strip(), id.strip(), descr.strip())]
                args += newlines
                
            if next_state == RET:
                (type, descr) = (m.group(1), m.group(2))
                newlines = ["- %s: %s" % (type.strip(), descr.strip())]
                ret += newlines
                
            if next_state == RAISES:
                type = m.group(1)
                newlines = ["- %s" % type.strip()]
                raises += newlines
                
            if next_state == NOTE:
                txt = m.group(1)
                newline = txt + "\n"
                note += [newline]
                
            if next_state == TODO:
                txt = m.group(1)
                newline = txt + "\n"
                todo += [newline]
            
            state = next_state

    # Copy back to lines in place.
    del lines[:]

    for line in first:
        lines += [line]
    
    for line in text:
        lines += [line]

    if args:
        lines += ["\n"]
        lines += ["*Parameters*\n"]
        lines += ["\n"]

        for line in args:
            lines += [line + "\n"]

    if ret:
        lines += ["\n"]
        lines += ["*Return value*\n"]
        lines += ["\n"]

        for line in ret:
            lines += [line + "\n"]

    if raises:
        lines += ["\n"]
        lines += ["*Raises*\n"]
        lines += ["\n"]

        for line in raises:
            lines += [line + "\n"]
            
    if note:
        lines += ["\n"]
        lines += [".. note::\n"]
        lines += ["\n"]

        for line in note:
            lines += [line]
        
    if todo:
        lines += ["\n"]
        lines += [".. todo::\n"]
        lines += ["\n"]

        for line in todo:
            lines += [line]
            
def processDocString(app, what, name, obj, options, lines):
    expandMarkup(app, what, name, obj, options, lines)
    expandReferences(app, what, name, obj, options, lines)
    addSignature(app, what, name, obj, options, lines)

#    print >>sys.stderr, "<<<<<<<<<<<<<<<<<<<"
#    for line in lines:
#        print >>sys.stderr, line,
#    print >>sys.stderr, ">>>>>>>>>>>>>>>>>>>"
    
def setup(app):
    
    extractSubstitutions(hilti, "hilti", 1, True)

    app.connect('autodoc-process-docstring', processDocString)
    app.connect('autodoc-process-signature', reformatSignature)
    
#    lines = []
#    for line in open("test.txt"):
#        lines += [line]
#        
#    expandMarkup(0, 0, 0, 0, 0, lines)
#    sys.exit(1)
        
