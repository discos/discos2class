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

import os
import logging
from datetime import datetime

import numpy as np 

from astropy.io import fits
from astropy import units as u
from astropy.time import Time

import pyclassfiller
from pyclassfiller import code

SUMMARY = "summary.fits"
STOKES = "stokes"
CLIGHT = 299793e3
FILE_PREFIX = "class"

class DiscosScanException(Exception):
    def __init__(self, message):
        super(DiscosScanException, self).__init__(message)

class DiscosScanConverter(object):

    def __init__(self, path=None):
        self.scan_path = path
        self.got_summary = False
        self.file_class_out = pyclassfiller.ClassFileOut()

    def convert_subscans(self, dest_dir=None):
        if not dest_dir:
            dest_dir = self.scan_path
        dest_subdir_name = os.path.normpath(self.scan_path).split(os.path.sep)[-1]
        dest_subdir_name += "_class"
        dest_subdir = os.path.join(dest_dir, dest_subdir_name)
        try:
            os.makedirs(dest_subdir)
        except Exception, e:
            logging.warning("cannot create directory: %s" % (dest_subdir,))
            logging.warning(e.message)
        subscan_files = [os.path.join(self.scan_path, f) 
                         for f in os.listdir(self.scan_path)
                         if not f == SUMMARY and
                         f.endswith(".fits")]
        #sort by creation date
        sorted(subscan_files, key=lambda(x):os.stat(x).st_ctime)
        for subscan_file in subscan_files:
            logging.debug("convert subscan file: %s" % (subscan_file,))
            self.convert_subscan(subscan_file, dest_subdir)

    def convert_subscan(self, subscan_file, dest_dir):
        with fits.open(subscan_file) as subscan:
            for section in subscan["SECTION TABLE"].data:
                logging.debug("loading section: %s" % (str(section["id"]),))
                if section["type"] == "stokes":
                    npols = 4
                else:
                    npols = 1
                for pol in range(npols):
                    dest_file_name = FILE_PREFIX + \
                                     "_sec" + str(section["id"]) + \
                                     "_pol" + str(pol) + \
                                     ".nmb"
                    dest_file_path = os.path.join(dest_dir, dest_file_name)
                    logging.debug("open output file: %s" % (dest_file_name,))
                    try:
                        self.file_class_out.open(dest_file_path, 
                                                 new = False,
                                                 over = False,
                                                 size = 999999,
                                                 single = True)
                        logging.debug("opened successfully in append mode")
                    except:
                        self.file_class_out.open(dest_file_path, 
                                                 new = True,
                                                 over = False,
                                                 size = 999999,
                                                 single = True)
                        logging.debug("opened successfully in create mode")
                    self.write_observations(section["id"], pol, subscan)
                    self.file_class_out.close()

    def write_observations(self, section, pol, subscan):
        for ndata in xrange(len(subscan["DATA TABLE"].data)):
            logging.debug("section: %s pol: %s ndata %s" % (
                                                           str(section),
                                                           str(pol),
                                                           str(ndata)))
            location = (subscan[0].header["SiteLongitude"] * u.rad,
                        subscan[0].header["SiteLatitude"] * u.rad)
            location = (location[0].to(u.deg),
                        location[1].to(u.deg))
            observation_time = Time(subscan["DATA TABLE"].data["time"][ndata],
                                    format = "mjd",
                                    scale = "utc", 
                                    location = location)
            now_time = Time(datetime.utcnow(), scale="utc")
            bandwidth = subscan["SECTION TABLE"].data["SampleRate"][section] / 2.0
            nchan = subscan["SECTION TABLE"].data["bins"][section]
            freq_resolution = bandwidth / float(nchan)
            offsetFrequencyAt0 = 0
            if nchan % 2 == 0:
                central_channel = nchan / 2
                offsetFrequencyAt0 = -freq_resolution / 2.
            else:
                central_channel = (nchan / 2) + 1
                offsetFrequencyAt0 = 0
            obs = pyclassfiller.ClassObservation()
            obs.head.presec[:]            = False  # Disable all sections except...
            obs.head.presec[code.sec.gen] = True  # General
            obs.head.presec[code.sec.pos] = True  # Position
            obs.head.presec[code.sec.spe] = True  # Spectral observatins  Activate always spectral section to include the name of the line 
            obs.head.gen.num = 0
            obs.head.gen.ver = 0
            obs.head.gen.teles = subscan[0].header["ANTENNA"]
            obs.head.gen.dobs = int(observation_time.mjd) - 60549
            obs.head.gen.dred = int(now_time.mjd) - 60549
            obs.head.gen.typec = code.coord.equ
            obs.head.gen.kind = code.kind.spec
            obs.head.gen.qual = code.qual.unknown
            obs.head.gen.scan = subscan[0].header["SCANID"]
            obs.head.gen.subscan = subscan[0].header["SubScanID"]
            obs.head.gen.ut = (observation_time.mjd - int(observation_time.mjd)) * np.pi * 2
            #FIXME: get sidereal time right
            #obs.head.gen.st = observation_time.sidereal_time()
            obs.head.gen.st = 0.
            obs.head.gen.az = subscan["DATA TABLE"].data["az"][ndata]
            obs.head.gen.el = subscan["DATA TABLE"].data["el"][ndata]
            obs.head.gen.tau = 0.
            #FIXME: should we read antenna temperature?
            obs.head.gen.tsys = 0. # file[5].data["Ch.."][i][0,1]
            obs.head.gen.time = subscan["SECTION TABLE"].header["Integration"] / 1000.
            obs.head.gen.xunit = code.xunit.velo  # Unused

            obs.head.pos.sourc = subscan[0].header["SOURCE"]
            obs.head.pos.epoch = 2000.0
            obs.head.pos.lam = subscan["DATA TABLE"].data["raj2000"][ndata]
            obs.head.pos.bet = subscan["DATA TABLE"].data["decj2000"][ndata]
            obs.head.pos.lamof = 0. #FIXME: leggere
            obs.head.pos.betof = 0. #FIXME: leggere
            obs.head.pos.proj = code.proj.none
            obs.head.pos.sl0p = 0. #FIXME: ?	
            obs.head.pos.sb0p = 0. #FIXME: ?	
            obs.head.pos.sk0p = 0. #FIXME: ?	

            obs.head.spe.restf = self.summary[0][section]
            obs.head.spe.nchan = subscan["SECTION TABLE"].data["bins"][section]
            obs.head.spe.rchan = subscan["SECTION TABLE"].data["bins"][section] / 2 + 1
            obs.head.spe.fres = bandwidth / float(nchan)
            obs.head.spe.foff = offsetFrequencyAt0
            obs.head.spe.vres = -1. # FIXME: da calcolare come fits '11cd2r'
            obs.head.spe.voff = 0. #FIXME: ricavare da vlsr (fits '1vsou2r')
            obs.head.spe.bad = 0.
            obs.head.spe.image = 0.
            obs.head.spe.vtype = code.velo.obs # FIXME: switch case
            obs.head.spe.doppler = 0. # FIXME: calcolare
            obs.head.spe.line = "LINE"

            starting_bin = pol * nchan
            ending_bin = starting_bin + nchan
            obs.datay = subscan["DATA TABLE"]\
                        .data["Ch%d" % (section,)][ndata]\
                        [starting_bin:ending_bin]\
                        .astype(np.float32)

            obs.write()

    def load_summary_info(self, summary_file_path=None):
        if not summary_file_path:
            dir_name = self.scan_path
        summary_file_path = os.path.join(dir_name, SUMMARY)
        if not os.path.exists(summary_file_path):
            raise DiscosScanException("scan %s does not conatain a %s" % (dir_name,
                                                                          SUMMARY))
        with fits.open(summary_file_path) as summary_file:
            logging.debug("loading summary from %s" % (summary_file_path,))
            summary_header = summary_file[0].header
            rest_frequency = [summary_header[ri] # * u.MHz
                              for ri in summary_header.keys() 
                              if ri.startswith("RESTFREQ")]
            velocity = dict(vrad = summary_header["VRAD"],
                            vdef = summary_header["VDEF"],
                            vframe = summary_header["VFRAME"])
        self.summary = (rest_frequency, velocity)
        self.got_summary = True


