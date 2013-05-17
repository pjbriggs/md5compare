#!/bin/env python
#
#     compare.py: compare contents of a pair of directories with md5 sums
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# compare.py
#
#########################################################################

"""compare.py

Compare the contents of a pair of directories using MD5 sums
"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.0.1"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import optparse
import logging
import Md5sum

#######################################################################
# Classes
#######################################################################

# none defined

#######################################################################
# Functions
#######################################################################

def compare(dir1,dir2,output):
    """Compare two directories using MD5 sums

    """
    # First get set of contents of dir1 and dir2
    dir1_set = set(list_files(dir1))
    dir2_set = set(list_files(dir2))
    # Initialise list of files with non-matching checksums
    different = []
    # Get list of common files (and of those which only appear in once
    # in one of the dirs)
    only_in_1 = list(dir1_set.difference(dir2_set))
    only_in_1.sort()
    only_in_2 = list(dir2_set.difference(dir1_set))
    only_in_2.sort()
    common = list(dir1_set.intersection(dir2_set))
    common.sort()
    # Report
    print "Files only in %s (%d)" % (dir1,len(only_in_1))
    for f in only_in_1:
        print "\t%s" % str(f)
    print "Files only in %s (%d)" % (dir2,len(only_in_2))
    for f in only_in_2:
        print "\t%s" % str(f)
    print "Common files (%d)" % len(common)
    for f in common:
        if check_file(dir1,dir2,f):
            status = "OK"
        else:
            status = "FAILED"
            different.append(f)
        print "\t%s\t%s" % (status,f)

def check_file(dir1,dir2,filen):
    """Compare the checksums for a file in two directories

    """
    chksum1 = Md5sum.md5sum(os.path.join(dir1,filen))
    chksum2 = Md5sum.md5sum(os.path.join(dir2,filen))
    return chksum1 == chksum2

def list_files(dirn):
    """Return a list of all files under a directory

    """
    files = []
    for d in os.walk(dirn):
        # os.walk returns tuple (dir,(file1,file2,...))
        for f in d[2]:
            # Hacky way to get path of each file relative to dirn
            files.append(os.path.join(str(d[0])[len(dirn):].lstrip(os.sep),f))
    files.sort()
    return files

def make_checksum_file(dirn,checksum_file):
    """Generate a file with the checksums for a specified directory

    """
    fp = open(checksum_file,'w')
    for f in list_files(dirn):
        checksum = Md5sum.md5sum(os.path.join(dirn,f))
        fp.write("%s  %s\n" % (checksum,f))
    fp.close()

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    usage = "%prog FROM_DIR TO_DIR OUTPUT_FILE"
    p = optparse.OptionParser(usage=usage,
                              version="%prog "+__version__,
                              description=
                              "compare contents of a pair of directories using "
                              "MD5 sums")
    # Define options
    p.add_option('--progress',action="store_true",dest="progress",default=False,
                 help="report progress")

    # Process command line
    options,arguments = p.parse_args()
    if len(arguments) != 3:
        p.error("Needs 3 arguments: FROM_DIR, TO_DIR and OUTPUT_FILE")
    from_dir = arguments[0]
    if not os.path.isdir(from_dir):
        p.error("%s: directory not found" % from_dir)
    to_dir = arguments[1]
    if not os.path.isdir(from_dir):
        p.error("%s: directory not found" % to_dir)
    output_file = arguments[2]

    # Set up logging output
    logging.basicConfig(format='%(message)s')
    
    # Invoke the comparison
    compare(from_dir,to_dir,output_file)
    
