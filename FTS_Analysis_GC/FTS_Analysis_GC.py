import pandas as pd
from scipy import integrate
import os
from typing import Literal
import matplotlib.pyplot as plt
import numpy as np

experiment_path=None
def collect_chromatogram_files(experiment_path):
    """
    Collects file lists for FID, TCD_AuxLeft, and TCD_AuxRight chromatograms and loads the first file from each list.
    Args:
        experiment_path (str): Path to the experiment directory.
    Returns:
        tuple: (FIDList, AuxLeftList, AuxRightList, FID_0, AuxLeft_0, AuxRight_0)
    """
    # Collect chromatogram files
    DataDict = os.path.join(experiment_path, 'chromatograms')
    FIDList = []
    AuxRightList = []
    AuxLeftList = []
    for root, dirs, files in os.walk(DataDict, topdown=True):
        for name in files:
            if 'FID_' in name:
                FIDList.append(os.path.join(root, name))
            if 'TCD_AuxLeft' in name:
                AuxLeftList.append(os.path.join(root, name))
            if 'TCD_AuxRight' in name:
                AuxRightList.append(os.path.join(root, name))
    FID_0 = pd.read_csv(FIDList[0], names=['Time', 'Step', 'Value'], sep='\t', skiprows=43) if FIDList else None
    AuxLeft_0 = pd.read_csv(AuxLeftList[0], names=['Time', 'Step', 'Value'], sep='\t', skiprows=43) if AuxLeftList else None
    AuxRight_0 = pd.read_csv(AuxRightList[0], names=['Time', 'Step', 'Value'], sep='\t', skiprows=43) if AuxRightList else None
    return FIDList, AuxLeftList, AuxRightList, FID_0, AuxLeft_0, AuxRight_0

class chromatogram_FTGC:
    def __init__(self, filename, datetime_start):
        self.df = pd.read_csv(filename, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
        self.df = self.df.replace(',', '', regex=True)
        #self.df = self.df.astype('float')

        self.Name = os.path.basename(filename)
        base = self.Name.split('.txt')[0]
        # Determine where the timestamp starts
        if base.startswith('FID_'):
            time_str = base.split('FID_')[-1]
        elif base.startswith('TCD_AuxLeft_'):
            time_str = base.split('TCD_AuxLeft_')[-1]
        elif base.startswith('TCD_AuxRight_'):
            time_str = base.split('TCD_AuxRight_')[-1]
        else:
            raise ValueError(f"Unrecognized filename format: {self.Name}")
        self.time_str = time_str  # e.g., '06-Apr-2025 16_29'
        self.file_datetime = pd.to_datetime(self.time_str, format='%d-%b-%Y %H_%M', errors='coerce')

        self.DateTimeFromStart = self.file_datetime - datetime_start
        self.MinutesFromStart = round(self.DateTimeFromStart.total_seconds() / 60)

class chromatogram_HTHPGC:
    def __init__(self, filename, datetime_start):
        self.df = pd.read_csv(filename, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
        self.df = self.df.replace('n.a.', 0, regex=True)
        self.df = self.df.replace(',', '.', regex=True)
        self.Name = os.path.basename(filename)
        # Extract time from filename
        self.time_str_ = self.Name.split('.txt')[0]
        if 'FID' in self.time_str_:
            self.time_str = self.time_str_.split('Ch1_')[-1]
        elif 'TCD' in self.time_str_:
            self.time_str = self.time_str_.split('Ch2_3_')[-1]
        else:
            self.time_str = self.time_str_  # fallback
        # Convert Dutch to English months if needed
        self.time_str = self.time_str.replace('okt', 'oct').replace('mei', 'may')
        self.file_datetime = pd.to_datetime(self.time_str, format='%d-%b-%Y %H_%M', errors='coerce')
        self.DateTimeFromStart = self.file_datetime - datetime_start
        self.MinutesFromStart = round(self.DateTimeFromStart.total_seconds() / 60)
        self.df = self.df.astype('float')


class chromatogram_LPIRGC:
    def __init__(self, filename, datetime_start):
        self.df = pd.read_csv(filename, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
        self.df = self.df.replace(',', '', regex=True)
        #self.df = self.df.astype('float')

        self.Name = os.path.basename(filename)
        base = self.Name.split('.txt')[0]
        # Determine where the timestamp starts
        if base.startswith('Detector 1_'):
            time_str = base.split('Detector 1_')[-1]
        elif base.startswith('Detector 2_'):
            time_str = base.split('Detector 2_')[-1]
        else:
            raise ValueError(f"Unrecognized filename format: {self.Name}")
        self.time_str = time_str  # e.g., '06-Apr-2025 16_29'
        self.file_datetime = pd.to_datetime(self.time_str, format='%d_%b_%Y %H_%M', errors='coerce')

        self.DateTimeFromStart = self.file_datetime - datetime_start
        self.MinutesFromStart = round(self.DateTimeFromStart.total_seconds() / 60)


def collect_chromatogram_filesAll(experiment_path, setup: str = 'FTGC'):
    """
    Collects chromatogram file lists and loads the first file for preview, based on setup type.

    Args:
        experiment_path (str): Path to the experiment directory.
        setup (str): Either 'FTGC' or 'HTHPGC' indicating the naming pattern of the chromatogram files.

    Returns:
        tuple: (FIDList, AuxLeftList, AuxRightList, FID_0, AuxLeft_0, AuxRight_0)
    """
    # Path to chromatogram files
    DataDict = os.path.join(experiment_path, 'chromatograms')

    # Initialize lists
    FIDList = []
    AuxLeftList = []
    AuxRightList = []
    
    # fix for LPIRGC!!

    # File matching patterns based on setup
    if setup == 'FTGC':
        fid_pattern = 'FID_'
        left_pattern = 'TCD_AuxLeft'
        right_pattern = 'TCD_AuxRight'
    elif setup == 'HTHPGC':
        fid_pattern = 'FID_Ch1'
        left_pattern = 'TCD_Ch2_3'  # Assuming AuxLeft is treated as TCD_Ch2_3
        right_pattern = ''  # No AuxRight assumed for HTHPGC, adjust if needed
    elif setup == 'LPIRGC':
        fid_pattern = 'Detector 1_'
        left_pattern = 'Detector 2_'  # No AuxLeft for LPIRGC
        right_pattern = ''  # No AuxRight for LPIRGC
    else:
        raise ValueError(f"Unknown setup: {setup}. Must be 'FTGC', 'HTHPGC' or 'LPIRGC'.")

    # Traverse the directory
    for root, dirs, files in os.walk(DataDict, topdown=True):
        for name in files:
            full_path = os.path.join(root, name)
            if fid_pattern in name:
                FIDList.append(full_path)
            if left_pattern in name:
                AuxLeftList.append(full_path)
            if right_pattern and right_pattern in name:
                AuxRightList.append(full_path)

    # Read first file previews if available
    FID_0 = pd.read_csv(FIDList[0], names=['Time', 'Step', 'Value'], sep='\t', skiprows=43) if FIDList else None
    AuxLeft_0 = pd.read_csv(AuxLeftList[0], names=['Time', 'Step', 'Value'], sep='\t', skiprows=43) if AuxLeftList else None
    AuxRight_0 = pd.read_csv(AuxRightList[0], names=['Time', 'Step', 'Value'], sep='\t', skiprows=43) if AuxRightList else None

    return FIDList, AuxLeftList, AuxRightList, FID_0, AuxLeft_0, AuxRight_0

def read_logfile(experiment_path, gases_to_plot=None, datetime_start=None, plot_against='TOS'):
    """
    Reads and processes reactor logfile(s) from experiment_path.

    Parameters:
        experiment_path (str): Path to the experiment folder containing logfiles.
        gases_to_plot (list of str): Gases to plot (e.g. ['CO', 'H2']). Default: all common.
        datetime_start (datetime or str): Reference start time for TOS calculation.
        plot_against (str): 'TOS' (default) or 'datetime' for x-axis reference.

    Returns:
        pd.DataFrame: Processed logfile with DateTime index and 'TOS' column (in minutes).
    """
    # Step 1: Collect .txt logfiles
    logfile_files = sorted([f for f in os.listdir(experiment_path) if f.endswith('.txt')])
    if not logfile_files:
        raise ValueError('No logfile found in the specified path.')
    
    # Step 2: Read header from first logfile
    df1 = pd.read_csv(os.path.join(experiment_path, logfile_files[0]), header=None, sep='\t', skiprows=1, nrows=1)
    header_row = df1.iloc[0].tolist()

    # Step 3: Read and combine logfiles
    if len(logfile_files) > 1:
        print('Multiple logfiles found! Combining them...')
        logfile = pd.concat([
            pd.read_csv(os.path.join(experiment_path, f), sep='\t', skiprows=2, names=header_row)
            for f in logfile_files
        ])
    else:
        logfile = pd.read_csv(os.path.join(experiment_path, logfile_files[0]), sep='\t', skiprows=2, names=header_row)
    
    # Step 4: Parse datetime and filter for Valve 9 ON (reactor line)
    logfile.index = pd.to_datetime(logfile['Date/Time'], format='%d-%b-%Y %H:%M:%S', errors='coerce')
    logfile = logfile.drop(columns='Date/Time')
    logfile = logfile[logfile['Valve 9'] == 1]

    # Step 5: Select relevant columns
    mfc_columns = [col for col in logfile.columns if 'MFC' in col and 'pv' in col]
    static_columns = ['Valve 9', 'Oven PV', 'Pressure R1', 'Pressure R2', 'BPC A-SP', 'MFM']
    selected_columns = static_columns + mfc_columns
    logfile = logfile[selected_columns]
    logfile['Total Flow'] = logfile[mfc_columns].sum(axis=1)  # Calculate total flow

    # Handle datetime_start and compute TOS
    if datetime_start is None:
        datetime_start = logfile.index[0]  # Default to first on-stream timestamp
        print(f"datetime_start not provided, using: {datetime_start}")
    else:
        datetime_start = pd.to_datetime(datetime_start)

    logfile['TOS'] = (logfile.index - datetime_start).total_seconds() / 60  # minutes

    # Choose x-axis for plotting
    x_axis = logfile['TOS'] if plot_against.lower() == 'tos' else logfile.index

    gas_map = { # Step 7: Define which gas flows to plot
        'CO': 'MFC CO pv',
        'H2': 'MFC H2 pv',
        'Ar': 'MFC Ar pv',
        'N2': 'MFC N2 pv',
        'CO2': 'MFC CO2 pv',
        'O2': 'MFC O2 pv',
        'He': 'MFC He pv'
    }
    if gases_to_plot is None:
        gases_to_plot = list(gas_map.keys())
    gas_columns = [gas_map[g] for g in gases_to_plot if gas_map.get(g) in logfile.columns]
    
    return logfile, x_axis, gas_columns, plot_against

FIDList=[]
def chromatogram(file_list, file_type:str=Literal['FID', 'AuxLeft', 'AuxRight'], fid_reference_list=FIDList, output_path=experiment_path, output_name:str=Literal['FID_total1.csv', 'AuxLeft_total1.csv', 'AuxRight_total1.csv']):    
    """
    Processes chromatogram files, aligns them by minutes from FID start time,
    and optionally saves to CSV unless the output already exists.

    Parameters:
        file_list (list of str): List of chromatogram file paths to process.
        file_type (str): The file type identifier in filenames (e.g., 'FID', 'AuxLeft').
        fid_reference_list (list of str): List of FID filenames to establish start time.
        output_path (str): Directory to save output CSV.
        output_name (str): Name of the CSV file to write.

    Returns:
        pd.DataFrame: Combined chromatogram DataFrame indexed by time (if computed), otherwise None.
    """
    output_file = os.path.join(output_path, output_name)

    # Always reconstruct datetime_start from fid_reference_list
    start_times = []
    for fid in fid_reference_list:
        fid_time_str = fid.split('FID_')[-1].split('.txt')[0]
        fid_datetime = pd.to_datetime(fid_time_str, format='%d-%b-%Y %H_%M', errors='coerce')
        start_times.append(fid_datetime)
    datetime_start = min(start_times) if start_times else None # Use earliest time as reference point

    # If output file exists, just load and return it with datetime_start
    if os.path.isfile(output_file):
        print(f"[INFO] Data is already loaded: {output_name} exists in {output_path}.")
        df_combined = pd.read_csv(output_file, index_col=0, low_memory=False)
        return df_combined, datetime_start 

    chromatogram_dict = {}

    #Step 2: Process each file in the chromatogram file list
    for file_path in file_list: #Read the data: skip metadata rows and load columns as Time, Step, and Value
        df = pd.read_csv(file_path, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
        df = df.replace(',', '', regex=True) # Remove commas if present

        filename = os.path.basename(file_path) # Extract file name from full path
        if file_type not in filename:
            raise ValueError(f"Expected '{file_type}' in filename but got: {filename}")

        #Extract timestamp portion from filename
        time_raw = filename.split('.txt')[0].split(file_type)[-1]
        parts = time_raw.split('_')
        if len(parts) < 3:
            raise ValueError(f"Filename format not recognized for timestamp extraction in: {filename}")
        time_str = parts[1] + '_' + parts[2] #Build timestamp string like '27-Feb-2025_14_30'

        # Convert extracted string into datetime object
        file_datetime = pd.to_datetime(time_str, format='%d-%b-%Y %H_%M', errors='coerce')
        delta_minutes = round((file_datetime - datetime_start).total_seconds() / 60)

        # Add to dict using minutes-from-start as column key
        chromatogram_dict[delta_minutes] = df['Value']
        chromatogram_dict['Time'] = df['Time']

    # Step 3: Construct final DataFrame
    df_combined = pd.DataFrame.from_dict(chromatogram_dict)
    df_combined.index = df['Time']
    df_combined = df_combined.drop(columns='Time')

    # Step 4: Save to CSV
    df_combined.to_csv(output_file, index=True)
    print(f"[INFO] Chromatogram saved to: {output_file}")

    return df_combined, datetime_start

def chromatogramAll(
    file_list,
    setup: Literal['HTHPGC', 'FTGC', 'LPIRGC'],
    output_path,
    output_name,
    fid_reference_list=None
):
    """
    Processes chromatogram files for a given setup ('HTHPGC' or 'FTGC'),
    aligns them by minutes from experiment start time, and saves to CSV.

    Parameters:
        file_list (list of str): List of chromatogram file paths to process.
        setup (str): Either 'HTHPGC' or 'FTGC'.
        output_path (str): Folder to save the output CSV.
        output_name (str): Output CSV filename.
        fid_reference_list (list of str): Required for HTHPGC to determine datetime_start.

    Returns:
        df_combined (pd.DataFrame): Combined chromatogram data.
        datetime_start (datetime): Reference start datetime.
    """
    output_file = os.path.join(output_path, output_name)

    # 1. Determine datetime_start based on setup
    if setup == 'HTHPGC':
        if not fid_reference_list:
            raise ValueError("fid_reference_list is required for setup='HTHPGC'")
        start_times = []
        for fid in fid_reference_list:
            fid_name = os.path.basename(fid)
            time_str = fid_name.split('FID_Ch1_')[-1].split('.txt')[0]
            time_str = time_str.replace('okt', 'oct').replace('mei', 'may')     # change for other setups
            dt = pd.to_datetime(time_str, format='%d-%b-%Y %H_%M', errors='coerce')
            start_times.append(dt)
        datetime_start = min(start_times)
    elif setup == 'FTGC':
        start_times = []
        for file in file_list:
            base = os.path.splitext(os.path.basename(file))[0]
            if base.startswith('FID_'):
                time_str = base.split('FID_')[-1]
            elif base.startswith('TCD_AuxLeft_'):
                time_str = base.split('TCD_AuxLeft_')[-1]
            elif base.startswith('TCD_AuxRight_'):
                time_str = base.split('TCD_AuxRight_')[-1]
            else:
                continue  # Skip unrecognized files

            dt = pd.to_datetime(time_str, format='%d-%b-%Y %H_%M', errors='coerce')
            if pd.notna(dt):
                start_times.append(dt)
        datetime_start = min(start_times)
    elif setup == 'LPIRGC':
        start_times = []
        for file in file_list:
            base = os.path.splitext(os.path.basename(file))[0]
            if base.startswith('Detector 1_'):
                time_str = base.split('Detector 1_')[-1]
            elif base.startswith('Detector 2_'):
                time_str = base.split('Detector 2_')[-1]
            else:
                continue  # Skip unrecognized files

            dt = pd.to_datetime(time_str, format='%d_%b_%Y %H_%M', errors='coerce')
            if pd.notna(dt):
                start_times.append(dt)
        datetime_start = min(start_times)
    else:
        raise ValueError(f"Unsupported setup: {setup}")

    # 2. Load from cache if CSV exists
    if os.path.isfile(output_file):
        print(f"[INFO] [INFO] Data is already loaded: {output_name} exists in {output_path}.")
        df_combined = pd.read_csv(output_file, index_col=0, low_memory=False)
        return df_combined, datetime_start

    # 3. Process chromatograms
    chromatogram_dict = {}
    for file_path in file_list:
        if setup == 'HTHPGC':
            chromo = chromatogram_HTHPGC(file_path, datetime_start)
        elif setup == 'FTGC':
            chromo = chromatogram_FTGC(file_path, datetime_start)
        elif setup == 'LPIRGC':
            chromo = chromatogram_LPIRGC(file_path, datetime_start)

        chromatogram_dict[chromo.MinutesFromStart] = chromo.df['Value']
        chromatogram_dict['Time'] = chromo.df['Time']

    # 4. Combine and export
    df_combined = pd.DataFrame.from_dict(chromatogram_dict)
    df_combined.index = chromo.df['Time']
    df_combined = df_combined.drop(columns='Time')
    df_combined.to_csv(output_file)

    print(f"[INFO] Chromatogram saved to: {output_file}")
    return df_combined, datetime_start

def plot_chromatogram(
    df_list,
    labels=None,
    tos_range=(0, 200),
    show_legend=False,
    show_peaks=True,
    peak_dict=None,
    colormap='viridis'
):
    """
    Plots layered chromatograms from multiple DataFrames with optional peak annotations.

    Parameters:
        df_list (list of pd.DataFrame): List of chromatogram DataFrames.
        labels (list of str): Labels corresponding to each DataFrame.
        tos_range (tuple): Time-on-stream range (min, max) to filter columns.
        show_legend (bool): Whether to show the legend.
        show_peaks (bool): Whether to annotate predefined peak regions.
        peak_dict (dict): Dictionary of peaks per channel, e.g., {'FID': FID_peaks}.
        colormap (str): Matplotlib colormap name (e.g., 'viridis', 'turbo').
    """
    n = len(df_list)
    labels = labels if labels else [f"Channel {i+1}" for i in range(n)]
    fig, axes = plt.subplots(n, 1, figsize=(12, 3.5 * n), sharex=True)

    if n == 1:
        axes = [axes]

    for i, (df, label) in enumerate(zip(df_list, labels)):
        ax = axes[i]
        # Filter by TOS range
        cols = [col for col in df.columns if tos_range[0] <= float(col) <= tos_range[1]]
        df_sub = df[cols]

        # Get colors
        cmap = plt.get_cmap(colormap)
        clr = cmap(np.linspace(0, 1, len(df_sub.columns)))

        # Plot each chromatogram
        for j, col in enumerate(df_sub.columns):
            ax.plot(df_sub.index, df_sub[col], color=clr[j], label=f"TOS {col} min" if show_legend else None)
        ax.set_title(f"{label}")
        ax.set_ylabel("Signal (a.u.)")

        # Optional: annotate peaks
        if show_peaks and peak_dict:
            matched_key = None
            for key in peak_dict.keys():
                if key.lower() in label.lower():
                    matched_key = key
                    break
            if matched_key:
                for compound, (start, end), _ in peak_dict[matched_key]:
                    ax.axvline(start, color='gray', linestyle='--', linewidth=1)
                    ax.axvline(end, color='gray', linestyle='--', linewidth=1)
                    ax.text((start + end)/2, ax.get_ylim()[1]*0.9, compound,
                            rotation=90, ha='center', va='top', fontsize=9, color='black')

        if show_legend:
            ax.legend(loc='upper right', fontsize=8)

    axes[-1].set_xlabel("Retention Time (min)")
    plt.tight_layout()
    plt.show()

def baseline_correct_column(col, time_index, start, end):
    # Select the baseline window values for this column based on the provided time index.
    baseline_values = col[ (time_index >= start) & (time_index <= end) ]
    # Compute the mean over the baseline period.
    baseline = baseline_values.mean()
    # Return the column with the baseline subtracted.
    return col - baseline 

def integrate_named_peaks(DF, named_peak_windows):
    """
    Integrate multiple named peaks from a chromatogram DataFrame.

    Parameters:
    - DF: DataFrame with chromatograms (columns = time points, index = retention time)
    - named_peak_windows: List of [peak_name, [StartTime, EndTime], UseTwoPointBaseLine]

    Returns:
    - DataFrame with integrated areas:
        rows = time points
        columns = peak names (e.g., C1, C2, C3)
    """
    result = {}

    for name, (StartTime, EndTime), UseTwoPointBaseLine in named_peak_windows:
        # Find nearest indices to the time window
        minutes = DF.index
        StartIndex = min(range(len(minutes)), key=lambda i: abs(minutes[i] - StartTime))
        EndIndex = min(range(len(minutes)), key=lambda i: abs(minutes[i] - EndTime))
        PeakDF = DF.iloc[StartIndex:EndIndex]

        peak_areas = []
        time_points = []

        for column in PeakDF.columns:
            time_points.append(float(column))

            if UseTwoPointBaseLine:
                Orginal_Chromatogram = PeakDF[column]
                x_values = PeakDF.index
                y1 = Orginal_Chromatogram.iloc[0]
                y2 = Orginal_Chromatogram.iloc[-1]
                x1 = x_values[0]
                x2 = x_values[-1]
                slope = (y2 - y1) / (x2 - x1)
                ZeroY = y1 - (x1 * slope)
                SlopeLine = x_values * slope + ZeroY
                Subtracted_Chromatogram = Orginal_Chromatogram - SlopeLine
                area = integrate.trapezoid(y=Subtracted_Chromatogram, x=x_values)
            else:
                area = integrate.trapezoid(y=PeakDF[column], x=PeakDF.index)

            peak_areas.append(area)

        result[name] = pd.Series(peak_areas, index=time_points)

    # Combine all peak area series into a DataFrame
    result_df = pd.DataFrame(result)
    result_df.index.name = "Time_Point"
    return result_df

def parse_logfile_areas(area_df, log_df):
    """
    Matches each chromatogram injection with the closest reactor conditions
    based on Time on Stream (TOS in minutes), and adds the exact DateTime.

    Parameters:
        area_df (pd.DataFrame): DataFrame with TOS as index (float).
        log_df (pd.DataFrame): DataFrame with DateTime as index, and 'TOS' as a column (float).

    Returns:
        pd.DataFrame: Combined DataFrame indexed by TOS, with matched reactor conditions and DateTime column.
    """
    # Step 1: Prepare area_df
    area_df = area_df.copy()
    area_df['TOS'] = area_df.index.astype(float)
    area_df = area_df.reset_index(drop=True)

    # Step 2: Prepare log_df — move DateTime index into a column
    log_df = log_df.copy()
    log_df = log_df.reset_index()  # index becomes 'DateTime'
    log_df['TOS'] = log_df['TOS'].astype(float)
    log_df = log_df.sort_values('TOS')

    # Step 3: Match on nearest TOS
    combined_df = pd.merge_asof(
        area_df.sort_values('TOS'),
        log_df,
        on='TOS',
        direction='nearest'
    )
    # Step 4: Set TOS as index, keep DateTime as column
    combined_df = combined_df.set_index('TOS')

    return combined_df
experiment_name = ''
peak_names = []

def plot_comined_overview(
    combined_df,
    gas_flow_columns,
    experiment_name=experiment_name,
    integration_gases=peak_names,
    plot_against='TOS',
    xlim=None,
    ax1_ylim=None,
    ax1_label='Area (pA·min)',
    ax1_title='Peak Areas from Chromatograms'
):
    """
    Plots 3 stacked subplots:
    1. Integration values of gases (C1–C4, CO2, CO, Ar, etc.)
    2. Pressure & Oven Temp
    3. Gas flows

    Parameters:
        combined_df (pd.DataFrame): Combined dataframe with chromatogram + log data.
        experiment_name (str): Title of the experiment.
        integration_gases (list of str): Integration gas column names.
        gas_flow_columns (list of str): Gas flow column names.
        plot_against (str): 'TOS' or 'datetime'
        xlim (tuple): (min, max) for x-axis
        ax1_ylim (tuple): (min, max) for top plot y-axis
        ax1_label (str): Y-axis label for chromatogram result plot
        ax1_title (str): Title for chromatogram result plot
    """
    # X-axis setup
    if plot_against.lower() == 'datetime':
        x_axis = combined_df['DateTime']
        x_label = 'Date/Time'
    else:
        x_axis = combined_df.index
        x_label = 'Time on Stream (min)'

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    # --- Top Plot: Integration values ---
    for gas in integration_gases:
        if gas in combined_df.columns:
            ax1.plot(x_axis, combined_df[gas], label=gas, marker='o', linestyle='')
    ax1.set_ylabel(ax1_label)
    ax1.set_title(f'{ax1_title} \n from {experiment_name}')
    ax1.legend()
    if ax1_ylim:
        ax1.set_ylim(ax1_ylim)

    # --- Middle Plot: Pressure and Oven Temp ---
    ax2.plot(x_axis, combined_df['Pressure R1'], color='tab:blue', label='Pressure (barg)')
    ax2.set_ylabel('Pressure (barg)', color='tab:blue')
    ax2.tick_params(axis='y', labelcolor='tab:blue')

    ax_temp = ax2.twinx()
    ax_temp.plot(x_axis, combined_df['Oven PV'], color='tab:red', label='Oven Temp (°C)')
    ax_temp.set_ylabel('Oven Temp (°C)', color='tab:red')
    ax_temp.tick_params(axis='y', labelcolor='tab:red')
    ax2.set_title(f'Pressure and Oven Temperature over {x_label}')

    # --- Bottom Plot: Gas Flows ---
    for gas_col in gas_flow_columns:
        if gas_col in combined_df.columns:
            ax3.plot(x_axis, combined_df[gas_col], label=gas_col)
    if 'Total Flow' in combined_df.columns:
        ax3.plot(x_axis, combined_df['Total Flow'], label='Total Flow', color='black')
    ax3.set_ylabel('Gas Flow (ml/min)')
    ax3.set_xlabel(x_label)
    ax3.legend(loc='upper right')
    ax3.set_title(f'Gas Flows over {x_label}')

    # Apply TOS xticks if relevant
    if plot_against.lower() == 'tos':
        ax3.set_xticks(np.arange(combined_df.index.min(), combined_df.index.max() + 1, 200))

    # Apply xlim if provided
    if xlim:
        ax1.set_xlim(xlim)

    plt.tight_layout()
    plt.show()

