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
import re

valid_onoff_geometry = re.compile("(?P<on>\d+)on(?P<off>\d+)off(?P<cal>\d+)cal",
                                 flags = re.I)


def parse_onoff_geometry(geometry):
    m = valid_onoff_geometry.match(geometry)
    if not m:
        raise Exception("Invalid onoff sequence: %s" %(geometry,))
    output_geometry = {}
    for k,v in m.groupdict().iteritems():
        output_geometry[k] = int(v)
    logging.debug("parsed geometry: %s" % (str(output_geometry),))
    return output_geometry


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
    parser.add_argument('-g', '--geometry', default="4on4off2cal",
                        dest="geometry",
                        help="scan geometry as \"<n>on<m>off<c>cal\" elements\
                        must be all presente but can be zeroes.")
    parser.add_argument('-s', '--skip-calibration', action='store_true',
                        default=False, dest="skip_calibration",
                        help="skip kelvin calibration and computes only \
                              ((on - off) / off) ignoring CAL signal")
    parser.add_argument('source_dir', nargs='+',
                        help='directory path(s) to scans')
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
    geometry = parse_onoff_geometry(ns.geometry)
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
    for input_scan_directory in ns.source_dir:
        try:
            converter = DiscosScanConverter(input_scan_directory, geometry,
                                            ns.skip_calibration)
            converter.load_subscans()
            converter.load_summary_info()
            converter.convert_subscans(ns.output_dir)
        except Exception, e:
            if ns.debug:
                raise
            else:
                logging.error("cannot convert scan at: %s" % (input_scan_directory,))
                logging.error(e.message)

