# 544_WBD_CXCU Project

## Project Overview
This is a neural data analysis project for WBD CXCU.
### Study Description
In this study, individuals were shown content that was either long-form or short-form. They were then asked questions regarding their expereince. 

EEG, Eye-tracking, Facial coding and GSR data was mesured throuhgout the individuals experience. 

Each individual was assigned into a group, ranging A-F. Each group was shown a unique combiantion of longform and short form stimuli.

### Data description
Data was collected and exported from imotions. Data is organised into a folder per group. Within each folder, there are two analyses. The first one has sensor data exports, and the second has merged survey responses.

#### Sensor Data
A single file per respondent. Each file contains a time series of sensor data form the individuals experience, including eye-tracking, facial coding, eeg and gsr data captured at a high frequency.

Each row is a timestamp, and each column is a sensor value.

#### Survey Data
Batch exports of text responses, with a row per respondent and a column per question

## Project Structure
- `README.md` - Project documentation
- `544_WBD_CXCU.py` - Main analysis script
- `requirements.txt` - Python dependencies
- `analysis/assemble_uv.ipynb` - Notebook assembling the unified view and feature extraction stages
- `data/` - Data files directory
- `results/` - Analysis results directory

## Setup Instructions
1. Install required dependencies: `pip install -r requirements.txt`
2. Place data files in the `data/` directory
3. Run the analysis script: `python 544_WBD_CXCU.py`

## Project Status
- Created: September 26, 2025
- Status: In Development