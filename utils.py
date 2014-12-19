__author__ = 'filipd'
import os
import datetime
import numpy as np
import matplotlib.dates as mdates
#import Pysolar
from settings import DAY_TCCON_DIR, TRACKER_LOG
import artist


def read_tccon_file(file_path):
    """
    read_tccon_file(file_path)

    --- Inputs --------------------------

    file_path: the path to a TCCON file

    --- Information ---------------------

    Reads the data in a TCCON file.  Returns a dictionary containing the data (key: data), column titles (key: fields),
    and the structure of the file (i.e. the numbers on the first line of the file) (key: format)
    """
    if not os.path.exists(file_path):
        raise IOError
    if os.path.splitext(file_path)[1] == ".csv":  # Choose the field separator based on the file extension
        separator = ","
    else:
        separator = " "

    data = []
    fields = []
    file_format = []

    with open(file_path, 'r') as fid:
        for ind, line in enumerate(fid):  # according to the docs this is faster than using the readline() method on fid
            if ind == 0:  # the first line in the file specifies the structure of the file and its data matrix
                try:
                    file_format = [int(x) for x in line.split(" ") if x]
                    # format[0] is the number of header lines in the file
                    # format[1] is the number of columns of data in the file
                    # format[2] is the number of rows of data in the file
                    # format[4] is a mystery
                    # In general, the last line of the header contains the column titles
                    data = [[] for _x in range(file_format[1])]  # [[]] * 6 just gives 6 refs to the same list
                except ValueError:
                    raise ValueError
            elif ind == file_format[0]-1:
                fields = [x for x in line.strip().split(separator) if x]  # get the column titles
            elif ind >= file_format[0]:
                row = [x for x in line.strip().split(separator) if x]
                for k, item in enumerate(row):
                    try:  # try converting the string to a float or integer
                        data[k].append(int(item))  # First try to convert to integer (will fail on e.g. "1.0")
                    except ValueError:
                        try:
                            data[k].append(float(item))  # Then try conversion to float (will fail on text strings)
                        except ValueError:
                            data[k].append(item)  # Just add the text string

    return {'data': data, 'fields': fields, 'format': file_format}


def tccon_2_datetime(year, doy, hour):
    """
    tccon_2_datetime(year, doy, hour)

    --- Inputs --------------------------

    year: A list of year entries
    doy: A list of day-of-year entries
    hour: A list of decimal hours

    --- Information ---------------------

    Converts the typical TCCON year-doy-hour date format into the python datetime format.
    """
    dates = []
    if not (len(year) == len(doy) and len(doy) == len(hour)):
        raise ValueError
    for j in range(len(year)):
        # January 1 is doy == 1 in the TCCON files
        dates.append(datetime.datetime(int(year[j]), 1, 1) + datetime.timedelta(days=(doy[j] - 1) + float(hour[j]/24)))
    return dates


class TimeSorter(object):
    """An object that sorts time-based values into time brackets
    """
    def __init__(self, times, values, minutes, range_minutes):
        self.times = times
        self.date = datetime.datetime.combine(self.times[0].date(), datetime.time.min)
        self.values = values
        self.minutes = minutes  # width of each time window in minutes
        self.range_minutes = range_minutes  # e.g. 24.0 * 60.0 for a full day
        self.window_border_times = []
        self.window_centre_times = []
        self.window_width = 0.0
        self.window_values = []
        self.window_times = []
        self.sort_by_time_interval()

    def sort_by_time_interval(self):
        max_idx = int(self.range_minutes / self.minutes)
        self.window_border_times = [self.date+datetime.timedelta(minutes=m*self.minutes) for m in range(max_idx + 1)]
        self.window_centre_times = [self.date+datetime.timedelta(minutes=(m+0.5)*self.minutes) for m in range(max_idx)]
        self.window_width = mdates.date2num(self.window_border_times[1]) - mdates.date2num(self.window_border_times[0])
        self.window_values = []
        self.window_times = []
        for _d in range(max_idx):
            self.window_values.append([])
            self.window_times.append([])

        for idx, a_time in enumerate(self.times):
            for no in range(max_idx):
                if self.window_border_times[no] <= a_time < self.window_border_times[no+1]:
                    self.window_values[no].append(self.values[idx])
                    self.window_times[no].append(a_time)
                    continue

    def get_mean_window_values(self):
        temp = []
        for no, a_list in enumerate(self.window_values):
            if len(a_list) > 0:
                avg = np.mean(np.array(a_list))
            else:
                avg = np.nan
            temp.append(avg)
        return temp


def get_sza(times, lat, long):
    output = []
    for a_time in times:
        angle = Pysolar.GetAltitude(lat, long, a_time)
        if angle > 0.0:
            angle = 90.0 - angle
        else:
            angle = np.nan
        output.append(angle)
    return output


def read_tracker_log(tracker_log):
    """ Reads data from the log file of the solar tracker (TrackerCam)
    """
    data = {}
    values = []
    with open(tracker_log, 'ra') as fid:
        for no, line in enumerate(fid):
            if no == 2:  # the second line contains the column titles
                data["fields"] = line.strip().split("\t")
                values = [[] for _x in range(len(data["fields"]))]  # [[]] * 6 just gives 6 refs to the same list
                continue
            elif no < 3:  # skip the header
                continue
            new_data = line.strip().split("\t")
            for nr, a_value in enumerate(new_data):
                if nr == 0:
                    values[nr].append(datetime.datetime.strptime(a_value, "%H:%M:%S"))
                else:
                    try:
                        values[nr].append(int(a_value))  # fails on e.g. "1.0"
                    except ValueError:
                        try:
                            values[nr].append(float(a_value))
                        except ValueError:
                            values[nr].append(a_value)
        data["data"] = values
    return data


def create_filelist(site, start_date, output_file, end_date=None):
    """ Write a filelist file for the specified site and date range
    If no optional end date is given, today is taken as the end date.
    
    Arguments:
    site -- name of the site for which to create the filelist
    start_date -- (datetime) starting date of the filelist
    output_file -- file to which the file list will be written, any existing file is overwritten without warning
    
    Optional arguments:
    end_date -- end date of the file list
    """
    if end_date is None:
      end_date = datetime.datetime.today()
    
    day = datetime.timedelta(days=1)
    file_list = []
    site_dir = DAY_TCCON_DIR.format(site=site)
    
    next_date = start_date
    while next_date < end_date:
      archdir = next_date.strftime(site_dir)
      next_date += day
      if not os.path.exists(archdir):
	continue
      files = os.listdir(archdir)
      for item in files:
	if "dual" in item or 'ingaas' in item:
	  file_list.append(os.path.join(archdir, item) + "\n")
      
    with open(output_file, 'w') as fid:
      fid.writelines(file_list)


def tracker_diagnostics(site, start_date, end_date):
    """Create a tracker diagnostics figure for a site for all dates in the specified range.

    Arguments:

    site -- Name of the site
    start_date -- A datetime, start of the date range
    end_date -- A datetime, end of the date range
    """
    day = datetime.timedelta(days=1)
    today = start_date
    while today <= end_date:
	log_file = today.strftime(TRACKER_LOG.format(site=site))
	if os.path.exists(log_file):
	    artist.tracker_diagnostics(log_file, figure_file=today.strftime("tracker%Y%m%d"))
	today += day
