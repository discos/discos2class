import configparser
import argparse
import math
import os
import time
import subprocess 
import sys

from astropy.io import fits
from astropy.time import Time
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QProgressBar
from PyQt5.QtCore import pyqtSignal, QDateTime, QThread, QTimer, QTime
from PyQt5.uic import loadUi
from tkinter import filedialog

# VERSION DATE: 09-02-2026

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
# Add the subfolder to sys.path
sys.path.append(os.path.join(SCRIPT_DIR, 'src'))
# The previous line allows to call modules without specifying the subfolders where they are located

from duty_cycle import DutyCycle
from file_services import FileServices


class CheckWorkerThread(QThread):

    DATA_EXTENSION = '.fits'
    subscans = [] # Each row conatins scan information about path, signal type and timestamp data 

    # Signal to notify the main thread to disable/enable the button in the interface
    update_button_signal = pyqtSignal(bool)
    # Signal to notify the main thread (UI) to update the console (QListView) in the interface 
    update_console_lv_signal = pyqtSignal(str, QColor)
    # Signal to notify the main thread (UI) to update the progressbar range values
    update_check_pb_range = pyqtSignal(QProgressBar, int, int)
    # Signal to notify the main thread (UI) to update the progressbar current value
    update_check_pb_value = pyqtSignal(QProgressBar, int)
    # Signal to notify the main thread (UI) with the result of the verify process
    result_signal = pyqtSignal(bool, object, int, int)

    def __init__(self, pb, root_folder, project_id_folder, folder_0, folder_1, folders_1, all_folders_selected, duty_cycle, duty_cycle_flags, duty_cycle_size, mode, skip_calibration=True, parent=None):
        super().__init__(parent)
        # Store the parameters passed to the thread
        self.pb = pb
        self.root_folder = root_folder
        self.project_id_folder = project_id_folder
        self.folder_0 = folder_0
        self.all_folders_selected = all_folders_selected
        self.duty_cycle = duty_cycle
        self.duty_cycle_flags = duty_cycle_flags
        self.duty_cycle_size = duty_cycle_size
        self.folders_1 = folders_1
        self.folder_1 = folder_1
        self.mode = mode
        self.skip_calibration = skip_calibration
        self.subscans = []

    def get_len_subscans(self):

        return len(self.subscans)

    def run(self):

        # Disable the button when the thread starts
        self.update_console_lv_signal.emit("Duty cycle check started. Please wait...", QColor("black")) 

        folders_to_scan = []

        if(self.all_folders_selected):
            # Loop through the items in the combo box
            for i in range(self.folders_1.count()):
                folders_to_scan.append(self.folders_1.itemText(i))
        
        else:

            folders_to_scan.append(self.folder_1)

        for f in range(len(folders_to_scan)): 

            input_scan_directory = self.root_folder + '/' + self.project_id_folder + '/' + self.folder_0 + '/' + folders_to_scan[f]

            self.update_button_signal.emit(False)  

            error = False
            check_result = [None]*3 # it contains the result of the duty cycle check 

            self.subscans.clear()

            self.update_console_lv_signal.emit("Checking SOURCE FOLDER: " + folders_to_scan[f], QColor("black")) 
            
            # Get useful information relative to each scan contained in the selected source folder
            for subscan_file in os.listdir(input_scan_directory):

                ext = os.path.splitext(subscan_file)[-1]

                if not subscan_file.lower().startswith('sum') and ext == self.DATA_EXTENSION:
                    subscan_path = os.path.join(input_scan_directory, subscan_file)

                    with fits.open(subscan_path) as subscan:
                        self.subscans.append((subscan_path, 
                                        subscan[0].header["SIGNAL"],
                                        Time(subscan["DATA TABLE"].data["time"][0],
                                            format = "mjd",
                                            scale = "utc")
                    ))

            # Before sorting the subscans in time, the backend name must be retrieved
            # Backend name can be retrieved in two ways: [A] from the summary dict or [B] from the file name
            # [A] self.backend = summary_header["BackendName"] or self.backend_name = summary_header["BackendName"][:3]
            # [B] If the file name contains the substr "FEED_" then the backend is "skarab", otherwise "sardara"
            if("FEED_" in str(self.subscans[0][0])): # from "load_subscans" first index is the item number in the list, second index the value [0]=file name, [1] signal flag, [2]=time
                self.backend_name = "ska"
            else:
                self.backend_name = "sar"

            if(self.backend_name == "ska" and self.mode == "NODDING"):
                # subscans should be sorted rather by internal time stamp as correct recording time (can differ from the disk rec time)
                # check this out once testing with real skarab data -> self.subscans.sort(key=lambda x:x[2])
                self.subscans.sort()
                #for i in range(len(self.subscans)):
                #    print(self.subscans[i][0])
                tmp_list = []
                # The Skarab duty_cycle_size is double than the Sardara one since feeds files are recorded independently 
                duty_cycle_size_sk = self.duty_cycle_size*2 # case Nodding [1:6:6:1]=14 *2 feeds
                cycles = int(len(self.subscans)/duty_cycle_size_sk)

                tmp_list = self.subscans[1::2] # extracts and copy all items with odd indexes
                del self.subscans[1::2] # del all items with odd indexes from the original list

                # Create blocks in the original list by adding all even items in the original list
                for i in range(0, cycles):
                    for j in range(int(i*duty_cycle_size_sk/2), int(i*duty_cycle_size_sk/2) + int(duty_cycle_size_sk/2)):
                        self.subscans.insert(j + int(i*duty_cycle_size_sk/2) + int(duty_cycle_size_sk/2), tmp_list[j])

            else:
                
                #order file names by internal data timestamp
                self.subscans.sort(key=lambda x:x[2])
            
            # Order fits file names by internal data timestamp
            # subscans.sort(key=lambda x:x[2])

            self.update_check_pb_range.emit(self.pb, 0, len(self.subscans)) 
            
            j = 0 # duty_cycle index
            d = 0 # duty_cycle current number
            
            # Start fits file and duty cycle comparison
            for i in range(len(self.subscans)):

                self.update_check_pb_value.emit(self.pb, int(i)+1)
                #self.verify_pb_sl.setValue(i+1)
                time.sleep(0.01)
            
                if(self.subscans[i][1] != self.duty_cycle_flags[j]): # in case of mismatch
                
                    error = True
                    filename_err = self.subscans[i][0]

                    check_result[0] = error
                    #check_result[1] = d
                    check_result[1] = math.floor(i/len(self.subscans))
                    check_result[2] = filename_err

                    f = len(folders_to_scan)
                    
                    break
                
                else:

                    error = False

                j = j + 1
                
                if(j == len(self.duty_cycle_flags)):

                    j = 0
                    d = d + 1

            self.update_button_signal.emit(True) 

            # Comunicate to the main thread (UI) the result of the verification process
            self.result_signal.emit(error, check_result, len(self.subscans), self.duty_cycle_size)     



class ConvertWorkerThread(QThread):

    # Signal to send data back to the main thread
    result_signal = pyqtSignal(bool)
    progress_bar_value_signal = pyqtSignal(QProgressBar, int)
    timer_start_signal = pyqtSignal()
    timer_stop_signal = pyqtSignal()

    p_returncode = 0 # a variable containing the processing code error, if any
    p_stderr = ""
    p_stdout = ""
    p_error = False

    def __init__(self, index, cmd, pb, parent=None):
        super().__init__(parent)
        self.index = index
        self.cmd = cmd
        self.pb = pb
        self.progress_timer = False

    
    
    def run(self):

        # Start the task
        self.timer_start_signal.emit()
        self.exec_cmd(self.cmd)
        
        # result = f"Task {self.index} done"
        
        # Emit the result back to the main thread
        self.timer_stop_signal.emit()
        self.result_signal.emit(self.p_error)

    
    
    def exec_cmd(self, executable_command):

        p = subprocess.Popen([executable_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
       
        # To capture the error message:
        # stdout = normal output
        # stderr = error output
        stdout, stderr = p.communicate()
    
        if p.returncode != 0:

            self.p_returncode = p.returncode
            self.p_stderr = stderr.decode()
            self.p_stdout = stdout.decode()
            self.p_error = True

        else:

            self.p_error = False



class MainUI(QMainWindow):

    DATA_EXTENSION = '.fits'
    subscans = [] # Each row conatins scan information about path, signal type and timestamp data 

    # Signal to notify the main thread to disable/enable the button in the interface
    update_button_signal = pyqtSignal(bool)
    # Signal to notify the main thread (UI) to update the console (QListView) in the interface 
    update_console_lv_signal = pyqtSignal(str, QColor)
    # Signal to notify the main thread (UI) to update the progressbar range values
    update_progressbar_range = pyqtSignal(int, int)
    # Signal to notify the main thread (UI) to update the progressbar current value
    update_progressbar_value = pyqtSignal(int)
    # Signal to notify the main thread (UI) with the result of the verify process
    result_signal = pyqtSignal(bool, object, int, int)
    # Signal to notify the main thread (UI) to update the QListView messages

    p_returncode = 0 # a variable containing the processing code error, if any
    p_stderr = ""
    p_stdout = ""
    progress_timer = False
    scan_cycles = [] # an array containing the number of scan cycles per each folder
    
    # List definitions
    # If you want to add a TEST item which points to data in the home02 folder then uncomment the following line
    # Next, add the home02 full-path of data as third item in the list of paths inside the config.ini file 
    # SERVER_BACKEND = ['SARDARA_BKD', 'SKARAB_BKD', 'TEST']
    SERVER_BACKEND = ['SARDARA_BKD', 'SKARAB_BKD']
    SERVER_PING = ['192.168.200.216', '192.168.203.36', '192.168.200.216']
    DUTY_CYCLE_VALUES = ['0','1','2','3','4','5','6','7','8','9']
    MODE_TYPE = ['POSITION SWITCHING', 'NODDING']
    COMBO_MSGs = ['NOT AVAILABLE'] 


    # path_to_spectral_line_data = ["/roach2_nuraghe/data/", "discos-archive/data"] # index connected to the backend chosen    

    def __init__(self):
        super(MainUI, self).__init__()

        loadUi("d2c_gui_v2_0.ui", self)

        # Create the parser
        parser = argparse.ArgumentParser(description="Run the script with optional debug mode")
        # Add the -d / --debug option
        parser.add_argument('-d', '--debug', action='store_true', help="Enable debug mode") # if '-d' then store 'True' value in args
        # Parse command line arguments
        args = parser.parse_args()
        # Check if the debug flag is set and print accordingly. If so all projects id are displayed in the combo box otherwise only that referred to the username is loaded
        self.debug_on = None

        if args.debug:
            print("DEBUG ON")
            self.debug_on = True
        else:
            print("DEBUG OFF")
            self.debug_on = False




        # Get the current working directory (the directory where the script is run from)
        # current_directory = os.getcwd()
        # print("Current working directory:", current_directory)
        
        # Get the directory where the script is located
        self.script_directory = os.path.dirname(os.path.realpath(__file__))
        print("Script is located at:", self.script_directory)
       
        # Check if the config.ini file exists otherwise initialize it. Retrieve the paths of the mounted drives
        self.path_to_spectral_line_data = self.check_config_exists(self.script_directory, 'config.ini')
        




        # Set the fixed size of the window (width, height)
        self.setFixedSize(1212, 747)  # Set the size to 800x600 pixels

        self.converter_results = None
        self.n_subscans = 0 # subscans per folder

        self.current_index = 0  # Index to track the thread number

        self.projects_id = []
        self.folders_level0 = []
        self.folders_level1 = []

        self.destination_folder = ""

        self.duty_cycle = DutyCycle()
        self.file_services = FileServices()

        # Create a QTimer to call the update_time function every 10 seconds (10000 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress_bar_timer)
        # Initial state of the timer
        self.timer_running = False
        self.timer_interval = 1000  # Timer interval set to 10 seconds

        # Buttons settings
        self.check_btn.setEnabled(False)
        self.start_btn.setEnabled(False)

        # Itialize progress bar values
        self.update_progress_bar_value(self.check_pb, 0)
        self.update_progress_bar_value(self.start_pb, 0)

        # Adding combobox drop down list values
        self.backend_cmb.addItems(self.SERVER_BACKEND)
        self.mode_cmb.addItems(self.MODE_TYPE)
        self.refsig_cmb.addItems(self.DUTY_CYCLE_VALUES)
        self.signal_cmb.addItems(self.DUTY_CYCLE_VALUES)
        self.ref_cmb.addItems(self.DUTY_CYCLE_VALUES)
        self.refcal_cmb.addItems(self.DUTY_CYCLE_VALUES)

        # Setting max number visible items in a combobox dropdown list
        self.folder0_cmb.setMaxVisibleItems(5) 
        self.folder1_cmb.setMaxVisibleItems(5) 
        self.project_id_cmb.setMaxVisibleItems(5) 
        self.refsig_cmb.setMaxVisibleItems(5) 
        self.signal_cmb.setMaxVisibleItems(5) 
        self.ref_cmb.setMaxVisibleItems(5) 
        self.refcal_cmb.setMaxVisibleItems(5) 

        # Load all projects id related to the path_to_spectral_line_data and all relative folders (level 0 and 1)
        self.update_projects_id(self.path_to_spectral_line_data[self.backend_cmb.currentIndex()])

        # Adding actions to comboboxes  
        self.project_id_cmb.activated.connect(self.update_folders_level0)
        self.folder0_cmb.activated.connect(self.update_folders_level1)
        self.mode_cmb.activated.connect(lambda: self.enable_nodding(True) if self.mode_cmb.currentText()==self.MODE_TYPE[1] else self.enable_nodding(False))
        self.refsig_cmb.activated.connect(self.enable_check_btn)
        self.signal_cmb.activated.connect(self.enable_check_btn)
        self.ref_cmb.activated.connect(self.enable_check_btn)
        self.refcal_cmb.activated.connect(self.enable_check_btn)
        #self.refsig_cmb_sl.activated.connect(lambda: self.enableCheckBtn(True) if self.getDutyCycleSize() > 0 else self.enableVeryfyBtn())        
        self.folder1_cmb.currentIndexChanged.connect(lambda: self.start_btn.setEnabled(False))
        self.backend_cmb.currentIndexChanged.connect(lambda: self.check_server(self.SERVER_PING[self.backend_cmb.currentIndex()]))
       
        # Buttons actions
        self.check_btn.clicked.connect(self.check_data)
        self.start_btn.clicked.connect(self.convert_data)
        self.dest_btn.clicked.connect(self.get_dest_folder)
        self.update_btn.clicked.connect(lambda: self.update_projects_id(self.path_to_spectral_line_data[self.backend_cmb.currentIndex()]))
        # Check Boxes actions
        self.all_folders_cb.clicked.connect(lambda: self.start_btn.setEnabled(False))

        # Initialize Position Switching
        self.enable_nodding(False)

        # Initialize the QListView
        # Create a standard item model to populate the QListView
        self.model = QStandardItemModel()
        self.console_lv.setModel(self.model)

        # Connect a signal to the console QListView of the UI
        self.update_console_lv_signal.connect(self.update_console_lv)
     
        # Get the current date in ddMMyyyy format
        current_date = QDateTime.currentDateTime().toString("dd-MM-yyyy")
        # Get the current time (you can also adjust the format if you want to include time)
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
        # Get the current date and time
        # current_datetime = QDateTime.currentDateTime().toString(Qt.DefaultLocaleLongDate)
        # Create a QStandardItem with the current date and time
        init_msg = f"[{current_date} - {current_time}]: Welcome to the D2C-GUI CONVERTER!"
        init_date_time_item = QStandardItem(init_msg)
        # Add the item to the model (which updates the QListView)
        self.model.appendRow(init_date_time_item)

    
    def check_config_exists(self, app_path, filename_ini):

        paths = None
        
        full_path_ini = app_path + '/' + filename_ini
        # if config.ini exists then load the mounted drives, otherwise create the config.ini with the list of mounted drives [it should be one drive per backend]
        
        if os.path.exists(full_path_ini):
            
            print(f"The file '{full_path_ini}' exists. Retrieving mounted drives...")
            # Read out the mounted drives from the config.ini file
            # Create a ConfigParser object
            config = configparser.ConfigParser()
            # Read the configuration file
            config.read(full_path_ini)
            # Get the comma-separated string of paths under the 'Paths' section
            paths_str = config.get('Paths', 'PATH')
            # Split the string into a list of paths
            paths = paths_str.split(',')
        
        else:
            
            paths = ["/roach2_nuraghe/data/", "/discos-archive/data/"] 

            print(f"The file '{full_path_ini}' does not exist. Initialization started...")
            # config.ini initialization
            # Create a ConfigParser object
            config = configparser.ConfigParser()
            # Add a section for PATH
            config.add_section('Paths')
            # Write the list of paths under the 'Paths' section, as a comma-separated string
            config.set('Paths', 'PATH', ','.join(paths))
            # Write the configuration to a file
            with open(full_path_ini, 'w') as configfile:
                config.write(configfile)


        return paths



    def check_data(self):

        # Reset the scan_cycle content [it contains the number of scan cycles per folder selected]
        self.scan_cycles.clear()

        # Reset the 'check' and 'start'progress bar value to 0%
        self.update_progress_bar_value(self.check_pb, 0)
        self.update_progress_bar_value(self.start_pb, 0)
       
        duty_cycle = ""
        duty_cycle_flags = []
        mode = self.mode_cmb.currentText()
        duty_cycle_size = self.duty_cycle.get_duty_cycle_size(int(self.refsig_cmb.currentText()),int(self.signal_cmb.currentText()),
            int(self.ref_cmb.currentText()),int(self.refcal_cmb.currentText())) 

        # Retrieve the duty cycle 
        if(self.mode_cmb.currentText() == self.MODE_TYPE[1]):

            duty_cycle = self.duty_cycle.parse_onoff_duty_cycle(self.refsig_cmb.currentText()+':'+self.signal_cmb.currentText()+':'+
                    self.ref_cmb.currentText()+':'+self.refcal_cmb.currentText())

        else:

            duty_cycle = self.duty_cycle.parse_onoff_duty_cycle(self.signal_cmb.currentText()+':'+self.ref_cmb.currentText()+':'+self.refcal_cmb.currentText())

        # Build the 'duty_cycle_flags' structure
        # If the mode is Nodding then we start adding the REFSIG flag to the 'duty_cycle_flags'
        if(self.mode_cmb.currentText() == self.MODE_TYPE[1]):

            for i in range(int(self.refsig_cmb.currentText())):
                
                duty_cycle_flags.append('REFSIG')

        # Regardless of the mode (i.e. Position switching or Nodding) add the following flags to the 'duty_cycle_flags'
        for i in range(int(self.signal_cmb.currentText())):
                
            duty_cycle_flags.append('SIGNAL')

        for i in range(int(self.ref_cmb.currentText())):
                
            duty_cycle_flags.append('REFERENCE')

        for i in range(int( self.refcal_cmb.currentText())):
                
            duty_cycle_flags.append('REFCAL')

        # Create and start the worker thread, passing the parameter (skip_calibration) to it
        self.thread = CheckWorkerThread(self.check_pb, self.path_to_spectral_line_data[self.backend_cmb.currentIndex()], self.project_id_cmb.currentText(), self.folder0_cmb.currentText(),
            self.folder1_cmb.currentText(), self.folder1_cmb, self.all_folders_cb.isChecked(), duty_cycle, duty_cycle_flags, duty_cycle_size, mode, True)
        #self.thread = CheckWorkerThread(self.path_to_spectral_line_data[self.backend_cmb.currentIndex()], self.project_id_cmb.currentText(), self.folder0_cmb.currentText(),
        #    folders_to_scan[i], duty_cycle, duty_cycle_flags, duty_cycle_size, mode, True)
        
        # Connect the signal from the worker thread to enable/disable the button
        self.thread.update_button_signal.connect(self.update_widgets_state)
        # Connect the signal from the worker thread to the status bar of the main interface
        self.thread.update_console_lv_signal.connect(self.update_console_lv)
        # Connect the signal from the worker thread to the progressbar range of the main interface
        self.thread.update_check_pb_range.connect(self.update_progress_bar_range)
        # Connect the signal from the worker thread to the progressbar value of the main interface
        self.thread.update_check_pb_value.connect(self.update_progress_bar_value)
        # Connect the signal from the worker thread to the main interface with the result
        self.thread.result_signal.connect(self.check_data_result)
        
        # Start the thread
        self.thread.start()

          

    def check_data_result(self, error, check_result, subscans, duty_cycle_size):

        if(error):
        
            self.update_console_lv('FILE ERROR - [DUTY CYCLE: ' + str(check_result[1]) + ', FILE: ' + check_result[2] + '.', QColor("red"))
            self.update_console_lv('Data conversion may provide wrong results!', QColor("red"))
            #self.update_console_lv("", QColor("black"))
            self.enable_check_btn()
            # Get the parameters anyway to start the process

           
        #else:

        # After disabling the combo mode restore it to the prevuious value
        if(self.mode_cmb.currentText() == self.MODE_TYPE[1]):
            self.enable_nodding(True)
        else:
            self.enable_nodding(False)

        n_duty_cycles = int(subscans / duty_cycle_size)
        self.update_console_lv("DUTY CYCLES FOUND [" + str(n_duty_cycles) + "]. Data check completed", QColor("black"))
        self.update_console_lv("", QColor("black"))

        # Enable the process button
        self.start_btn.setEnabled(True)

        # Set the number of subscan per folder
        self.n_subscans = subscans
        #print('SCAN CYCLE PAR', subscans, duty_cycle_size, n_duty_cycles)
        self.scan_cycles.append(n_duty_cycles)

        # Scroll to the bottom of the list view
        self.scroll_to_bottom()
           
    
    
    def check_server(self, remote_ip):

        server_up = self.file_services.ping_server(remote_ip)

        if(server_up):

            self.update_projects_id(self.path_to_spectral_line_data[self.backend_cmb.currentIndex()])
        
        else:

            self.disable_combobox(self.folder0_cmb)
            self.disable_combobox(self.folder1_cmb)
            self.disable_combobox(self.project_id_cmb)
            self.disable_widget([self.update_btn], True)
            self.enable_check_btn()
    

    
    def d2c_cmd_builder(self, duty_cycle, calibration, input_scan_directory, destination_folder):

        cmd = "discos2class " + '-o ' + destination_folder + ' ' + '-c ' + duty_cycle + ' '
       
        if(calibration):
            
            cmd = cmd + '-s '
      
        cmd = cmd + input_scan_directory
        
        return cmd


         
    def disable_combobox(self, widget):

        widget.clear() 
        widget.addItems(self.COMBO_MSGs)
        widget.setEnabled(False)

    
    
    def disable_widget(self, widgets, value):

        for i in range(len(widgets)):

            widgets[i].setDisabled(value)
            
    
    
    def enable_check_btn(self):

        if(self.destination_folder != ""):
            if self.duty_cycle.get_duty_cycle_size(int(self.refsig_cmb.currentText()),int(self.signal_cmb.currentText()),
                int(self.ref_cmb.currentText()),int(self.refcal_cmb.currentText())) > 0:
                if((self.project_id_cmb.currentText() != self.COMBO_MSGs[0]) and (self.folder0_cmb.currentText() != self.COMBO_MSGs[0] ) and 
                    (self.folder1_cmb.currentText() != self.COMBO_MSGs[0] )): 

                    self.check_btn.setEnabled(True)

                else:

                    self.check_btn.setEnabled(False)

            else:
                
                self.check_btn.setEnabled(False)
        else:
                
            self.check_btn.setEnabled(False)
    
    

    def enable_nodding(self, value):

        self.refsig_cmb.setEnabled(value)

        if value == False:
            
            self.refsig_cmb.setCurrentIndex(0)

        self.enable_check_btn()



    def get_dest_folder(self):
        
        self.check_btn.setDisabled(True)
        self.start_btn.setDisabled(True)
        self.destination_folder = filedialog.askdirectory()
        
        if(self.destination_folder):
            
            self.update_console_lv('Selected DESTINATION FOLDER: ' + self.destination_folder, QColor("black"))
            self.enable_check_btn()
        
        else:
            
            self.update_console_lv('Selected DESTINATION FOLDER: <Not Specified>', QColor("black"))
            self.destination_folder = ""

    

    def get_duty_cycle(self):

        # Create the duty cycle string
        if(self.mode_cmb.currentText() == self.MODE_TYPE[0]):

            duty_cycle = str(self.signal_cmb.currentText()) + ':'  + str(self.ref_cmb.currentText()) + ':' + str(self.refcal_cmb.currentText())
        
        else:
            
            duty_cycle = str(self.refsig_cmb.currentText()) + ':'  + str(self.signal_cmb.currentText()) + ':' + str(self.ref_cmb.currentText()) + ':' +  str(self.refcal_cmb.currentText())

        return duty_cycle

    
    
    def get_folders_to_scan(self):

        folders_to_scan = []

        if(self.all_folders_cb.isChecked()):
            # Loop through the items in the combo box
            for i in range(self.folder1_cmb.count()):
                
                folders_to_scan.append(self.folder1_cmb.itemText(i))
        
        else:

            folders_to_scan.append(self.folder1_cmb.currentText())

        return folders_to_scan

    
    
    def on_task_done(self, result):
            
        if(result): # case of errors
            
            self.update_console_lv("Data processing ended with errors! Please check your data and try again.", QColor("red")) 

        else:
                
            self.update_console_lv('Data processing successfully completed! Enjoy GILDAS :-)', QColor("black"))
            self.update_console_lv('', QColor("black"))

        # Scroll to the bottom of the list view
        self.scroll_to_bottom()
 
        # Get the duty cycle string
        duty_cycle = self.get_duty_cycle()   
       
        # Retrieve the folders to scan
        folders_to_scan = self.get_folders_to_scan()

        # Start the next process
        self.start_next_task(folders_to_scan, duty_cycle)
    
    

    def scroll_to_bottom(self):
        # Get the vertical scrollbar and set its value to the maximum to scroll to the bottom
        scrollbar = self.console_lv.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


    
    def convert_data(self):
        
        # Start first thread
        self.current_index = 0
        # Disable the button when the thread starts
        self.update_widgets_state(False)
        self.update_console_lv("Data processing started! Please wait...", QColor("black")) 

        # Create the duty cycle string
        duty_cycle = self.get_duty_cycle()
        # Retrieve the folders to scan
        folders_to_scan = self.get_folders_to_scan()

        # Start the next process        
        self.start_next_task(folders_to_scan, duty_cycle)
    
    
    
    def start_next_task(self, folders_to_scan, duty_cycle):

        if self.current_index < len(folders_to_scan):  # Check if we still have tasks to run

            # Folder to scan
            input_scan_directory = (self.path_to_spectral_line_data[self.backend_cmb.currentIndex()] + '/' + self.project_id_cmb.currentText() +  '/' 
                + self.folder0_cmb.currentText() + '/' + folders_to_scan[self.current_index])
           
            executable_command = self.d2c_cmd_builder(duty_cycle, self.skip_cal_cb.isChecked(), input_scan_directory, self.destination_folder)
            self.update_console_lv_signal.emit("COMMAND BEING EXECUTED -> " + executable_command, QColor("black"))

            # Scroll to the bottom of the list view
            self.scroll_to_bottom()
            
            # Reset the progress bar and associate the scan_cycles to its max value
            self.update_progress_bar_value(self.start_pb, 0)
            self.update_progress_bar_range(self.start_pb, 0, self.scan_cycles[self.current_index])

            self.worker = ConvertWorkerThread(self.current_index, executable_command, self.start_pb)
            # Connect the worker's signal to the method that will start the next task
            self.worker.result_signal.connect(self.on_task_done)
            self.worker.timer_start_signal.connect(self.start_timer)
            self.worker.timer_stop_signal.connect(self.stop_timer)
            self.worker.progress_bar_value_signal.connect(self.update_progress_bar_value)
            self.worker.start()
            self.current_index += 1  # Move to the next task

        else:

            self.update_widgets_state(True)    
            self.start_btn.setEnabled(False)        

        
    
    def update_folders_level0(self):
        
        # populate the combo boxes containing the sub-folder [level-0]
        self.folders_level0 = self.file_services.get_folders(self.path_to_spectral_line_data[self.backend_cmb.currentIndex()] + self.project_id_cmb.currentText(), "0-sl")

         # if self.folders_level0 is not empty then populate the relative combo box and try to get the folders relative to level 1 
        if(len(self.folders_level0) > 0):

            self.folders_level0.sort()
            self.folder0_cmb.clear() 
            self.folder0_cmb.addItems(self.folders_level0)
            self.folder0_cmb.setCurrentIndex(0)
            self.folder0_cmb.setEnabled(True)
            self.folder1_cmb.clear()  

            self.update_folders_level1()
        
        else:
        
            self.disable_combobox(self.folder0_cmb)
            self.disable_combobox(self.folder1_cmb)

    
    def update_folders_level1(self):

        # populate the combo boxes containing the sub-folder [level-0]
        self.folders_level1 = self.file_services.get_folders(self.path_to_spectral_line_data[self.backend_cmb.currentIndex()] + self.project_id_cmb.currentText() 
                + "/" + self.folder0_cmb.currentText(), "1-sl")

         # if self.folders_level1 is not empty then populate the relative combobox 
        if(len(self.folders_level1) > 0):

            self.folders_level1.sort()
            self.folder1_cmb.clear()  
            self.folder1_cmb.addItems(self.folders_level1)
            self.folder1_cmb.setCurrentIndex(0)
            self.folder1_cmb.setEnabled(True)
            
            # Change dinamically the width of the dropdown list of the QcomboBox
            # Instead of converting the combo items lengths into pixels (it is font properties dependant) we use another trick
            # For the given font used, 29 characters in length are equal to around 340 pixels of the dropdown QcomboBox width
        
            # get maximum length in characters from the list
            max_item_length = len(max(self.folders_level1, key=len))

            required_width = (340/29)*max_item_length        

            view = self.folder1_cmb.view()
            view.setFixedWidth(int(required_width))
        
        else:

            self.disable_combobox(self.folder1_cmb)
        
        self.enable_check_btn()
    
      

    def update_console_lv(self, string: str, color: QColor):

        current_date = QDateTime.currentDateTime().toString("dd-MM-yyyy")
        # Get the current time (you can also adjust the format if you want to include time)
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
        # Get the current date and time
        # current_datetime = QDateTime.currentDateTime().toString(Qt.DefaultLocaleLongDate)
        # Create a QStandardItem with the current date and time
        init_msg = f"[{current_date} - {current_time}]: " + string
        init_msg_item = QStandardItem(init_msg)
        # Set the foreground color according to the message ('red' for errors, 'black' otherwise)
        init_msg_item.setForeground(color)
        # Add the item to the model (which updates the QListView)
       
        self.model.appendRow(init_msg_item)

        
    

        scrollbar = self.console_lv.verticalScrollBar()
        # Scroll to the maximum value (bottom of the list)
        scrollbar.setValue(scrollbar.maximum())


        
    def update_progress_bar_value(self, pb: QProgressBar, value: int):

        # print('Value:', value)
        pb.setValue(value)

    
    
    def update_progress_bar_range(self, pb: QProgressBar, min_value: int, max_value: int):

        # pb.reset()
        # print('Range:', min_value, max_value)
        pb.setRange(min_value, max_value)


    
    def update_projects_id(self, server_index):

        if(self.debug_on):

            # get the projects id
            self.projects_id.clear()
            self.project_id_cmb.clear()
            self.projects_id = self.file_services.get_projects_id(server_index)
            # if the projects id is not empty sort the folder names otherwise disable the combo boxes containing the folder names
            if(self.projects_id):

                self.projects_id.sort()
                self.project_id_cmb.addItems(self.projects_id)
                self.project_id_cmb.setEnabled(True)
                self.disable_widget([self.update_btn], False)

                # populate the combo boxes containing the sub-folder [level-0]
                self.update_folders_level0()
            
            else:

                self.disable_combobox(self.folder0_cmb)
                self.disable_combobox(self.folder1_cmb)
                self.disable_combobox(self.project_id_cmb)
                self.disable_widget([self.update_btn], True)
            
            self.enable_check_btn()

        else:

            # Retrieve the project id associated to the logged username
            # Get the current logged-in username. This coincides with the project id number
            username = os.getlogin()
            #username = '26-23'
            #print("Current logged-in username:", username)
            project_id = [] # defined as list since the combo box accept an items-list
            project_id.append(username)
            
            self.project_id_cmb.addItems(project_id)
            self.project_id_cmb.setEnabled(False)
            self.disable_widget([self.update_btn], False)

            # populate the combo boxes containing the sub-folder [level-0]
            self.update_folders_level0()

            self.enable_check_btn()
            
    
    
    def update_widgets_state(self, value):

        # Adding combobox drop down list 
        self.backend_cmb.setEnabled(value) 
        self.all_folders_cb.setEnabled(value)
        self.mode_cmb.setEnabled(value) 
        self.refsig_cmb.setEnabled(value) 
        self.signal_cmb.setEnabled(value) 
        self.ref_cmb.setEnabled(value) 
        self.refcal_cmb.setEnabled(value) 
        self.project_id_cmb.setEnabled(value)  
        self.folder0_cmb.setEnabled(value) 
        self.folder1_cmb.setEnabled(value) 
        self.skip_cal_cb.setEnabled(value)
        self.update_btn.setEnabled(value) 
        self.check_btn.setEnabled(value) 
        self.dest_btn.setEnabled(value) 
        self.start_btn.setEnabled(value) 

    
    # Timer stuff
    def update_progress_bar_timer(self):
        
        try:
                
            f = open('scan_cycle.txt', 'r')
            current_scan_cycle = int(f.read()) 
            f.close()
            # print(self.scan_cycle+1)
            self.update_progress_bar_value(self.start_pb, current_scan_cycle)

            current_time = QTime.currentTime().toString("hh:mm:ss AP")
            print(f"Current Time: {current_time}")
            
        except:
                
            pass

    def start_timer(self):
        
        if not self.timer_running:
            # Start the timer
            self.timer.start(self.timer_interval)
            self.timer_running = True

    def stop_timer(self):
        
        if self.timer_running:
            # Stop the timer
            self.timer.stop()
            self.timer_running = False

            try:
                
                current_time = QTime.currentTime().toString("hh:mm:ss AP")
                print(f"Current Time [STOP]: {current_time}")
                # Read the last value for final update of the progressbar
                f = open('scan_cycle.txt', 'r')
                current_scan_cycle = int(f.read())    
                f.close()
                # print(self.scan_cycle)
                self.update_progress_bar_value(self.start_pb, current_scan_cycle)
                # Reset the output file scan cycle value
                with open('scan_cycle.txt', 'w') as output:
                    output.write(str(0))
                print(time.ctime())
            
            except:
                
                pass
           

        
if __name__ == "__main__":
    # The next line solves the issues of mismatch between designer sizes and monitor sizes
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setStyleSheet('QComboBox {combobox-popup: 0}') # this line makes possible to render the limit of visible rows in a combobox  

    ui = MainUI()
    ui.show()
    app.exec_()
