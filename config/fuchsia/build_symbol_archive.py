#!/usr/bin/env python
#
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Creates a compressed archive of binary symbols derived from the unstripped
executables and libraries cataloged by "ids.txt"."""

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile


def main(args):
  parser = argparse.ArgumentParser()
  parser.add_argument('ids_txt', type=str, nargs=1,
                      help='Path to the ids.txt file.')
  parser.add_argument('output_tarball', nargs=1, type=str,
                      help='Path which the tarball will be written to.')
  parser.add_argument('--eu-strip', required=True, type=str,
                      help='Path to the the eu-strip tool.')
  args = parser.parse_args(args)


  stripped_tempfile = tempfile.NamedTemporaryFile()

  ids_txt = args.ids_txt[0]
  build_ids_archive = tarfile.open(args.output_tarball[0], 'w:bz2')
  for line in open(ids_txt, 'r'):
    # debug_tempfile: The path which debug symbols will be written to.
    # stripped_tempfile: The path which the stripped executable will be written
    #                    to. This file is ignored and immediately deleted.
    with tempfile.NamedTemporaryFile() as debug_tempfile, \
         tempfile.NamedTemporaryFile() as stripped_tempfile:
      build_id, binary_path = line.strip().split(' ')
      binary_abspath = os.path.abspath(
          os.path.join(os.path.dirname(ids_txt), binary_path))

      # Extract debugging symbols from the binary into their own file.
      # The stripped executable binary is written to |debug_tempfile| and
      # deleted. Writing to /dev/null would be preferable, but eu-strip
      # disallows writing output to /dev/null.
      subprocess.check_call([args.eu_strip, '-g', binary_abspath,
                             '-f', debug_tempfile.name,
                             '-o', stripped_tempfile.name])

      # An empty result means that the source binary (most likely a prebuilt)
      # didn't have debugging data to begin with.
      if os.path.getsize(debug_tempfile.name) == 0:
        continue

      # Archive the debugging symbols, placing them in a hierarchy keyed to the
      # GNU build ID. The symbols reside in directories whose names are the
      # first two characters of the build ID, with the symbol files themselves
      # named after the remaining characters of the build ID. So, a symbol file
      # with the build ID "deadbeef" would be located at the path 'de/adbeef'.
      build_ids_archive.add(debug_tempfile.name,
                            '%s/%s' % (build_id[:2], build_id[2:]))


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
