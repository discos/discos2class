from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import pyqtSignal
from PyQt5.uic import loadUi

from astropy.io import fits
from astropy.time import Time

# from concurrent import futures

import datetime
import glob
import os
import threading
import time
import subprocess 
import sys

import tkinter as tk
from tkinter import filedialog

# thread_pool_executor = futures.ThreadPoolExecutor(max_workers=1)

DATA_EXTENSION = ".fits"

class MainUI(QMainWindow):

    updateText = pyqtSignal(str) 
    
    DUTY_CYCLE_VALUES = ['0','1','2','3','4','5','6','7','8','9']
    MODE_TYPE = ['Position Switching', 'Nodding']
    BACKEND_TYPE = ['Sardara', 'Skarab']

    def __init__(self):
        super(MainUI, self).__init__()

        loadUi("d2c_gui.ui", self)

        self.updateText.connect(self.info_panel_ta.appendPlainText)

        self.source_folder = ""
        self.destination_folder = ""
        # Fix dimensions of the QMainWindow widget
        self.setFixedSize(850, 450)
        # self.centralwidget.setFixedSize(800,441)

        #self.gridLayout.setColumnStretch(10, 2)
        #self.horizontalLayout_1.setStretch(10, 2)

        # using now() to get current time
        current_time = datetime.datetime.now()
        greetings_text = '*** Welcome to d2c Converter [GUI Mode - v. 0.1] ***'

        # adding the duty cycle values to the relative combo boxes
        self.duty_cycle_cmb0.addItems(self.DUTY_CYCLE_VALUES)
        self.duty_cycle_cmb1.addItems(self.DUTY_CYCLE_VALUES)
        self.duty_cycle_cmb2.addItems(self.DUTY_CYCLE_VALUES)
        self.duty_cycle_cmb3.addItems(self.DUTY_CYCLE_VALUES)

        # adding mode-type list to the relative combo box
        self.mode_cmb.addItems(self.MODE_TYPE)
        self.backend_cmb.addItems(self.BACKEND_TYPE)
        self.backend_cmb.setDisabled(True)

        #  adding action to combo box mode type (Position Switching, Nodding) 
        self.mode_cmb.activated.connect(self.switch_duty_cycles) 

        # Make the text area read-only
        self.info_panel_ta.setReadOnly(True)

        self.info_panel_ta.appendPlainText(greetings_text)
        self.info_panel_ta.appendPlainText("")

        #self.info_panel_ta.appendPlainText('Current time is: ' + str(current_time))

        # 'convert' and 'verify' button are disabled until both source and destination folders are selected 
        self.convert_btn.setDisabled(True)
        self.verify_btn.setDisabled(True)
        
        # Buttons and Combos functions
        self.source_folder_btn.clicked.connect(self.select_source_folder)
        self.destination_folder_btn.clicked.connect(self.select_destination_folder)
        self.verify_btn.clicked.connect(self.verify_btn_handler)
        self.convert_btn.clicked.connect(self.convert_btn_handler)
        self.duty_cycle_cmb3.currentIndexChanged.connect(self.disable_convert_btn)
        self.duty_cycle_cmb1.currentIndexChanged.connect(self.disable_convert_btn)
        self.duty_cycle_cmb2.currentIndexChanged.connect(self.disable_convert_btn)
        self.duty_cycle_cmb0.currentIndexChanged.connect(self.disable_convert_btn)
        self.mode_cmb.currentIndexChanged.connect(self.disable_convert_btn)
        self.calibration_cb.clicked.connect(self.disable_convert_btn)

    def disable_all_widgets(self, value):

        self.source_folder_btn.setDisabled(value)
        self.destination_folder_btn.setDisabled(value)
        self.verify_btn.setDisabled(value)
        self.convert_btn.setDisabled(value)
        self.duty_cycle_cmb3.setDisabled(value)
        self.duty_cycle_cmb1.setDisabled(value)
        self.duty_cycle_cmb2.setDisabled(value)
        if(self.mode_cmb.currentText() == 'Nodding'):
            self.duty_cycle_cmb0.setDisabled(value)
        self.calibration_cb.setDisabled(value)
        self.mode_cmb.setDisabled(value)                       
        
    def switch_duty_cycles(self):
        # activete or deactivare the fourth duty_cycle_cb according to the mode selected (PS:3, ND:4)
        if(self.mode_cmb.currentText() == 'Position Switching'):
            self.duty_cycle_cmb0.setCurrentIndex(0) 
            self.duty_cycle_cmb0.setDisabled(True)
        else:
            self.duty_cycle_cmb0.setDisabled(False)
    
    def select_source_folder(self):

        self.verify_btn.setDisabled(True)
        self.convert_btn.setDisabled(True)
        self.source_folder = filedialog.askdirectory()
        if(self.source_folder):
            self.info_panel_ta.appendPlainText('Source folder selected: ' + self.source_folder)
            self.enable_verify_btn()

    def select_destination_folder(self):
        
        self.verify_btn.setDisabled(True)
        self.convert_btn.setDisabled(True)
        self.destination_folder = filedialog.askdirectory()
        if(self.destination_folder):
            self.info_panel_ta.appendPlainText('Destination folder selected: ' + self.destination_folder)
            self.enable_verify_btn()

    def disable_convert_btn(self):

        self.convert_btn.setDisabled(True)
        

    def build_duty_cycle(self):

        duty_cycle = ''
        
        if(self.mode_cmb.currentText() == 'Position Switching'):

            duty_cycle = str(self.duty_cycle_cmb1.currentText()) + ':'  + str(self.duty_cycle_cmb2.currentText()) + ':' + str(self.duty_cycle_cmb3.currentText())
        else:
            duty_cycle = str(self.duty_cycle_cmb0.currentText()) + ':'  + str(self.duty_cycle_cmb1.currentText()) + ':' + str(self.duty_cycle_cmb2.currentText()) + ':' +  str(self.duty_cycle_cmb3.currentText())
        return duty_cycle

    def convert_btn_handler(self):

        #self.disable_all_widgets(True)

        duty_cycle = self.build_duty_cycle()

        executable_command = self.d2c_cmd_builder(self.debug_cb.isChecked(), duty_cycle, self.calibration_cb.isChecked(), self.version_cb.isChecked())
        
        self.info_panel_ta.appendPlainText('Please wait while data are being converted...')
        self.info_panel_ta.appendPlainText("")
        self.disable_all_widgets(True)

        #self.thread0 = threading.Thread(target=self.disable_all_widgets, args=(True,))
        #self.thread0.start()
        #self.thread0.join()

        self.thread = threading.Thread(target=self.exec_cmd, args=(executable_command,))
        self.thread.start()
        #self.thread.join()

        

    def verify_btn_handler(self):

        file_error = False

        duty_cycle = self.build_duty_cycle()

        executable_command = self.d2c_cmd_builder(self.debug_cb.isChecked(), duty_cycle, self.calibration_cb.isChecked(), self.version_cb.isChecked())                                        

        self.info_panel_ta.appendPlainText("")
        self.info_panel_ta.appendPlainText('*** PARAMETERS SUMMARY***')
        self.info_panel_ta.appendPlainText("")
        self.info_panel_ta.appendPlainText('Duty Cycle -> ' + duty_cycle)
        self.info_panel_ta.appendPlainText('Debug -> ' + str(self.debug_cb.isChecked()))
        self.info_panel_ta.appendPlainText('Skip Calibration -> ' + str(self.calibration_cb.isChecked()))
        self.info_panel_ta.appendPlainText('Version -> ' + str(self.version_cb.isChecked()))
        self.info_panel_ta.appendPlainText('Mode -> ' + str( self.mode_cmb.currentText()))
        self.info_panel_ta.appendPlainText('Backend -> ' + str( self.backend_cmb.currentText()))
        self.info_panel_ta.appendPlainText("")
        self.info_panel_ta.appendPlainText(executable_command)
        self.info_panel_ta.appendPlainText("")

        self.check_fits_files_duty_cycle()

        file_error, nduty_cycle_err  = self.check_fits_files_duty_cycle()
        if not file_error:

            self.enable_convert_btn()

        else:
            # update QtextArea
            self.updateText.emit('Duty-Cycle ERROR #' + str(nduty_cycle_err))


    def check_fits_files_duty_cycle(self):
        # This method checks if the fits files contained in the source folder match the duty cycle structure
        subscans = []
        duty_cycle_flags = []
        error = False
        nfile_err = 0 

        # if the mode is Nodding then we start adding the REFSIG flag to the 'duty_cycle_flags'
        if(self.mode_cmb.currentText() == 'Nodding'):

            for i in range(int(self.duty_cycle_cmb0.currentText())):
                
                duty_cycle_flags.append('REFSIG')

        # regardless of the mode (i.e. Position switching or Nodding) add the following flags to the 'duty_cycle_flags'

        for i in range(int(self.duty_cycle_cmb1.currentText())):
                
            duty_cycle_flags.append('SIGNAL')

        for i in range(int(self.duty_cycle_cmb2.currentText())):
                
            duty_cycle_flags.append('REFERENCE')

        for i in range(int(self.duty_cycle_cmb3.currentText())):
                
            duty_cycle_flags.append('REFCAL')
      
        # Start fits file and duty cycle comparison
        
        # summary_file = glob.glob(self.source_folder+'?um*.fits')
        
        for subscan_file in os.listdir(self.source_folder):

            ext = os.path.splitext(subscan_file)[-1]

            if not subscan_file.lower().startswith('sum') and ext == DATA_EXTENSION:
                subscan_path = os.path.join(self.source_folder, subscan_file)

                with fits.open(subscan_path) as subscan:
                    subscans.append((subscan_path, 
                                     subscan[0].header["SIGNAL"],
                                     Time(subscan["DATA TABLE"].data["time"][0],
                                          format = "mjd",
                                          scale = "utc")
                    ))
        
        # order file names by internal data timestamp
        subscans.sort(key=lambda x:x[2])

        j = 0 # duty_cycle index
        d = 0 # duty_cycle current number
        
        for i in range(len(subscans)):
        
            if(subscans[i][1] != duty_cycle_flags[j]):
            
                error = True
                nfile_err = i
                break
            else:

                error = False

            j = j + 1

            if(j == len(duty_cycle_flags)):

                j = 0
                d = d + 1
            
        return error, d
       
          
    def enable_convert_btn(self):
        if( (self.source_folder != "") and (self.destination_folder != "") ):
            self.convert_btn.setDisabled(False)   
        else:
            self.convert_btn.setDisabled(True)

    def enable_verify_btn(self):
        if( (self.source_folder != "") and (self.destination_folder != "") ):
            self.verify_btn.setDisabled(False)   
        else:
            self.verify_btn.setDisabled(True)
    
           

    def d2c_cmd_builder(self, debug_mode, duty_cycle, calibration, version):

        cmd = "discos2class "
        if(debug_mode):
            cmd = cmd + '-d '
        cmd = cmd + '-o ' + self.destination_folder + ' '
        cmd = cmd + '-c ' + duty_cycle + ' '
        if(calibration):
            cmd = cmd + '-s '
        if(version):
            cmd = cmd + '--version '
        cmd = cmd + self.source_folder
        
        return cmd

    
 
    def exec_cmd(self, executable_command):

        p = subprocess.Popen([executable_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #p = subprocess.Popen(['designer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
       
        # To capture the error message:
        stdout, stderr = p.communicate()
        # stdout = normal output
        # stderr = error output

        # p.terminate()
        time.sleep(1)
        # self.convert_btn.setDisabled(False)
        
        if p.returncode != 0:
            # handle error
            self.updateText.emit('*** PROCESS RETURNED ERRORS ***')
            self.updateText.emit(stderr.decode()) # stderr is a byte object and must be converted
            self.updateText.emit(stdout.decode())
        else:
            self.updateText.emit('*** PROCESS SUCCESSFULLY COMPLETED ***')
            self.updateText.emit("")

        self.disable_all_widgets(False)
        self.convert_btn.setDisabled(True)   
        

if __name__ == "__main__":
    # the next line solves the issues of mismatch between designer sizes and monitor sizes
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    app.exec_()


