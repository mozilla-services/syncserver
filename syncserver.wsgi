# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import site
from logging.config import fileConfig
from ConfigParser import NoSectionError

# detecting if virtualenv was used in this dir
_CURDIR = os.path.dirname(os.path.abspath(__file__))
_PY_VER = sys.version.split()[0][:3]
_SITE_PKG = os.path.join(_CURDIR, 'local', 'lib', 'python' + _PY_VER, 'site-packages')

# adding virtualenv's site-package and ordering paths
saved = sys.path[:]

if os.path.exists(_SITE_PKG):
    site.addsitedir(_SITE_PKG)

for path in sys.path:
    if path not in saved:
        saved.insert(0, path)

sys.path[:] = saved

# setting up the egg cache to a place where apache can write
os.environ['PYTHON_EGG_CACHE'] = '/tmp/python-eggs'

# setting up logging
ini_file = os.path.join(_CURDIR, 'syncserver.ini')
try:
    fileConfig(ini_file)
except NoSectionError:
    pass

# running the app using Paste
from paste.deploy import loadapp
application = loadapp('config:%s'% ini_file)
