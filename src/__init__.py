##coding=utf-8

#
#
#    Copyright (C) 2016  Marco Bartolini, bartolini@ira.inaf.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

VERSION = "0.1.0-beta"

import logging

def cmd_line():
    import argparse
    import os
    import sys

    #Adding command line options
    parser = argparse.ArgumentParser(description="Convert discos SCANs into class files")
    parser.add_argument('-d', action='store_true', help="enable debug messages",
                        dest='debug')
    parser.add_argument('-o', '--output-dir', default="classconverter",
                        dest="output_dir",
                        help="output directory name")
    parser.add_argument('source_dir', nargs='+',
                        help='directory path(s) to scans')
    parser.add_argument('-f', action='store_true', dest='force',
                        help='force override of existing files')
    parser.add_argument('--version', action='store_true', dest='show_version',
                        help='print version information and exit')

    #parsing command line arguments
    ns = parser.parse_args()
    if ns.show_version:
        print "discos2class v%s" % (VERSION,)
        sys.exit()
    #setting logger level and format
    if ns.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.INFO)
    logger = logging.getLogger("discos2class")
    logger.debug("Running with options:")
    for k,v in vars(ns).iteritems():
        logger.debug("\t%s:\t%s" % (k, str(v),))

    from discosscan import DiscosScanConverter

    if not os.path.isdir(ns.output_dir):
        logging.debug("creating directory: %s" % (ns.output_dir,))
        try:
            os.makedirs(ns.output_dir)
        except Exception, e:
            logging.warning("cannot create directory: %s" % (ns.output_dir,))
            logging.warning(e.message)
    for input_scan_directory in ns.source_dir:
        try:
            converter = DiscosScanConverter(input_scan_directory)
            converter.load_summary_info()
            converter.convert_subscans(ns.output_dir)
        except Exception, e:
            if ns.debug:
                raise
            else:
                logging.error("cannot convert scan at: %s" % (input_scan_directory,))
                logging.error(e.message)

