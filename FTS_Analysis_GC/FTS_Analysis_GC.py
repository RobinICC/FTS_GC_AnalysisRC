import pandas as pd
from scipy import integrate
import os
from typing import Literal
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import yaml

def load_experiment_metadata(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

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

class chromatogram_TWOSTAGE:
    def __init__(self, filename, datetime_start):
        self.df = pd.read_csv(filename, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
        self.df = self.df.replace(',', '', regex=True)
        #self.df = self.df.astype('float')

        self.Name = os.path.basename(filename)
        base = self.Name.split('.txt')[0]
        # Determine where the timestamp starts
        if base.startswith('FrontDetector_'):
            time_str = base.split('FrontDetector_')[-1]
        elif base.startswith('AuxLeftDetector_'):
            time_str = base.split('AuxLeftDetector_')[-1]
        elif base.startswith('AuxRightDetector_'):
            time_str = base.split('AuxRightDetector_')[-1]
        else:
            raise ValueError(f"Unrecognized filename format: {self.Name}")
        self.time_str = time_str  # e.g., '06-Apr-2025 16_29'
        self.file_datetime = pd.to_datetime(self.time_str, format='%d_%b_%Y %H_%M', errors='coerce')

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
            raise ValueError(f"Unrecognized filename format: {self.Name}")
        # Convert Dutch to English months if needed
        self.time_str = self.time_str.replace('mrt', 'mar').replace('okt', 'oct').replace('mei', 'may')
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


def collect_chromatogram_filesAll(experiment_path, setup: Literal['HTHPGC', 'FTGC', 'LPIRGC', 'TWOSTAGE']):
    """
    Collects chromatogram file lists and loads the first file for preview, based on setup type.

    Args:
        experiment_path (str): Path to the experiment directory.
        setup (str): Either 'FTGC' or 'HTHPGC' indicating the naming pattern of the chromatogram files.

    Returns:
        tuple: (FIDList, AuxLeftList, AuxRightList)
    """
    # Path to chromatogram files
    DataDict = os.path.join(experiment_path, 'chromatograms')

    # Initialize lists
    FIDList = []
    AuxLeftList = []
    AuxRightList = []

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
    elif setup == 'TWOSTAGE':
        fid_pattern = 'FrontDetector_'
        left_pattern = 'AuxLeftDetector_'
        right_pattern = 'AuxRightDetector_'
    else:
        raise ValueError(f"Unknown setup: {setup}. Must be 'FTGC', 'HTHPGC', 'LPIRGC', or 'TWOSTAGE'.")

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

    return FIDList, AuxLeftList, AuxRightList

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
    DataDict = os.path.join(experiment_path, 'log')
    logfile_files = sorted([f for f in os.listdir(DataDict) if f.endswith('.txt')])
    if not logfile_files:
        raise ValueError('No logfile found in the specified path.')
    
    # Step 2: Read header from first logfile
    df1 = pd.read_csv(os.path.join(DataDict, logfile_files[0]), header=None, sep='\t', skiprows=1, nrows=1)
    header_row = df1.iloc[0].tolist()

    # Step 3: Read and combine logfiles
    if len(logfile_files) > 1:
        print('Multiple logfiles found! Combining them...')
        logfile = pd.concat([
            pd.read_csv(os.path.join(DataDict, f), sep='\t', skiprows=2, names=header_row)
            for f in logfile_files
        ])
    else:
        logfile = pd.read_csv(os.path.join(DataDict, logfile_files[0]), sep='\t', skiprows=2, names=header_row)
    
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

def chromatogramAll(file_list, setup: Literal['HTHPGC', 'FTGC', 'LPIRGC', 'TWOSTAGE'], output_path=None, output_name=None):
    """
    Processes chromatogram files for a given setup ('HTHPGC' or 'FTGC'),
    aligns them by minutes from experiment start time, and saves to CSV.

    Parameters:
        file_list (list of str): List of chromatogram file paths to process.
        setup (str): Either 'HTHPGC', 'FTGC' or 'LPIRGC'.
        output_path (str): Folder to save the output CSV.
        output_name (str): Output CSV filename.

    Returns:
        df_combined (pd.DataFrame): Combined chromatogram data.
        datetime_start (datetime): Reference start datetime.
    """
    output_file = os.path.join(output_path, output_name)

    # 1. Determine datetime_start based on setup
    if setup == 'HTHPGC':
        start_times = []
        for file in file_list:
            base = os.path.splitext(os.path.basename(file))[0]
            if base.startswith('FID_Ch1_'):
                time_str = base.split('FID_Ch1_')[-1]
            elif base.startswith('TCD_Ch2_3_'):
                time_str = base.split('TCD_Ch2_3_')[-1]
            else:
                continue # Skip unrecognized files
            time_str = time_str.replace('mrt', 'mar').replace('okt', 'oct').replace('mei', 'may')     
            dt = pd.to_datetime(time_str, format='%d-%b-%Y %H_%M', errors='coerce')
            if pd.notna(dt):    
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
    
    elif setup == 'TWOSTAGE':
        start_times = []
        for file in file_list:
            base = os.path.splitext(os.path.basename(file))[0]
            if base.startswith('FrontDetector_'):
                time_str = base.split('FrontDetector_')[-1]
            elif base.startswith('AuxLeftDetector_'):
                time_str = base.split('AuxLeftDetector_')[-1]
            elif base.startswith('AuxRightDetector_'):
                time_str = base.split('AuxRightDetector_')[-1]
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
        print(f"[INFO] Data is already loaded: {output_name} exists in {output_path}.")
        gc_combined = pd.read_csv(output_file, index_col=0, low_memory=False)
        gc_combined = gc_combined.replace(',', '', regex=True)  # Remove commas if present
        gc_combined.columns = gc_combined.columns.astype('float')  # Ensure all values are float
        gc_combined = gc_combined.sort_index(axis=1)  # Sort columns by time
        return gc_combined, datetime_start

    # 3. Process chromatograms
    chromatogram_dict = {}
    for file_path in file_list:
        if setup == 'HTHPGC':
            chromo = chromatogram_HTHPGC(file_path, datetime_start)
        elif setup == 'FTGC':
            chromo = chromatogram_FTGC(file_path, datetime_start)
        elif setup == 'LPIRGC':
            chromo = chromatogram_LPIRGC(file_path, datetime_start)
        elif setup == 'TWOSTAGE':
            chromo = chromatogram_TWOSTAGE(file_path, datetime_start)

        chromatogram_dict[chromo.MinutesFromStart] = chromo.df['Value']
        chromatogram_dict['Time'] = chromo.df['Time']

    # 4. Combine and export
    gc_combined = pd.DataFrame.from_dict(chromatogram_dict)
    gc_combined.index = chromo.df['Time']
    gc_combined = gc_combined.drop(columns='Time')
    gc_combined.to_csv(output_file)
    gc_combined = gc_combined.replace(',', '', regex=True)  # Remove commas if present
    gc_combined.columns = gc_combined.columns.astype('float')  # Ensure all values are float
    gc_combined = gc_combined.sort_index(axis=1)  # Sort columns by time
    

    print(f"[INFO] Chromatogram saved to: {output_file}")
    return gc_combined, datetime_start

def plot_chromatogram(
    df_list,
    channels=None,
    tos_range=None,
    show_peaks=False,
    peak_dict=None,
    colormap='viridis',
    plot_colorbar=True
):
    """
    Plots layered chromatograms from multiple DataFrames with optional peak annotations.

    Parameters:
        df_list (list of pd.DataFrame): List of chromatogram DataFrames.
        channels (list of str): Labels corresponding to each DataFrame.
        tos_range (tuple): Time-on-stream range (min, max) to filter columns. 
                           If None, full range is used.
        show_peaks (bool): Whether to annotate predefined peak regions.
        peak_dict (dict): Dictionary of peaks per channel, e.g., {'FID': FID_peaks}.
        colormap (str): Matplotlib colormap name (e.g., 'viridis', 'turbo').
        plot_colorbar (bool): Whether to add a shared colorbar for TOS.
    """
    n = len(df_list)
    channels = channels if channels else [f"Channel {i+1}" for i in range(n)]
    fig, axes = plt.subplots(n, 1, figsize=(12, 3.5 * n), sharex=True)

    if n == 1:
        axes = [axes]

    # Collect global TOS values for normalization
    all_tos_vals = []
    for df in df_list:
        all_tos_vals.extend([float(col) for col in df.columns])
    if tos_range is None:
        tos_range = (min(all_tos_vals), max(all_tos_vals))

    # Setup colormap + normalization
    cmap = plt.get_cmap(colormap)
    norm = Normalize(vmin=tos_range[0], vmax=tos_range[1])

    for i, (df, label) in enumerate(zip(df_list, channels)):
        ax = axes[i]

        # Filter by TOS range
        cols = [col for col in df.columns if tos_range[0] <= float(col) <= tos_range[1]]
        df_sub = df[cols]

        # Colors based on TOS values
        clr = [cmap(norm(float(col))) for col in df_sub.columns]

        # Plot each chromatogram
        for j, col in enumerate(df_sub.columns):
            ax.plot(df_sub.index, df_sub[col], color=clr[j])
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
                    ax.text(
                        (start + end)/2, ax.get_ylim()[1]*0.9, compound,
                        rotation=90, ha='center', va='top', fontsize=9, color='black'
                    )

    # Shared colorbar
    if plot_colorbar:
        sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=axes, location='right', pad=0.02)
        cbar.set_label("TOS (min)")

    axes[-1].set_xlabel("Retention Time (min)")
    fig.subplots_adjust(right=0.78)
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

def plot_comined_overview(
    combined_df,
    gas_flow_columns,
    experiment_name=None,
    integration_gases=None,
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

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 9), sharex=True)

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

def calculate_conversion_based_on_reactant(df, reactant, reactant_initial_concentration):
    """
    Calculates conversion (%) for a single reactant.

    Parameters:
        df (pd.DataFrame): DataFrame containing reactant concentrations.
        reactant (str): Reactant column name.
        reactant_initial_concentration (float): Initial concentration of the reactant.

    Returns:
        pd.Series: Conversion (%) over time with name 'X conversion (%)'.
    """
    reactant_amount = df[reactant]
    conversion_df = ((reactant_initial_concentration - reactant_amount) / reactant_initial_concentration) * 100
    conversion_df.name = f"{reactant} conversion (%)"
    return conversion_df

def calculate_product_conversions(df, products, reactant_initial_concentration):
    """
    Calculates conversion (%) separately for each product over TOS.

    Parameters:
        df (pd.DataFrame): DataFrame with product amounts (columns) over time (index = TOS).
        products (list of str): List of product column names to calculate conversion from.
        reactant_initial_concentration (float): Initial concentration of the reactant.

    Returns:
        pd.DataFrame: Conversion (%) for each product over time.
    """
    interpolated_df = df[products].ffill()     # Interpolate missing data if any (forward fill)
    conversion_df = pd.DataFrame(index=interpolated_df.index)  # Initialize a DataFrame to store conversions
    for product in products:    # Calculate conversion for each product separately
        converted = interpolated_df[product]
        conversion = (1 - ((reactant_initial_concentration - converted) / reactant_initial_concentration)) * 100
        conversion_df[f"{product} conversion (%)"] = conversion
    return conversion_df

def plot_experiment_results(
    metadata_path: str,
    experiments: list,
    column: str,
    ylabel: str = None,
    xlim: tuple = None,
    ylim: tuple = None,
    colors: dict = None,
    figsize: tuple = (8, 6)
):
    """
    Load multiple FTS experiment results and plot them together.

    Parameters:
        metadata_path (str): Path to metadata YAML.
        experiments (list): List of experiment IDs (keys in YAML).
        column (str): Column name to plot (e.g., "CO conversion (%)", "CTY_corrected").
        ylabel (str): Y-axis label (default = column).
        xlim (tuple): X-axis limits (min, max).
        ylim (tuple): Y-axis limits (min, max).
        colors (dict): Optional mapping {exp_id: color}.
        figsize (tuple): Figure size.
    """
    # Load metadata
    all_metadata = load_experiment_metadata(metadata_path)

    dfs = {}
    for exp_id in experiments:
        exp_meta = all_metadata[exp_id]
        exp_path = os.path.join(exp_meta["root"], exp_meta["folder_name"])
        excel_path = os.path.join(exp_path, f"all_results_{exp_id}.xlsx")

        if not os.path.isfile(excel_path):
            print(f"[WARNING] File not found: {excel_path}")
            continue

        dfs[exp_id] = pd.read_excel(excel_path, index_col=0)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    for exp_id, df in dfs.items():
        if column not in df.columns:
            print(f"[WARNING] Column '{column}' not found in {exp_id}")
            continue

        df[column].plot(
            ax=ax,
            marker="o",
            linestyle="",
            label=exp_id,
            c=colors.get(exp_id, None) if colors else None
        )

    ax.set_xlabel("Time on stream (min)", fontsize=14)
    ax.set_ylabel(ylabel if ylabel else column, fontsize=14)

    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)

    ax.xaxis.set_tick_params(labelsize=14)
    ax.yaxis.set_tick_params(labelsize=14)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    ax.legend(title="Experiment", fontsize=12)
    plt.tight_layout()
    plt.show()


def collect_chromatogram(experiment_path):
    """
    Collects file lists for FID, TCD_AuxLeft, and TCD_AuxRight chromatograms and loads the first file from each list.
    Args:
        experiment_path (str): Path to the experiment directory.
    Returns:
        tuple: (chromatogramlist, FIDList, AuxLeftList, AuxRightList)
        chromatogramlist is a list of all chromatograms, the others are only of that respective detector.
    """
        # Collect chromatogram files
    DataDict = os.path.join(experiment_path, 'chromatograms')
    chromatogramlist = []
    FIDList = []
    AuxLeftList = []
    AuxRightList = []
    for root, dirs, files in os.walk(DataDict, topdown=True):
        for name in files:
            if 'FID_' in name:
                FIDList.append(os.path.join(root, name))
            if 'TCD_AuxLeft' in name:
                AuxLeftList.append(os.path.join(root, name))
            if 'TCD_AuxRight' in name:
                AuxRightList.append(os.path.join(root, name))
            chromatogramlist.append(os.path.join(root, name))
    return chromatogramlist, FIDList, AuxLeftList, AuxRightList

class Chromatogram:
    def __init__(self, FID_filepath):
        # General section
        self.file_datetime = None  # Will be set when loading chromatogram
        # FID section
        self.FID_file_path = FID_filepath # this is the only required parameter when creating a chromatogram object, the rest will be loaded later
        self.FID_filename = None
        self.FID_chromatogram = None # Will be set when loading chromatogram
        self.FID_baseline_corrected_chromatogram = None # Will be set when baseline correction is applied
        # TCD_AuxLeft section
        self.TCDLeft_file_path = None
        self.TCDLeft_filename = None
        self.TCDLeft_chromatogram = None # Will be set when loading chromatogram
        #self.TCDLeft_baseline_corrected_chromatogram = None # Will be set when baseline correction is applied
        # TCD_AuxRight section
        self.TCDRight_file_path = None
        self.TCDRight_filename = None
        self.TCDRight_chromatogram = None # Will be set when loading chromatogram
        #self.TCDRight_baseline_corrected_chromatogram = None # Will be set when baseline correction is applied
        # peak integration section
        self.CO2_area = None # Will be set when integrating CO2 peak
        self.Ar_area = None # Will be set when integrating Ar peak
        self.N2_area = None # Will be set when integrating N2 peak
        self.CO_area = None # Will be set when integrating CO peak
        self.C1_area = None # Will be set when integrating CH4 peak
        self.C2_area = None # Will be set when integrating C2H6 peak
        self.C3_area = None # Will be set when integrating C2H4 peak
        self.H2_area = None # Will be set when integrating H2 peak
        # calculation section
        self.CO2_conversion = None # Will be set when calculating CO2 conversion
        
    def __repr__(self):
        return (f"file_datetime = {self.file_datetime},\n"
                f"FID_file_path = {self.FID_file_path},\n"
                f"FID_filename = {self.FID_filename},\n"
                f"FID_chromatogram = {self.FID_chromatogram},\n"
                f"FID_baseline_corrected_chromatogram = {self.FID_baseline_corrected_chromatogram},\n"
                f"TCDLeft_file_path = {self.TCDLeft_file_path},\n"
                f"TCDLeft_filename = {self.TCDLeft_filename},\n"
                f"TCDLeft_chromatogram = {self.TCDLeft_chromatogram},\n"
                f"TCDRight_file_path = {self.TCDRight_file_path},\n"
                f"TCDRight_filename = {self.TCDRight_filename},\n"
                f"TCDRight_chromatogram = {self.TCDRight_chromatogram},\n"
                f"CO2_area = {self.CO2_area},\n"
                f"Ar_area = {self.Ar_area},\n"
                f"N2_area = {self.N2_area},\n"
                f"CO_area = {self.CO_area},\n"
                f"C1_area = {self.C1_area},\n"
                f"C2_area = {self.C2_area},\n"
                f"C3_area = {self.C3_area},\n"
                f"H2_area = {self.H2_area}\n"
                )

    def load_chromatogram(self, file_path):
        if 'FID_' in file_path:
            self.FID_chromatogram = pd.read_csv(file_path, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
            self.FID_chromatogram.replace('n.a.', 0, regex=True, inplace=True)  # Fill NaN values with 0
            self.FID_chromatogram.replace(',', '', regex=True, inplace=True)  # Remove commas if present
            self.FID_chromatogram['Time'] = self.FID_chromatogram['Time'].astype(float)  # Ensure Time is float
            self.FID_chromatogram['Value'] = self.FID_chromatogram['Value'].astype(float)  # Ensure Value is float
            self.FID_chromatogram['Step'] = self.FID_chromatogram['Step'].astype(float)  # Ensure Step is float

        elif 'TCD_AuxLeft' in file_path:
            self.TCDLeft_chromatogram = pd.read_csv(file_path, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
            self.TCDLeft_chromatogram.replace('n.a.', 0, regex=True, inplace=True)  # Fill NaN values with 0
            self.TCDLeft_chromatogram.replace(',', '', regex=True, inplace=True)  # Remove commas if present
            self.TCDLeft_chromatogram['Time'] = self.TCDLeft_chromatogram['Time'].astype(float)  # Ensure Time is float
            self.TCDLeft_chromatogram['Value'] = self.TCDLeft_chromatogram['Value'].astype(float)  # Ensure Value is float
            self.TCDLeft_chromatogram['Step'] = self.TCDLeft_chromatogram['Step'].astype(float)  # Ensure Step is float

        elif 'TCD_AuxRight' in file_path:
            self.TCDRight_chromatogram = pd.read_csv(file_path, names=['Time', 'Step', 'Value'], sep='\t', skiprows=43)
            self.TCDRight_chromatogram.replace('n.a.', 0, regex=True, inplace=True)  # Fill NaN values with 0
            self.TCDRight_chromatogram.replace(',', '', regex=True, inplace=True)  # Remove commas if present
            self.TCDRight_chromatogram['Time'] = self.TCDRight_chromatogram['Time'].astype(float)  # Ensure Time is float
            self.TCDRight_chromatogram['Value'] = self.TCDRight_chromatogram['Value'].astype(float)  # Ensure Value is float
            self.TCDRight_chromatogram['Step'] = self.TCDRight_chromatogram['Step'].astype(float)  # Ensure Step is float

    def create_objects(self, file_path):
        """
        Create chromatogram objects for FID, TCD_AuxLeft, and TCD_AuxRight.
        Args:
            file_path (str): Path to the chromatogram file.
        """
        print(f"Processing file: {file_path}")
        if 'FID_' in file_path:
            self.FID_file_path = file_path
            self.FID_filename = self.FID_file_path.split('\\')[-1]  # Extract file name from full path
            parts = self.FID_filename.rsplit('_', 2)
            date = parts[1]
            time = parts[2].replace('.txt', '')
            time = date[12:14] + ':' + time[:2] #this extra code adds the last part of the date column to the time column, since the splitting on '_' also created problems here
            date = date[:11]
            datetime_str = f"{date} {time}" #this creates a string with the date and time
            self.file_datetime = pd.to_datetime(datetime_str, format='%d-%b-%Y %H_%M', errors='coerce')# Convert to datetime object
            self.load_chromatogram(file_path) # use the load_chromatogram method to load the corresponding chromatogram
        elif 'TCD_AuxLeft' in file_path:
            self.TCDLeft_file_path = file_path
            self.TCDLeft_filename = self.TCDLeft_file_path.split('\\')[-1]  # Extract file name from full path
            self.load_chromatogram(file_path) # use the load_chromatogram method to load the corresponding chromatogram
        elif 'TCD_AuxRight' in file_path:
            self.TCDRight_file_path = file_path
            self.TCDRight_filename = self.TCDRight_file_path.split('\\')[-1]  # Extract file name from full path
            self.load_chromatogram(file_path) # use the load_chromatogram method to load the corresponding chromatogram
        else:
            raise ValueError(f"Unknown chromatogram type in filename: {file_path}")
            
    def apply_baseline_correction(self):
        """
        Apply baseline correction to the chromatogram's 'Value' column.
        Args:
            None
        
        Output:
            it stores the baseline corrected chromatogram in the object but does not overwrite the original one. 
        """
        if self.FID_chromatogram is None:
            raise ValueError("Chromatogram data not loaded. Call load_chromatogram() first.")
        
        else:
            # Define the start and end times for the baseline window
            baseline_start_time = 0.6  # Replace with your desired start time
            baseline_end_time = 0.9    # Replace with your desired end time

            # Select the baseline window values
            baseline_window = self.FID_chromatogram[
                (self.FID_chromatogram['Time'] >= baseline_start_time) &
                (self.FID_chromatogram['Time'] <= baseline_end_time)
            ]['Value']

            # Compute the mean over the baseline period
            baseline_value = baseline_window.mean()
            #print(f"Baseline value calculated: {baseline_value}")
        
        self.FID_baseline_corrected_chromatogram = self.FID_chromatogram.copy()
        self.FID_baseline_corrected_chromatogram['Value'] = self.FID_baseline_corrected_chromatogram['Value'] - baseline_value
        # Ensure no negative values after correction
        self.FID_baseline_corrected_chromatogram['Value'] = self.FID_baseline_corrected_chromatogram['Value'].clip(lower=0)
        #print(f"baseline correction applied to {self.FID_filename}")

    def integrate(self, peak_definitions_dict):
        """
        Integrate specified peaks from the chromatogram using a nested dictionary.

        Args:
            peak_definitions_dict (dict): Dictionary where each key is a detector type (e.g., 'FID', 'TCD_AuxLeft', 'TCD_AuxRight'),
                                          and each value is a dict of {peak_name: (start_time, end_time)}.

        Returns:
            dict: Nested dictionary with detector types as keys, each containing a dict of peak areas.
        """
        results = {}

        # Map detector type to chromatogram attribute
        detector_map = {
            'FID': 'FID_baseline_corrected_chromatogram',
            'TCD_AuxLeft': 'TCDLeft_chromatogram',
            'TCD_AuxRight': 'TCDRight_chromatogram'
        }

        for detector, peaks in peak_definitions_dict.items():
            chromatogram_attr = detector_map.get(detector)
            df = getattr(self, chromatogram_attr, None)
            if df is None:
                continue  # Skip if chromatogram not available

            detector_results = {}
            for peak_name, times in peaks.items():
                mask = (df['Time'] >= times["start_time"]) & (df['Time'] <= times["end_time"])
                peak_df = df.loc[mask]
                if not peak_df.empty:
                    area = integrate.trapezoid(y=peak_df['Value'], x=peak_df['Time'])
                else:
                    area = 0.0
                detector_results[peak_name] = area
                # Set the corresponding attribute if it exists
                attr_name = f"{peak_name}_area"
                if hasattr(self, attr_name):
                    setattr(self, attr_name, area)
            results[detector] = detector_results

        return results

    def calculate_CO2_conversion(self):
        """
        Calculate CO2 conversion based on the areas of CO2 and CH4 peaks.
        Assumes CO2_area and C1_area are already set.
        Returns:
            float: CO2 conversion percentage.
        """
        if self.CO2_area is None or self.Ar_area is None:
            raise ValueError("CO2 and Ar area must be set before calculating conversion.")
        
        self.CO2_conversion = (self.CO2_area / (self.CO2_area + self.Ar_area)) * 100
        print(f"CO2 conversion calculated: {self.CO2_conversion:.2f}%")
    
    

def integrate_peaks(chromatograms, peak_definitions_dict):
    """
    Integrate specified peaks from the chromatograms using a nested dictionary.
    Parameters:
    - chromatograms: List of Chromatogram objects.
    - peak_definitions_dict: Dictionary where each key is a detector type (e.g., 'FID', 'TCD_AuxLeft', 'TCD_AuxRight'),
                             and each value is a dict of {peak_name: (start_time, end_time)}.
    Returns:
    - pd.DataFrame: DataFrame with each column as a peak area, indexed by time in minutes.
    """
    all_peak_names = set()
    # Collect all unique peak names from the definitions
    for peaks in peak_definitions_dict.values():
        all_peak_names.update(peaks.keys())

    data = {peak_name: [] for peak_name in all_peak_names}
    times_minutes = []

    # Use the first chromatogram's file_datetime as reference (t=0)
    if chromatograms and hasattr(chromatograms[0], "file_datetime"):
        t0 = chromatograms[0].file_datetime
    else:
        t0 = None

    for chromatogram in chromatograms:
        chromatogram_results = chromatogram.integrate(peak_definitions_dict)
        # Flatten all detector results into one dict for this chromatogram
        flat_results = {}
        for detector_peaks in chromatogram_results.values():
            flat_results.update(detector_peaks)
        for peak_name in all_peak_names:
            data[peak_name].append(flat_results.get(peak_name, None))
        # Calculate time in minutes relative to t0
        if hasattr(chromatogram, "file_datetime") and t0 is not None:
            delta = chromatogram.file_datetime - t0
            minutes = delta.total_seconds() / 60.0
            times_minutes.append(minutes)
        else:
            times_minutes.append(None)

    df = pd.DataFrame(data)
    df.index = times_minutes
    df.index.name = "Time (min)"
    return df

def find_catalysis_range(areaDF, reactant):
    """
    Find the start and end indices for catalysis based on reactant and N2/H2 criteria.
    Start: first index where reactant > 1.
    End: last index (from the end) where N2 > H2.
    The end index is only considered if it is at the end of the DataFrame (not at the start).
    Parameters:
    - areaDF: DataFrame with peak areas.
    - reactant: str, column name of the reactant peak.
    Returns:
    - Tuple (start_idx, end_idx), and the sliced DataFrame.
    """
    if reactant not in areaDF.columns:
        raise ValueError("Reactant not found in dataframe.")
    if 'N2' not in areaDF.columns or 'H2' not in areaDF.columns:
        raise ValueError("N2 or H2 not found in dataframe.")

    # Find first index where reactant > 1
    start_candidates = areaDF.index[areaDF[reactant] > 10]
    if len(start_candidates) == 0:
        raise ValueError("No start index found where reactant > 1.")
    start_idx = start_candidates[0]

    # Find last index where H2 > N2 (from the end)
    h2_gt_n2 = areaDF['H2'] > areaDF['N2']
    end_candidates = areaDF.index[h2_gt_n2]
    if len(end_candidates) == 0:
        end_idx = areaDF.index[-1]
    else:
        end_idx = end_candidates[-1]

    # Slice the DataFrame
    catalysisDF = areaDF.loc[start_idx:end_idx].copy()
    # Reset the index so that time starts from 0 again
    catalysisDF.index = catalysisDF.index - catalysisDF.index[0]

    return (start_idx, end_idx), catalysisDF


def convert_area_to_amount(area_df, correction_factors):
    """
    Convert area DataFrame to amount DataFrame using correction factors.
    Parameters:
    - area_df: DataFrame with peak areas (output from integrate_peaks).
    - correction_factors: Dictionary with correction factors for each peak name.
    Returns:
    - DataFrame with amounts for each peak.
    """
    amounts = area_df.copy()
    for peak_name, factor in correction_factors.items():
        if peak_name in amounts.columns:
            amounts[peak_name] = amounts[peak_name] / factor
    return amounts

def internal_standard_correction(amounts_df, internal_standard, internal_standard_concentration):
    """
    Apply internal standard correction to the amounts DataFrame.
    Parameters:
    - amounts_df: DataFrame with amounts (output from convert_area_to_amount).
    - internal_standard: str, column name to use as internal standard (e.g., 'N2' or 'Ar').
    - internal_standard_concentration: float, known concentration of the internal standard.
    Returns:
    - DataFrame with corrected amounts and 'IS_correction_factor' column.
    """
    if amounts_df.empty or internal_standard not in amounts_df.columns:
        raise ValueError(f"Internal standard '{internal_standard}' not found in DataFrame columns.")

    corrected_amounts = amounts_df.copy()
    # Calculate IS_correction_factor as Ar (or chosen IS) divided by IS_concentration
    corrected_amounts['IS_correction_factor'] = corrected_amounts[internal_standard] / internal_standard_concentration

    # Ensure no negative values in IS_correction_factor
    corrected_amounts['IS_correction_factor'] = corrected_amounts['IS_correction_factor'].clip(lower=0.1)

    # Apply correction to all columns except the internal standard and IS_correction_factor
    for col in corrected_amounts.columns:
        if col not in [internal_standard, 'IS_correction_factor']:
            corrected_amounts[col] = corrected_amounts[col] / corrected_amounts['IS_correction_factor']

    return corrected_amounts

def plot_CO2_conversion(chromatograms):
    """
    Plot CO2 conversion from the chromatograms.
    Parameters:
    - chromatograms: List of Chromatogram objects.
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    file_datetimes = []
    CO2_conversions = []

    for chromatogram in chromatograms:
        if hasattr(chromatogram, 'file_datetime') and hasattr(chromatogram, 'CO2_conversion'):
            file_datetimes.append(chromatogram.file_datetime)
            CO2_conversions.append(chromatogram.CO2_conversion)

    ax.plot(file_datetimes, CO2_conversions, label='CO2 Conversion', marker='o', markersize=8)
    ax.set_xlabel('Datetime')
    ax.set_ylabel('CO2 Conversion (%)')
    ax.legend()
    plt.show()

