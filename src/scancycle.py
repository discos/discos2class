import logging
logger = logging.getLogger(__name__)

import numpy as np

POLARIZATIONS = ["LCP", "RCP"]

class ScanCycle(object):
    def __init__(self, sections, geometry):
        self.geometry = geometry
        self.cycle_length = sum(geometry.values())
        self.data = {}
        for section in sections:
            if section["type"] == "simple":
                pols = ["simple"]
            else:
                pols = POLARIZATIONS
            bins = section["bins"]
            self.data[section["id"]] = {}
            for pol in pols:
                self.data[section["id"]][pol] = {}
                for k,v in self.geometry.iteritems():
                    self.data[section["id"]][pol][k] = np.zeros(1, 
                                        dtype=[('spectrum',np.float32, (bins,)),
                                        ('samples', np.int),
                                        ('integration', np.float64)])

    @property
    def sections(self):
        return self.data.keys()

    def add_data(self, section_id, flag, pol, data, integration):
        """
        @param data: a single spectrum file containing all polarizations
        """
        self.data[section_id][pol][flag]["spectrum"] += data
        self.data[section_id][pol][flag]["samples"] += 1
        self.data[section_id][pol][flag]["integration"] += integration

    def add_data_file(self, fits_file, flag="on"):
        #TODO: add CAL flag check when implemented in fits file
        unit_integration = fits_file["SECTION TABLE"].header["Integration"] / 1000.0
        for section in fits_file["SECTION TABLE"].data:
            self.add_section_data(section, 
                                  flag,
                                  unit_integration,
                                  fits_file["DATA TABLE"].data["Ch%d"%(section["id"])],
                                  )

    def add_section_data(self, section, flag, integration, data):
        if section["type"] == "stokes":
            pols = POLARIZATIONS
        else:
            pols = ["simple"]
        total_integration = len(data) * integration
        data_sum = data.sum(0)
        for i,pol in enumerate(pols):
            data_start = i * section["bins"]
            data_stop = data_start + section["bins"]
            self.add_data(section["id"],
                          flag,
                          pol,
                          data_sum[data_start:data_stop],
                          total_integration)

    def onoffcal(self):
        result = dict()
        for s_id,section in self.data.iteritems():
            result[s_id] = dict()
            for pol_id, data in section.iteritems():
                on = data['on'][0]["spectrum"] / data["on"][0]["samples"]
                off = data['off'][0]["spectrum"] / data["off"][0]["samples"]
                if "cal" in data.keys():
                    cal = data['cal'][0]["spectrum"] / data["cal"][0]["samples"]
                else:
                    cal = None
                result[s_id][pol_id] = (on, off, cal)
        return result

