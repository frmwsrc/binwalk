#!/usr/bin/env python
from __future__ import print_function
import os
import sys
from distutils.core import setup
from distutils.dir_util import remove_tree

# Python2/3 compliance
try:
	raw_input
except NameError:
	raw_input = input

def cleanup_build_directory():
	# Requires to chdir into the src directory first
	try:
		remove_tree("build")
	except KeyboardInterrupt as e:
		raise e
	except Exception:
		pass

def cleanup_module_directory():
	# Installing doesn't remove old files that may have been deleted from the module.
	if "install" in sys.argv:
		try:
			import binwalk
			for path in binwalk.__path__:
				try:
					remove_tree(path + os.path.sep + "*")
				except OSError as e:
					pass
		except ImportError:
			pass

# Change to the binwalk src directory
def warning(lines, terminate=True, prompt=True):
	WIDTH = 115

	if not IGNORE_WARNINGS:
		print("\n" + "*" * WIDTH)
		for line in lines:
			print(line)
		print("*" * WIDTH, "\n")

		if prompt:
			if raw_input('Continue installation anyway (Y/n)? ').lower().startswith('n'):
				terminate = True
			else:
				terminate = False

		if terminate:
			sys.exit(1)
		
# This is super hacky.
if "--yes" in sys.argv:
	sys.argv.pop(sys.argv.index("--yes"))
	IGNORE_WARNINGS = True
else:
	IGNORE_WARNINGS = False

# cd into the src directory, no matter where setup.py was invoked from
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "src"))

print("checking pre-requisites")
try:
	import magic
	try:
		magic.MAGIC_NO_CHECK_TEXT
	except AttributeError as e:
		msg = ["Pre-requisite failure: " + str(e),
			"It looks like you have an old or incompatible magic module installed.",
			"Please install the official python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/"
		]
		
		warning(msg)
except ImportError as e:
	msg = ["Pre-requisite failure:", str(e),
		"Please install the python-magic module, or download and install it from source: ftp://ftp.astron.com/pub/file/",
	]
	
	warning(msg)

try:
	import pyqtgraph
except ImportError as e:
	msg = ["Pre-requisite check warning: " + str(e),
		"To take advantage of this tool's graphing capabilities, please install the pyqtgraph module.",
	]
	
	warning(msg, prompt=True)

# Build / install C compression libraries
c_lib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "C")
c_lib_makefile = os.path.join(c_lib_dir, "Makefile")

working_directory = os.getcwd()
os.chdir(c_lib_dir)
status = 0

if not os.path.exists(c_lib_makefile):
	status |= os.system("./configure")

status |= os.system("make")

if status != 0:
	msg = ["Build warning: failed to build C libraries.",
		"Some features will not work without these libraries."
	]
	warning(msg, prompt=True)
elif "install" in sys.argv:
	if os.system("make install") != 0:
		msg = ["Install warning: failed to install C libraries.",
			   "Some features will not work without these libraries."
		]
		warning(msg, prompt=True)

os.system("make distclean")
	
os.chdir(working_directory)

cleanup_build_directory()
cleanup_module_directory()

# Generate a new magic file from the files in the magic directory
print("creating binwalk magic file")
magic_files = os.listdir("magic")
magic_files.sort()
fd = open("binwalk/magic/binwalk", "wb")
for magic in magic_files:
	fpath = os.path.join("magic", magic)
	if os.path.isfile(fpath):
		fd.write(open(fpath, "rb").read())
fd.close()

# The data files to install along with the binwalk module
install_data_files = ["magic/*", "config/*", "plugins/*", "modules/*", "core/*"]

# Install the binwalk module, script and support files
setup(	name = "binwalk",
	version = "2.0.0 beta",
	description = "Firmware analysis tool",
	author = "Craig Heffner",
	url = "https://github.com/devttys0/binwalk",

	requires = ["magic", "pyqtgraph"],
	packages = ["binwalk"],
	package_data = {"binwalk" : install_data_files},
	scripts = ["scripts/binwalk"],
)

cleanup_build_directory()
