md5compare
==========

MD5 comparison programs for Alan Roseman's EM data.

What is required
----------------

1. A command-line "compare" program which will take a FROM directory and
   a TO directory plus the name of an output file; it will compare the
   contents of FROM and TO and report the differences (including the
   presence of any additional files in TO which are not in FROM). The
   report will be written to the output file.

2. A GUI tool built on the "compare" program which allows the user to
   select the FROM and TO directories and the output file using standard
   file-browsing widgets, run the comparison and then report the result. It
   should also keep its own log that can be examined at a later date.

The GUI should also report and update status while it is in progress (with
a big directory it might run for about an hour or more).

In both cases the tools need to clearly report:

 - that the verification actually completed
 - the status of each file compared and which had problems
