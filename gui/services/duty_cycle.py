import re

class DutyCycle:

    # case POSITION SWITCHING
    valid_onoff_duty_cycle_ps = re.compile("(?P<on>\d+):(?P<off>\d+):(?P<cal>\d+)",
                                    flags = re.I)
    # case NODDING                                 
    valid_onoff_duty_cycle_nd = re.compile("(?P<sig>\d+):(?P<on>\d+):(?P<off>\d+):(?P<cal>\d+)",
                                    flags = re.I)

    def __init__(self) -> None:
        
        pass

    def get_duty_cycle_size(self, rsig, sig, ref, rcal):

        duty_cycle_size = rsig + sig + ref + rcal

        return duty_cycle_size

    def parse_onoff_duty_cycle(self, duty_cycle):

        # Check the number of ':' inside the duty_cycle string
        if duty_cycle.count(':') == 2:
            m = self.valid_onoff_duty_cycle_ps.match(duty_cycle) # case PS
           
        else: 
            m = self.valid_onoff_duty_cycle_nd.match(duty_cycle) # case ND
           
        # m = valid_onoff_duty_cycle.match(duty_cycle)
        if not m:
            raise Exception("Invalid onoff sequence: %s" %(duty_cycle,))
        
        output_duty_cycle = {}
        
        for k,v in m.groupdict().items():
            output_duty_cycle[k] = int(v)
      
        return output_duty_cycle