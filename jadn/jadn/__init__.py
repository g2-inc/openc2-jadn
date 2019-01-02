# from pkgutil import walk_packages
# from os import path

from .enums import OpenC2MessageFormats, OpenC2SchemaFormats
from .jadn import jadn_analyze, jadn_check, jadn_dump, jadn_dumps, jadn_load, jadn_loads, jadn_merge, jadn_strip

__all__ = [
    'OpenC2MessageFormats',
    'OpenC2SchemaFormats',
    # JADN Utils
    'jadn_analyze',
    'jadn_check',
    'jadn_dump',
    'jadn_dumps',
    'jadn_load',
    'jadn_loads',
    'jadn_merge',
    'jadn_strip'
]

# Load all sub modules/packages
'''
__pkg_prefix = "%s." % __name__
__pkg_path = path.dirname(path.realpath(__file__))  # script dir

for loader, modname, ispkg in walk_packages(path=[__pkg_path], prefix=__pkg_prefix):
    if modname.startswith(__pkg_prefix):
        # load the module / package
        module = loader.find_module(modname).load_module(modname)
        modname = modname[len(__pkg_prefix):] #strip package prefix from name
        # append all toplevel modules and packages to __all__
        if not "." in modname:
            __all__.append(modname)
            globals()[modname] = module
        # set everything else as an attribute of their parent package
        else:
            # get the toplevel package from globals()
            pkg_name, rest = modname.split(".", 1)
            pkg = globals()[pkg_name]
            # recursively get the modules parent package via getattr
            while "." in rest:
                subpkg, rest = rest.split(".", 1)
                pkg = getattr(pkg, subpkg)
                del subpkg
            # set the module (or package) as an attribute of its parent package
            setattr(pkg, rest, module)
            del pkg_name, pkg, rest
        del module

del loader, modname, ispkg, walk_packages
'''
