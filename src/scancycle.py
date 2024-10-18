import logging
logger = logging.getLogger(__name__)

import numpy as np

POLARIZATIONS = ["LCP", "RCP"]
POLARIZATIONS_SPECTRA = ["LCP", "RCP"]

class ScanCycle(object):
    def __init__(self, sections, duty_cycle):
        self.duty_cycle = duty_cycle
        self.cycle_length = sum(duty_cycle.values())
        self.data = {}

        create_data_structure = False # default value

        for section in sections:

            bins = section["bins"]

            if section["type"] == "simple":
                pols = ["simple"]
                create_data_structure = True
            if section["type"] == "spectra":
                pols = POLARIZATIONS_SPECTRA
                # In the 'spectra' case, each polarization (LCP, RCP) has a separate section
                # We need to merge them into one to create a data structure similar to the "Stokes" case
                # We will consider only sections with id 0 or those which can be divided by 2 (for Position switching and Nodding case respectively)
                # The section will accomodate a spectra with a number of bins equal to bins*2 (for LCP and RCP)
                if((int(section['id'] == 0)) or (int(section['id'] % 2 == 0))):
                    create_data_structure = True
                    #bins = bins * 2
                else:
                    create_data_structure = False

            if section["type"] == "stokes":
                pols = POLARIZATIONS
                create_data_structure = True
            
            if(create_data_structure):
                #bins = section["bins"]
                self.data[section["id"]] = {}
                for pol in pols:
                    self.data[section["id"]][pol] = {}
                    for k,v in self.duty_cycle.items():
                        self.data[section["id"]][pol][k] = np.zeros(1, 
                                            dtype=[('spectrum',np.float32, (bins,)),
                                            ('samples', np.int_),
                                            ('integration', np.float64)])
        print(self.data.items())

    @property
    def sections(self):
        return list(self.data.keys())

    def add_data(self, section_id, flag, pol, data, samples, integration):
        """
        @param data: a single spectrum file containing all polarizations
        """

        self.data[section_id][pol][flag]["spectrum"] += data
        self.data[section_id][pol][flag]["samples"] += samples
        self.data[section_id][pol][flag]["integration"] += integration

        #print("Added data for: ", section_id, flag, pol, data, samples, integration)
        #print(data[5140:5145])
        #print("\n")

    def add_data_file(self, fits_file, flag="on"):
       
        #TODO: add CAL flag check when implemented in fits file
        unit_integration = fits_file["SECTION TABLE"].header["Integration"] / 1000.0
        n_feeds = set(fits_file["RF INPUTS"].data["feed"]) # get unique number of feed

        for section in fits_file["SECTION TABLE"].data:

            if section["type"] == "spectra":
                # At first, check the number of feeds: 
                # if n_feeds = 1 -> Position Switching
                # if n_feeds = 2 -> Nodding 

                if(len(n_feeds) == 1): # Position Switching

                    #if((int(section['id'] == 0)) or (int(section['id'] % 2 == 0))):
                    if((int(section['id'] == 0))):
                    
                        lcp_data = np.array(fits_file["DATA TABLE"].data["Ch%d"%(section["id"])])
                        rcp_data = np.array(fits_file["DATA TABLE"].data["Ch%d"%(int(section["id"])+1)])
                        # merge LCP and RCP data in a single spectrum of 32000 channels
                        data = np.hstack([lcp_data,rcp_data])
                        self.add_section_data(section, 
                                        flag,
                                        unit_integration,
                                        data,
                                        )

                if(len(n_feeds) == 2): # Nodding

                    # Section 0 has always the correct flag value i.e. feed 0 ON
                    if((int(section['id'] == 0))):
                    
                        try: # try to get data from the data columns relative to the section id
                            lcp_data = np.array(fits_file["DATA TABLE"].data["Ch%d"%(section["id"])])
                            rcp_data = np.array(fits_file["DATA TABLE"].data["Ch%d"%(int(section["id"])+1)])
                        except:
                            # manage the error
                            pass
                        else: # if no errors then execute the following code
                            # print('***SECTION ID and FLAG***', section['id'], flag)
                            # merge LCP and RCP data in a single spectrum of 32000 channels
                            data = np.hstack([lcp_data,rcp_data])
                            self.add_section_data(section, 
                                            flag,
                                            unit_integration,
                                            data,
                                            )


                    # The section relative to the second feed (for instance feed 6) has flag ON but in reality is OFF and must be inverted
                    # If the first feed has flag 'on' (type SIGNAL) then the second feed must have flag 'off' 
                    # If the first feed has flag 'off' (type REFERENCE) then the second feed must have flag 'on' 
                    if((int(section['id'] == 2))): # this and the next sections are referred to the second feed
                        
                        # print('********** flag **********', flag)
                        # Update the flag value for the second feed
                        if(flag != 'cal' and flag != 'sig'):                 
                            if(flag == 'on'):
                                flag = 'off'
                            else:
                                flag = 'on'
                        # print('********** new flag **********', flag)
                        try:
                            lcp_data = np.array(fits_file["DATA TABLE"].data["Ch%d"%(section["id"])])
                            rcp_data = np.array(fits_file["DATA TABLE"].data["Ch%d"%(int(section["id"])+1)])
                        except:
                            # manage the error
                            pass
                        else: # if no errors then execute the following code
                            # print('***SECTION ID and FLAG***', section['id'], flag)
                            # merge LCP and RCP data in a single spectrum of 32000 channels
                            data = np.hstack([lcp_data,rcp_data])
                            self.add_section_data(section, 
                                            flag,
                                            unit_integration,
                                            data,
                                            )

                    
            else:    

                self.add_section_data(section, 
                                    flag,
                                    unit_integration,
                                    fits_file["DATA TABLE"].data["Ch%d"%(section["id"])],
                                    )

    def add_section_data(self, section, flag, integration, data):

        if section["type"] == "simple":
            pols = ["simple"]
               
        if section["type"] == "spectra":
            pols = POLARIZATIONS_SPECTRA
               
        if section["type"] == "stokes":
            pols = POLARIZATIONS
       
        total_integration = len(data) * integration
        data_sum = data.sum(0)
       
        for i,pol in enumerate(pols):
            data_start = i * section["bins"]
            data_stop = data_start + section["bins"]
           
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

                # According to the mode (Position Switching and Nodding) get the calibration values:
                # Case Position Switching
                if(len(self.duty_cycle.keys())) == 3: 
                    if "cal" in list(data.keys()):
                        print('Executing cal averages...')
                        cal = data['cal'][0]["spectrum"] / data["cal"][0]["samples"]

                    else:
                        cal = None
                
                # Case Nodding
                if(len(self.duty_cycle.keys())) == 4: 
                    if "cal" and "sig" in list(data.keys()):
                        print('Executing sig and cal averages...')
                        cal = data['cal'][0]["spectrum"] / data["cal"][0]["samples"]
                        sig = data['sig'][0]["spectrum"] / data["sig"][0]["samples"]

                    else:
                        cal = None
                        sig = None
                
                # Nodding mode is also detected whether the flag 'sig' belongs to the list(data.keys()
                if "sig" in list(data.keys()):
                    result[s_id][pol_id] = (sig, on, off, cal)
                else:
                    result[s_id][pol_id] = (on, off, cal)
                #print("data[on][0][samples]", data["on"][0]["samples"])
                #print("data[off][0][samples]", data["off"][0]["samples"])
                #print("data[cal][0][samples]", data["cal"][0]["samples"])
                #print("Data for", s_id, pol_id)
                #print("on", on[5140:5150])
                #print("off", off[5140:5150])
                #print("cal", cal[5140:5150])
                #print("sig", sig[5140:5150])


        return result

