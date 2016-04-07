# discos2class

##TOC

1. [Usage](#Usage)
1.1 [Command line help](#Command_line_help)
1.2 [An example session](#An example session)
2. [Data calibration](#Data_calibration)

**discos2class** command line tool used to 
convert discos spectroscopy files acquired with XARCOS into class native format.

**WARNING: this project is in a very early beta version and it is not 
guaranteed to be working at all, neither producing correct results**

##Usage

The tool operates on data directories of fits files saved by the DISCOS system,
where each directory matches a schedule **SCAN**

###Command line help

The command line help explains what options are available and gives hints about
usage:


```bash
$ discos2class --help
usage: discos2class [-h] [-d] [-o OUTPUT_DIR] [-g GEOMETRY] [-s] [--version]
                    source_dir [source_dir ...]

Convert discos SCANs into class files

positional arguments:
  source_dir            directory path(s) to scans

optional arguments:
  -h, --help            show this help message and exit
  -d                    enable debug messages
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        output directory name
  -g GEOMETRY, --geometry GEOMETRY
                        scan geometry as "<n>on<m>off<c>cal" elements must be
                        all presente but can be zeroes.
  -s, --skip-calibration
                        skip kelvin calibration and computes only ((on - off)
                        / off) ignoring CAL signal
  --version             print version information and exit
```

As you can see the program elaborates scans found in one ore more source 
directories and saves class converted spectra in corresponding directories 
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
**summary.fits** file. In this case **w3oh** source has been observed using a
scan geometry of 10 spectra onsource, 10 spectra offsource and 1 spectra 
offsource with calibration mark activated, for a total of 21 subscans.

```bash
$ discos2class -o classdata -g 10on10off1cal xarcos_test_data_set/20160331-104808-7-15-w3oh
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

We have invoked the discos2class command specifying the san geometry ("10on10off1cal")
and the intpu and output data directories, from the command output we can see
what files have been created.

In the destination directory a new directory is created named exactly as the 
source directory plus the **_class** suffix:

```bash
$ ls classdata/
20160331-104808-7-15-w3oh_class
```

Inside the directory a new class file is created for each **SECTION** 
**POLARIZATION** and **SCAN NUMBER** combination foud in the original files:

```bash
$ ls classdata/20160331-104808-7-15-w3oh_class/
20160331-104808_w3oh_SCAN2_SEC0_LCP.d2c  20160331-104808_w3oh_SCAN2_SEC1_RCP.d2c  20160331-104808_w3oh_SCAN2_SEC3_LCP.d2c
20160331-104808_w3oh_SCAN2_SEC0_RCP.d2c  20160331-104808_w3oh_SCAN2_SEC2_LCP.d2c  20160331-104808_w3oh_SCAN2_SEC3_RCP.d2c
20160331-104808_w3oh_SCAN2_SEC1_LCP.d2c  20160331-104808_w3oh_SCAN2_SEC2_RCP.d2c
```

These files can be directly opened with **class** software. 

##Data Calibration

If at least one **cal** subscan is present in the specified geometry, the software
will calibrate data in Kelvin using the calibration mark temperature obtained
from original fits files metadata. The procedure will run as:

1. Tcal / (CAL.mean - OFF.mean) = counts2kelvin
2. Tsys = counts2kelvin * OFF.mean
3. SpectrumInKelvin = (ON - OFF) * counts2kelvin = (ON - OFF) * Tsys / OFF.mean

If you skip data calibration by specifying the **-s** command line option or if
 no **cal** subscan is present in the specified geometry the software will just
 compute the resulting spectrum as:
 
* (on - off) / off

#



 
