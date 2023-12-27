import logging
logger = logging.getLogger(__name__)

import numpy as np

POLARIZATIONS = ["LCP", "RCP"]

class ScanCycle(object):
    def __init__(self, sections, duty_cycle):
        self.duty_cycle = duty_cycle
        self.cycle_length = sum(duty_cycle.values())
        self.data = {}
        
        for section in sections:
            '''
            if section["type"] == "simple" or section["type"] == "spectra":
                pols = "simple"
                bins = section["bins"]
                print ('sec id', type(section['id']))

                self.data[section["id"]]['simple'] = {}
                
                for k,v in self.duty_cycle.items():
                    print('k',k)
                    print('section',section["id"])
                    self.data[section["id"]][pols][k] = np.zeros(1, 
                                        dtype=[('spectrum',np.float32, (bins,)),
                                        ('samples', np.int_),
                                        ('integration', np.float64)])

            else:
            ''' 
            if section["type"] == "simple" or section["type"] == "spectra":
                pols= ['simple',]
            else:
                pols = POLARIZATIONS
            bins = section["bins"]
            self.data[section["id"]] = {}

            for pol in pols:
                    print ('sec id', type(pol))

                    self.data[section["id"]][pol] = {}
                    for k,v in self.duty_cycle.items():
                        print('k',k)
                        print('section',section["id"])
 
                        self.data[section["id"]][pol][k] = np.zeros(1, 
                                        dtype=[('spectrum',np.float32, (bins,)),
                                        ('samples', np.int_),
                                        ('integration', np.float64)])

    @property
    def sections(self):
        return list(self.data.keys())

    def add_data(self, section_id, flag, pol, data, samples, integration):
        """
        @param data: a single spectrum file containing all polarizations
        """
        self.data[section_id][pol][flag]["spectrum"] +=  data
        self.data[section_id][pol][flag]["samples"] += samples
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
        print ("forma:",data.shape)

        if section["type"] == "stokes":
            print("Sezione:",section["type"])
            pols = POLARIZATIONS
            total_integration = len(data) * integration
            data_sum = data.sum(0)
            for i,pol in enumerate(pols):
                data_start = i * section["bins"]
                data_stop = data_start +section["bins"]
                print("forma data sum",data_sum.shape)
                self.add_data(section["id"],
                          flag,
                          pol,
                          data_sum[data_start:data_stop],
                          len(data),
                          total_integration)
        else:
            print("Sezione:",section["type"])
            total_integration = len(data) * integration

            pol = "simple"
            data_start = 0 
            data_stop = section["bins"]
            data_sum = data.sum(0)
            print (type(data_sum))
            print("forma data sum",data_sum.shape)

            self.add_data(section["id"],
                          flag,
                          pol,
                          data_sum[data_start:data_stop],
                          len(data),
                          total_integration)
 
    def onoffcal(self):
        result = dict()
        for s_id,section in self.data.items():
            result[s_id] = dict()
            for pol_id, data in section.items():
                on = data['on'][0]["spectrum"] / data["on"][0]["samples"]
                off = data['off'][0]["spectrum"] / data["off"][0]["samples"]
                if "cal" in list(data.keys()):
                    cal = data['cal'][0]["spectrum"] / data["cal"][0]["samples"]
                else:
                    cal = None
                result[s_id][pol_id] = (on, off, cal)
        return result

