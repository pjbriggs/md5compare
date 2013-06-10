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
import time
import Md5sum

#######################################################################
# Classes
#######################################################################

class Compare:
    """Class to compare contents of two directories
    
    """

    def __init__(self,from_dir,to_dir,
                 report_progress=False,report_every=0,
                 progress_callback=None):
        """Create a new Compare object

        Arguments:
          from_dir: path to "source" directory
          to_dir: path to "target" directory
          report_progress: if True then invoke progress_callback
            with progress messages, or write to stdout (if callback
            is not defined)
          report_every: if non-zero then send a progress update for
            every n files that are checked (if n=0 then a reasonable
            value will be set automatically)
          progress: (optional) callback function that will be
            invoked to report progress

        """
        # Store info about source ("from") and target ("to") dirs
        self._from_dir = from_dir
        self._to_dir = to_dir
        # Store progress options and callback function
        self._report_progress_flag = report_progress
        self._report_every = report_every
        self._progress_callback = progress_callback
        # Setup
        self._start_time = time.time()
        self.setup()
        # Do checksum comparison
        self.go_compare()
        self._end_time = time.time()

    def setup(self):
        """Collect lists of files for comparison

        """
        # Create sets of files in "from" and "to" directories
        self._report_progress("Collecting files for %s" % self._from_dir)
        self._from_set = set(self._list_files(self._from_dir))
        self._report_progress("Collecting files for %s" % self._to_dir)
        self._to_set = set(self._list_files(self._to_dir))
        # Lists created from subsets
        self._report_progress("Sorting files into sets")
        self._common = list(self._from_set.intersection(self._to_set))
        self._only_in_from = list(self._from_set.difference(self._to_set))
        self._only_in_to   = list(self._to_set.difference(self._from_set))
        # Sort the lists
        self._common.sort()
        self._only_in_from.sort()
        self._only_in_to.sort()        

    def go_compare(self):
        """Do the comparison

        """
        nfiles = len(self._common)
        if self._report_every < 1:
            n_mod = int(float(nfiles)/100)
        else:
            n_mod = self._report_every
        if n_mod == 0: n_mod = 1
        n = 0
        failed_md5 = []
        unreadable = []
        for f in self._common:
            n += 1
            if n%n_mod == 0:
                self._report_progress("Examining %d/%d (%s)" % (n,nfiles,f))
            try:
                if not self._check_md5(f):
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
            self._report_progress("Writing report to %s" % output_file)
            self.report(fp=open(output_file,'w'))
            return
        # Calculate numbers of files that passed, failed etc
        n_passed = len(self._common) - len(self._failed_md5) - len(self._unreadable)
        n_failed = len(self._failed_md5)
        n_unreadable = len(self._unreadable)
        n_only_in_from = len(self._only_in_from)
        n_only_in_to = len(self._only_in_to)
        # Preamble
        title_line = "Comparing contents of %s and %s" % (self._from_dir,
                                                          self._to_dir)
        fp.write("%s\n%s\n" % (title_line,"="*len(title_line)))
        fp.write("\nStart time: %s\nEnd time  : %s\n" % (time.ctime(self._start_time),
                                                         time.ctime(self._end_time)))
        # Summary
        fp.write("\nSummary\n%s\n" % ("-"*len("Summary")))
        fp.write("\t%d files only found in %s\n" % (n_only_in_from,self._from_dir))
        fp.write("\t%d files only found in %s\n" % (n_only_in_to,self._to_dir))
        fp.write("\t%d files in both\n" % len(self._common))
        fp.write("\t\t%d files OK\n" % n_passed)
        fp.write("\t\t%d files FAILED\n" % n_failed)
        fp.write("\t\t%d files UNREADABLE\n" % n_unreadable)
        # Files only in one or the other directory
        fp.write("\nFiles only in %s (%d)\n" % (self._from_dir,n_only_in_from))
        for f in self._only_in_from:
            fp.write("\t%s\n" % str(f))
        fp.write("\nFiles only in %s (%d)\n" % (self._to_dir,n_only_in_to))
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
        # Send a progress update indicating final result
        summary = ["Finished: %d OK" % n_passed]
        if n_failed > 0:
            summary.append(", %d failed" % n_failed)
        if n_unreadable > 0:
            summary.append(", %d 'bad' files" % n_unreadable)
        if n_only_in_from > 0 or n_only_in_to > 0:
            summary.append(", %d 'extra' files" % (n_only_in_from + n_only_in_to))
        self._report_progress(' '.join(summary))
        # Return status depending on whether there were problems
        if n_failed or n_unreadable or (n_only_in_from + n_only_in_to):
            return False
        else:
            return True

    def _report_progress(self,message):
        if self._report_progress_flag:
            if self._progress_callback is not None:
                self._progress_callback(message)
            else:
                print str(message)

    def _list_files(self,dirn):
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

    def _check_md5(self,filen):
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
    comparison = Compare(from_dir,to_dir,report_progress=options.progress).report(output_file)
