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

class Compare:
    """Class to compare contents of two directories
    
    """

    def __init__(self,from_dir,to_dir):
        """Create a new Compare object

        Arguments:
          from_dir: path to "source" directory
          to_dir: path to "target" directory

        """
        # Store info about source ("from") dir
        self._from_dir = from_dir
        self._from_set = set(self.list_files(from_dir))
        # Store info about target ("to") dir
        self._to_dir = to_dir
        self._to_set = set(self.list_files(to_dir))
        # Lists created from subsets
        self._common = list(self._from_set.intersection(self._to_set))
        self._only_in_from = list(self._from_set.difference(self._to_set))
        self._only_in_to   = list(self._to_set.difference(self._from_set))
        # Sort the lists
        self._common.sort()
        self._only_in_from.sort()
        self._only_in_to.sort()
        # Do checksum comparison
        self.go_compare()

    def go_compare(self):
        """Do the comparison

        """
        failed_md5 = []
        unreadable = []
        for f in self._common:
            try:
                if not self.check_md5(f):
                    failed_md5.append(f)
            except IOError:
                unreadable.append(f)
        self._failed_md5 = failed_md5
        self._unreadable = unreadable

    def report(self,output_file=None,fp=sys.stdout):
        """Write a report of the comparison

        Report will be written to the specified file name (if provided),
        or else to the specified file handle (must have been opened for
        writing).

        If neither is supplied then the report is written to stdout.

        """
        # Deal with output file
        if output_file is not None:
            self.report(fp=open(output_file,'w'))
            return
        # Preamble
        title_line = "Comparing contents of %s and %s" % (self._from_dir,
                                                          self._to_dir)
        fp.write("%s\n%s\n" % (title_line,"="*len(title_line)))
        # Summary
        fp.write("\nSummary\n%s\n" % ("-"*len("Summary")))
        fp.write("\t%d files only found in %s\n" % (len(self._only_in_from),self._from_dir))
        fp.write("\t%d files only found in %s\n" % (len(self._only_in_to),self._to_dir))
        fp.write("\t%d files in both\n" % len(self._common))
        fp.write("\t\t%d files OK\n" % (len(self._common) -
                                        len(self._failed_md5) -
                                        len(self._unreadable)))
        fp.write("\t\t%d files FAILED\n" % len(self._failed_md5))
        fp.write("\t\t%d files UNREADABLE\n" % len(self._unreadable))
        # Files only in one or the other directory
        fp.write("\nFiles only in %s (%d)\n" % (self._from_dir,len(self._only_in_from)))
        for f in self._only_in_from:
            fp.write("\t%s\n" % str(f))
        fp.write("\nFiles only in %s (%d)\n" % (self._to_dir,len(self._only_in_to)))
        for f in self._only_in_to:
            fp.write("\t%s\n" % str(f))
        # Compare checksums for files in both directories
        fp.write("\nCommon files (%d)\n" % len(self._common))
        for f in self._common:
            status = "OK"
            if f in self._failed_md5:
                status = "FAILED"
            elif f in self._unreadable:
                status = "UNREADABLE"
            fp.write("\t%s\t%s\n" % (status,f))

    def list_files(self,dirn):
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

    def check_md5(self,filen):
        """Compare MD5 sums of two copies of a file

        Calculates and compares the MD5 sums of each copy of the
        specified file in the source and target directories.

        Returns True if the MD5 sums match, False if they differ.

        """
        chksum1 = Md5sum.md5sum(os.path.join(self._from_dir,filen))
        chksum2 = Md5sum.md5sum(os.path.join(self._to_dir,filen))
        return chksum1 == chksum2

#######################################################################
# Functions
#######################################################################

# None defined

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    usage = "%prog FROM_DIR TO_DIR [ OUTPUT_FILE ]"
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
    if len(arguments) < 2 or len(arguments) > 3:
        p.error("Takes either 2 or 3 arguments: FROM_DIR, TO_DIR and optional OUTPUT_FILE")
    from_dir = arguments[0]
    if not os.path.isdir(from_dir):
        p.error("%s: directory not found" % from_dir)
    to_dir = arguments[1]
    if not os.path.isdir(from_dir):
        p.error("%s: directory not found" % to_dir)
    if len(arguments) == 3:
        output_file = arguments[2]
    else:
        output_file = None

    # Set up logging output
    logging.basicConfig(format='%(message)s')
    
    # Invoke the comparison
    comparison = Compare(from_dir,to_dir).report(output_file)
