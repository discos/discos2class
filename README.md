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
$ ls data/xarcos_test_data_set/20160331-104808-7-15-w3oh/
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
$ discos2class -o classdata/xarcos_test/ -c 10:10:1 data/xarcos_test_data_set/20160331-104808-7-15-w3oh
E-OPEN,  Open error file classdata/xarcos_test/2016091_w3oh.d2c
E-OPEN,  No such file or directory (O/S errno #    2)
I-FILE,  File is version 2 (record length: 1024 words)
I-NEWPUT,  classdata/xarcos_test/2016091_w3oh.d2c initialized
INFO: open new file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-OUTPUT,  classdata/xarcos_test/2016091_w3oh.d2c successfully opened
INFO: append observation to file classdata/xarcos_test/2016091_w3oh.d2c

```

We have invoked the discos2class command specifying the scan configuration (10 on 10 off 1 cal)
and the input and output data directories, from the command output we can see
which file have been created and succesively updated with all observations.

In the destination directory a new directory is created. It is named exactly as 
specified in the command line option:

```bash
$ ls classdata/xarcos_test/
2016091_w3oh.d2c
```

Inside the directory a new CLASS file is created for each different source per 
day found in the original files.

Each file contains the result of the integration and calibration of all the observation
data. Different sections and polarizations are treated as different line names
in different observations listed in the file.

You can now use CLASS software to inspect your data: 

```bash
$ cd classdata/xarcos_test $
$ class
...
LAS> file in 2016091_w3oh.d2c
I-CONVERT,  File is  [Native]
I-INPUT,  2016091_w3oh.d2c successfully opened
LAS> find /all
I-FIND,  8 observations found
LAS> list
Current index contains:
N;V Source       Line         Telescope      Lambda     Beta Sys  Sca Sub
1;1 W3OH         SEC0-RCP     MEDICINA         +0.0     +0.0 Eq     2 1
2;1 W3OH         SEC0-LCP     MEDICINA         +0.0     +0.0 Eq     2 1
3;1 W3OH         SEC1-RCP     MEDICINA         +0.0     +0.0 Eq     2 1
4;1 W3OH         SEC1-LCP     MEDICINA         +0.0     +0.0 Eq     2 1
5;1 W3OH         SEC2-RCP     MEDICINA         +0.0     +0.0 Eq     2 1
6;1 W3OH         SEC2-LCP     MEDICINA         +0.0     +0.0 Eq     2 1
7;1 W3OH         SEC3-RCP     MEDICINA         +0.0     +0.0 Eq     2 1
8;1 W3OH         SEC3-LCP     MEDICINA         +0.0     +0.0 Eq     2 1
LAS> get 1
I-GET,  Observation 1; Vers 1 Scan 2
LAS> plot
```
![Class screenshot](class_screenshot.png?raw=true "Class Screenshot")

###Class Utility scripts

In the package directory **class_scripts** are located scripts callable from the
class elaboration software. These scripts are very naive, I'm not an experienced 
class users and I devloped these scripts only as shortcuts for common operations
I'm doing in the development process. Nevertheless if an experienced user is
willing to write more complex elaboration pipelines, this is where those should be put.

At the moment we have defined: 

  * **average_sections** : for sections 0 to 3 make an average of all observations
     in the current file and adds a new observation of line **SECN-AVERAGE**
     
Using the scripts is accomplished via the **@** operator in a class session:

```bash
LAS> @ class_scripts/average_sections
I-FIND,  8 observations found
Consistency checks:
  Checking Data type and regular x-axis sampling
...

I-WRITE,  Observation #36;1 successfully written
I-FIND,  4 observations found
Current index contains:
 N;V Source       Line         Telescope      Lambda     Beta Sys  Sca Sub
33;1 S140         SEC0-AVERAGE MEDICINA         +0.0     +0.0 Eq     1 1
34;1 S140         SEC1-AVERAGE MEDICINA         +0.0     +0.0 Eq     1 1
35;1 S140         SEC2-AVERAGE MEDICINA         +0.0     +0.0 Eq     1 1
36;1 S140         SEC3-AVERAGE MEDICINA         +0.0     +0.0 Eq     1 1
```

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
that is **GILDAS Version: apr24a**

## Installation

The command line tool can be installed via:

```bash
$ python setup.py install
```

Tested with Python 3.11.8






 
