# -*- coding: utf-8 ; test-case-name: bridgedb.test.test_runner -*-
#
# This file is part of BridgeDB, a Tor bridge distribution system.
#
# :authors: Isis Lovecruft 0xA3ADB67A2CDB8B35 <isis@torproject.org>
#           please also see AUTHORS file
# :copyright: (c) 2007-2017, The Tor Project, Inc.
#             (c) 2007-2017, all entities within the AUTHORS file
#             (c) 2012-2017, Isis Lovecruft
# :license: 3-clause BSD, see included LICENSE for information

"""Classes for running components and servers, as well as daemonisation.

** Module Overview: **

"""

from __future__ import print_function

import glob
import logging
import sys
import os

from twisted.python import procutils

import util


def cleanupUnparseableDescriptors(directory, seconds):
    """Delete any ``*.unparseable`` descriptor files in ``directory`` with
    mtimes more than ``seconds`` ago.

    The :func:`bridgedb.parsers._copyUnparseableDescriptors` function
    will make copies of any files we attempt to parse which contain
    unparseable descriptors.  This function should run on a timer to
    clean them up.

    :param str directory: The directory in which to search for unparseable
        descriptors.
    :param int olderThan: If a file's mtime is more than this number
        (in seconds), it will be deleted.
    """
    files = []

    for pattern in ["*.unparseable", "*.unparseable.xz"]:
        files.extend(glob.glob(os.sep.join([directory, pattern])))

    if files:
        logging.info("Deleting old unparseable descriptor files...")
        logging.debug("Considered for deletion: %s" % "\n".join(files))

        deleted = util.deleteFilesOlderThan(files, seconds)
        logging.info("Deleted %d unparseable descriptor files." % len(deleted))

def find(filename):
    """Find the executable ``filename``.

    :param string filename: The executable to search for. Must be in the
       effective user ID's $PATH.
    :rtype: string
     :returns: The location of the executable, if found. Otherwise, returns
        None.
    """
    executable = None

    logging.debug("Searching for installed '%s'..." % filename)
    which = procutils.which(filename, os.X_OK)

    if len(which) > 0:
        for that in which:
            if os.stat(that).st_uid == os.geteuid():
                executable = that
                break
    if not executable:
        return None

    logging.debug("Found installed script at '%s'" % executable)
    return executable

def generateDescriptors(count=None, rundir=None):
    """Run a script which creates fake bridge descriptors for testing purposes.

    This will run Leekspin_ to create bridge server descriptors, bridge
    extra-info descriptors, and networkstatus document.

    .. warning: This function can take a very long time to run, especially in
        headless environments where entropy sources are minimal, because it
        creates the keys for each mocked OR, which are embedded in the server
        descriptors, used to calculate the OR fingerprints, and sign the
        descriptors, among other things.

    .. _Leekspin: https://gitweb.torproject.org/user/isis/leekspin.git

    :param integer count: Number of mocked bridges to generate descriptor
        for. (default: 3)
    :type rundir: string or None
    :param rundir: If given, use this directory as the current working
        directory for the bridge descriptor generator script to run in. The
        directory MUST already exist, and the descriptor files will be created
        in it. If None, use the whatever directory we are currently in.
    """
    import subprocess
    import os.path

    proc = None
    statuscode = 0
    script = 'leekspin'
    rundir = rundir if os.path.isdir(rundir) else None
    count = count if count else 3
    try:
        proc = subprocess.Popen([script, '-n', str(count)],
                                close_fds=True, cwd=rundir)
    finally:
        if proc is not None:
            proc.wait()
            if proc.returncode:
                print("There was an error generating bridge descriptors.",
                      "(Returncode: %d)" % proc.returncode)
                statuscode = proc.returncode
            else:
                print("Sucessfully generated %s descriptors." % str(count))
        del subprocess
        return statuscode
