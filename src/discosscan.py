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
import sys

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
DATA_EXTENSION = ".fits"

class DiscosScanException(Exception):
    def __init__(self, message):
        super(DiscosScanException, self).__init__(message)

class DiscosScanConverter(object):
    def __init__(self, path=None):
        self.scan_path = path
        self.got_summary = False
        self.file_class_out = pyclassfiller.ClassFileOut()
        self.subscans = []

    def load_subscans(self):
        for subscan_file in os.listdir(self.scan_path):
            ext = os.path.splitext(subscan_file)[-1]
            if not subscan_file == SUMMARY and ext == DATA_EXTENSION:
                subscan_path = os.path.join(self.scan_path, subscan_file)
                with fits.open(subscan_path) as subscan:
                    self.subscans.append((subscan_path, 
                                          subscan[0].header["SIGNAL"],
                                          Time(subscan["DATA TABLE"].data["time"][0],
                                               format = "mjd",
                                               scale = "utc")
                                         ))
        self.subscans.sort(key=lambda(x):x[2])
        logging.debug("ordered files: %s" % (str([filename for filename,_,_ in
                                                  self.subscans]),))

    def convert_subscans(self, dest_dir=None):
        if not dest_dir:
            dest_dir = self.scan_path
        dest_subdir_name = os.path.normpath(self.scan_path).split(os.path.sep)[-1]
        dest_subdir_name += "_class"
        dest_subdir = os.path.join(dest_dir, dest_subdir_name)
        try:
            os.makedirs(dest_subdir)
        except Exception, e:
            logging.error("output directory exists: %s" % (dest_subdir,))
            sys.exit(1)
        for subscan_file, signal, subscan_time in self.subscans:
            logging.debug("convert subscan file: %s" % (subscan_file,))
            self.convert_subscan(subscan_file, dest_subdir)

    def convert_subscan(self, subscan_file, dest_dir):
        with fits.open(subscan_file) as subscan:
            rf_inputs = subscan["RF INPUTS"].data
            sections = subscan["SECTION TABLE"].data
            for rf_index, rf_input in enumerate(rf_inputs):
                #search for section
                found_section = False
                section = None
                for s in sections:
                    if rf_input["section"] == s["id"]:
                        found_section = True
                        section = s
                if not found_section:
                    raise DiscosScanException("cannot find section %d" %\
                                              (rf_input["section"],))
                dest_file_name = FILE_PREFIX + \
                                 "_FEED%d" % (rf_input["feed"],) +\
                                 "_IF%d" % (rf_input["ifChain"],) +\
                                 "_SEC%d" % (section["id"],) +\
                                 "_%s" % (rf_input["polarization"],) +\
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
                self.write_observations(subscan, rf_input, rf_index, section)
                self.file_class_out.close()

    def write_observations(self, subscan, rf_input, rf_index, section):
        for data in subscan["DATA TABLE"].data:
            location = (subscan[0].header["SiteLongitude"] * u.rad,
                        subscan[0].header["SiteLatitude"] * u.rad)
            location = (location[0].to(u.deg),
                        location[1].to(u.deg))
            observation_time = Time(data["time"],
                                    format = "mjd",
                                    scale = "utc", 
                                    location = location)
            now_time = Time(datetime.utcnow(), scale="utc")
            bandwidth = rf_input["bandwidth"]
            nchan = section["bins"]
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
            obs.head.gen.az = data["az"]
            obs.head.gen.el = data["el"]
            obs.head.gen.tau = 0.
            #FIXME: should we read antenna temperature?
            obs.head.gen.tsys = 0. # ANTENNA TEMP TABLE is broken with XARCOS
            obs.head.gen.time = subscan["SECTION TABLE"].header["Integration"] / 1000.
            obs.head.gen.xunit = code.xunit.velo  # Unused

            obs.head.pos.sourc = subscan[0].header["SOURCE"]
            obs.head.pos.epoch = 2000.0
            obs.head.pos.lam = data["raj2000"]
            obs.head.pos.bet = data["decj2000"]
            obs.head.pos.lamof = 0. #FIXME: leggere
            obs.head.pos.betof = 0. #FIXME: leggere
            obs.head.pos.proj = code.proj.none
            obs.head.pos.sl0p = 0. #FIXME: ?	
            obs.head.pos.sb0p = 0. #FIXME: ?	
            obs.head.pos.sk0p = 0. #FIXME: ?

            obs.head.spe.restf = self.summary["rest_frequency"]
            obs.head.spe.nchan = nchan
            obs.head.spe.rchan = nchan / 2 + 1
            obs.head.spe.fres = bandwidth / float(nchan)
            obs.head.spe.foff = offsetFrequencyAt0
            obs.head.spe.vres = -1. # FIXME: da calcolare come fits '11cd2r'
            obs.head.spe.voff = self.summary["velocity"]["vrad"]
            obs.head.spe.bad = 0.
            obs.head.spe.image = 0.
            #nel fits abbiamo la frequenfa topocentrica calcolata
            # quindi immagino che anche la velocita' sia uguale
            obs.head.spe.vtype = code.velo.earth 
            obs.head.spe.doppler = 0. # FIXME: calcolare
            obs.head.spe.line = "LINE"

            starting_bin = (rf_index % 2) * nchan
            ending_bin = starting_bin + nchan
            obs.datay = data["Ch%d" % (section["id"],)]\
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
            rest_frequency = summary_header["RESTFREQ1"]
            #rest_frequency = [summary_header[ri] # * u.MHz
            #                  for ri in summary_header.keys() 
            #                  if ri.startswith("RESTFREQ")]
            velocity = dict(vrad = summary_header["VRAD"],
                            vdef = summary_header["VDEF"],
                            vframe = summary_header["VFRAME"])
        self.summary = (dict(rest_frequency = rest_frequency,
                             velocity = velocity))
        self.got_summary = True


