# discos2class

**discos2class** command line tool used to 
convert DISCOS spectroscopy files acquired with XARCOS into CLASS native format.

##TOC

* [Usage](#usage)
  - [Command line help](#command-line-help)
  - [An example session](#an-example-session)
* [Data calibration](#data-calibration)
* [Requirements](#requirements)
* [Installation](#installation)


**WARNING: this project is in a very early beta version and it is not 
guaranteed to be working at all, neither producing correct results**

##Usage

The tool operates on data directories of FITS files saved by the DISCOS system,
where each directory matches a schedule **SCAN**

###Command line help

The command line help explains which options are available and gives hints about
usage:


```bash
$ discos2class --help
usage: discos2class [-h] [-d] [-o OUTPUT_DIR] [-c DUTY_CYCLE] [-s] [--version]
                    source_dir [source_dir ...]

Convert discos SCANs into class files

positional arguments:
  source_dir            directory path(s) to scans

optional arguments:
  -h, --help            show this help message and exit
  -d                    enable debug messages
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        output directory name
  -c DUTY_CYCLE, --duty-cycle DUTY_CYCLE
                        scan duty cycle as "<on>:<off>:<cal>", elements must
                        be all presente but can be zeroes.
  -s, --skip-calibration
                        skip kelvin calibration and computes only ((on - off)
                        / off) ignoring CAL signal
  --version             print version information and exit

```

As you can see, the program elaborates scans found in one ore more source 
directories and saves CLASS-converted spectra in corresponding directories, 
created in an output directory folder. 

###An example session

```bash
$ ls xarcos_test_data_set/20160331-104808-7-15-w3oh/
20160331-104808-7-15-w3oh_002_001.fits  20160331-105255-7-15-w3oh_002_009.fits  20160331-105749-7-15-w3oh_002_017.fits
20160331-104844-7-15-w3oh_002_002.fits  20160331-105331-7-15-w3oh_002_010.fits  20160331-105825-7-15-w3oh_002_018.fits
20160331-104920-7-15-w3oh_002_003.fits  20160331-105414-7-15-w3oh_002_011.fits  20160331-105900-7-15-w3oh_002_019.fits
20160331-104956-7-15-w3oh_002_004.fits  20160331-105450-7-15-w3oh_002_012.fits  20160331-105936-7-15-w3oh_002_020.fits
20160331-105032-7-15-w3oh_002_005.fits  20160331-105525-7-15-w3oh_002_013.fits  20160331-110012-7-15-w3oh_002_021.fits
20160331-105107-7-15-w3oh_002_006.fits  20160331-105601-7-15-w3oh_002_014.fits  summary.fits
20160331-105143-7-15-w3oh_002_007.fits  20160331-105637-7-15-w3oh_002_015.fits
20160331-105219-7-15-w3oh_002_008.fits  20160331-105713-7-15-w3oh_002_016.fits
```

As you can see the source directory contains a whole scan including the 
**summary.fits** file. In this case the **w3oh** source has been observed using a
scan configuration of 10 spectra on-source, 10 spectra off-source and 1 spectrum 
off-source with calibration mark switched on (duty cycle 10-10-1), for a total of 21 subscans.

```bash
$ discos2class -o classdata -g 10:10:1 xarcos_test_data_set/20160331-104808-7-15-w3oh
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC0_RCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC0_LCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC1_RCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC1_LCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC2_RCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC2_LCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC3_RCP.d2c initialized
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/20160331-104808-7-15-w3oh_class/20160331-104808_w3oh_SCAN2_SEC3_LCP.d2c initialized
```

We have invoked the discos2class command specifying the scan configuration (10 on 10 off 1 cal)
and the input and output data directories, from the command output we can see
which files have been created.

In the destination directory a new directory is created. It is named exactly as the 
source directory adding the **_class** suffix:

```bash
$ ls classdata/
20160331-104808-7-15-w3oh_class
```

Inside the directory a new CLASS file is created for each **SECTION** 
**POLARIZATION** and **SCAN NUMBER** combination foud in the original files:

```bash
$ ls classdata/20160331-104808-7-15-w3oh_class/
20160331-104808_w3oh_SCAN2_SEC0_LCP.d2c  20160331-104808_w3oh_SCAN2_SEC1_RCP.d2c  20160331-104808_w3oh_SCAN2_SEC3_LCP.d2c
20160331-104808_w3oh_SCAN2_SEC0_RCP.d2c  20160331-104808_w3oh_SCAN2_SEC2_LCP.d2c  20160331-104808_w3oh_SCAN2_SEC3_RCP.d2c
20160331-104808_w3oh_SCAN2_SEC1_LCP.d2c  20160331-104808_w3oh_SCAN2_SEC2_RCP.d2c
```

Each file contains the integrated spectrum relative to the specified polarization for the specified backend section
in that particular scan. These files can be directly opened with **CLASS** software. 

You can now use CLASS software to inspect your data: 

```bash
$ cd classdata/20160331-104808-7-15-w3oh_class $
$ class
...
LAS> file in 20160331-104808_w3oh_SCAN2_SEC0_LCP.d2c
I-CONVERT,  File is  [Native]
I-INPUT,  20160331-104808_w3oh_SCAN2_SEC0_LCP.d2c successfully opened
LAS> find /all
I-FIND,  1 observation found
LAS> get 1
I-GET,  Observation 1; Vers 1 Scan 2
LAS> plot 
```
![Class screenshot](class_screenshot.png?raw=true "Class Screenshot")


##Data Calibration

If at least one **cal** subscan is present in the specified duty cycle, the software
will calibrate spectra in Kelvin using the calibration mark temperature (obtained
from metadata present in the original FITS files). The procedure will run as:

1. Tcal / (CAL.mean - OFF.mean) = counts2kelvin
2. Tsys = counts2kelvin * OFF.mean
3. SpectrumInKelvin = (ON - OFF) * counts2kelvin = (ON - OFF) * Tsys / OFF.mean

If you skip data calibration by specifying the **-s** command line option, or if
no **cal** subscan is present in the specified duty cycle, the software will just
compute the resulting spectrum as:
 
* (ON - OFF) / OFF

##Requirements

The software is developed in Python, using python2.7, and it depends on  
external python packages:

* astropy
* pyclassfiller

Any astropy version >= 1.0 should be enough for the software to work, while 
pyclassfiller is provided by the **GILDAS** package that you can find at 
https://www.iram.fr/IRAMFR/GILDAS/ . We have installed the latest stable release 
that is **GILDAS Version: mar16a**

## Installation

The command line tool can be installed via:

```bash
$ python setup.py install
```



 
