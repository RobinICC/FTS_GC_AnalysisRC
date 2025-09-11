# CO/CO2 hydrogenation (Fischer-Tropsch) analysis - Under active development
## Description
This repository contains my FTS_GC analysis package. Among others, the package can be used to import .txt files containing the raw chromatogram data 

## Installation 
- clone the repository:
```
git clone https://github.com/RobinICC/FTS_GC_AnalysisRC
```
- install the package by **navigating to the cloned repository** in your python environment and executing the following command:

```
pip install -r requirements.txt
pip install -e .
```
- You should now be able to load the package in python by using:

```python
import FTS_GC_AnalysisRC as fts
```

## Installation (simplest version)
- Download the repository. 
- Copy the *FTS_GC_AnalysisRC* folder to the folder where the script you wanna use for analysis is located. Example:

```
My_Scripts
│
└───FTS
│   │   your_chromatogram_script.py
│   │   your_chromatogram_script.ipynb
│   │
│   └───*FTS_GC_AnalysisRC*
```

## Usage
With only a few simple steps, you can import, view, intergrate GC data data form Chromeleon with online GC setups from the FTS setup DDW ('FTGC'), high temperature high pressure IR ('HTHPGC'), the low pressure IR ('LPIRGC'):
1. Find your data and collect chromatogram files with collect_chromatogram_filesAll() function
  a. Define your experiment_path where you have a folder called 'chromatograms'. Here must alll your raw .txt chromatograms files be placed. When you export them with 'Bram method' from Chromoleon, they should be in the form of 'FID_16-Jun-2025 16_26.txt'. This name differs per setup but they have to contain some sort of datetime in the filename
  b. This function will return a list of filenames per channel of your GC
2. The chromatogram function chromatogramAll() processes a list of chromatogram files (e.g., FID, AuxLeft, AuxRight), aligns them based on time relative to the earliest FID file, and returns a combined DataFrame saved as a CSV file. This can take a while depending on the amount of injections and computer power. Aprox 60 seconds. It will export a df with the combined chromatogram data and saves a .csv file. The index is the retention time and the columns are the time points (TOS)
  a. You only have to do this once to load your data
3. With the plot_chromatogram() function, you can plot all (or a range) of your chromagrams for every channel.
4. Optional: You can apply the baseline_correct_column() function to the gc dataframe. This take a flat part of the chromatogram and substract is from every chromatogram
5. Intergrate your peaks with the integrate_named_peaks() function for each channel seperately. This uses a list of peak windows in the form of [peak_name, [StartTime, EndTime], UseTwoPointBaseLine]. It will return a df with rows as time point (TOS) and columns as peak names (C1, C2, ...)
  a. You can plot you intergration values yourself with a simple for loop. 
7. Optionally, if you hava a logfile containing for example gasflows, temperature and pressures, you can load en read the logfile with the read_logfile() function and parse it with the intergration values with the parse_logfile_areas() function.
  a. If you have the logfile, you can plot the combined overview of your intergration values or amounts with the temperature and pressures in different subplots with plot_combined_overview() function

## Support
If you find bugs or have other questions send me a message or open an issue.

## Contributing
If you want to contribute, let me know.

## Authors
Robin Conradi, Utrecht University

## Acknowledgements
Bram, Bas, en Jan.

