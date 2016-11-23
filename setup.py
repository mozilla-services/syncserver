# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
from setuptools import setup

entry_points = """
[paste.app_factory]
main = syncserver:main
"""

setup(
    name='syncserver',
    version="1.6.0",
    packages=['syncserver'],
    entry_points=entry_points
)
