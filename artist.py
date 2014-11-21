__author__ = 'filipd'

import datetime
import tccon_site as ts
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from math import sin, cos, pi
import numpy as np
import utils


def make_meteo_figure(site, date, output_file):
    dd = date
    meteo = ts.Meteo(dd, site)

    if meteo.file_path is None:
        return

    xmin = mdates.date2num(datetime.datetime.combine(dd.date(), datetime.time.min))
    xmax = mdates.date2num(datetime.datetime.combine(dd.date(), datetime.time.max))

    rows = 4
    cols = 1
    tick_rotation = 45
    quarters = mdates.MinuteLocator(byminute=[15, 30, 45])
    hours = mdates.HourLocator()

    fig = plt.figure(figsize=[10, 10])
    gs = gridspec.GridSpec(rows, cols)
    gs.update(wspace=0.025, hspace=0.0)

    plt.subplot(gs[0])

    ax = plt.gca()
    ax.set_ylabel("Sun [W/m$^2$]")
    sdif = np.array(meteo.data["sdif"])
    sdir = np.array(meteo.data["sdir"])
    ax.fill_between(meteo.data["time"], 0, sdif, color="#ff800d", zorder=1)
    ax.fill_between(meteo.data["time"], sdif, sdir+sdif, color="#f9bb00", zorder=1)
    ax2 = ax.twinx()
    ax2.plot(meteo.data["time"], utils.get_sza(meteo.data["time"], -21, 55.5), color="r", zorder=2)
    ax2.set_ylim(0, 90)
    ax2.invert_yaxis()
    ax2.set_ylabel("SZA [$^\circ$]")
    hide_bottom_edge_ticks(ax)
    a = ax2.get_yticks().tolist()
    a[-1] = ''  # we invert the axis
    ax2.set_yticklabels(a)
    ax.set_xlim(xmin, xmax)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_minor_locator(quarters)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(''))
    tsl = ax.get_xticks().tolist()
    for i in range(len(tsl) - 1):
        if i % 2 == 0:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#eeeeee', edgecolor="none", zorder=0)
        else:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#dddddd', edgecolor="none", zorder=0)

    plt.subplot(gs[1])

    ln1 = plt.plot(meteo.data["time"], meteo.data["tout"], 'r', label="T")
    ax = plt.gca()
    ax2 = ax.twinx()
    ln2 = ax2.plot(meteo.data["time"], meteo.data["pout"], 'k', zorder=10, label="p")
    hide_bottom_edge_ticks(ax)
    hide_bottom_edge_ticks(ax2)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_minor_locator(quarters)
    ax.set_ylabel("Temperature [$^\circ$C]")
    ax2.set_ylabel("Pressure [hPa]")
    ax.set_xlim(xmin, xmax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(''))
    labs = [l.get_label() for l in ln1]
    ax.legend(ln1, labs, loc=2)
    labs = [l.get_label() for l in ln2]
    ax2.legend(ln2, labs, loc=1)
    for i in range(len(tsl) - 1):
        if i % 2 == 0:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#eeeeee', edgecolor="none", zorder=0)
        else:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#dddddd', edgecolor="none", zorder=0)

    plt.subplot(gs[2])

    ax = plt.gca()
    rain_window = utils.TimeSorter(meteo.data["time"], meteo.data["rain"], 30, 24.0*60.0)
    rain = []
    last_rain = 0
    for nr, a in enumerate(rain_window.window_values):
        rain.append(a[-1] - last_rain)
        last_rain = a[-1]
    ax.bar(rain_window.window_border_times[:-1], rain, width=rain_window.window_width, color="#99CCFF", edgecolor="none")
    hide_bottom_edge_ticks(ax)
    ax2 = ax.twinx()
    ax2.plot(meteo.data["time"], meteo.data["hout"], 'b', zorder=10)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_minor_locator(quarters)
    ax.set_ylabel("Rain duration [s]")
    ax2.set_ylabel("Rel. Humidity [%]")
    ax.set_xlim(xmin, xmax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(''))
    for i in range(len(tsl) - 1):
        if i % 2 == 0:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#eeeeee', edgecolor="none", zorder=0)
        else:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#dddddd', edgecolor="none", zorder=0)

    plt.subplot(gs[3])

    wspd = utils.TimeSorter(meteo.data["time"], meteo.data["wspd"], 10, 24.0*60.0)
    wdir = utils.TimeSorter(meteo.data["time"], meteo.data["wdir"], 10, 24.0*60.0)
    x = []
    y = []
    u = []
    v = []
    wspd_avg = wspd.get_mean_window_values()
    wdir_avg = wdir.get_mean_window_values()
    for no, a_time in enumerate(wdir.window_centre_times):
        x.append(mdates.date2num(a_time))
        y.append(wspd_avg[no])
        u.append(sin(-wdir_avg[no] * pi / 180.0))
        v.append(cos(-wdir_avg[no] * pi / 180.0))
    plt.plot(wspd.window_centre_times, wspd.get_mean_window_values(), marker=".", color="#1f88a7", zorder=2)
    plt.quiver(x, y, u, v, color="r", zorder=3)
    ax = plt.gca()
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_minor_locator(quarters)
    plt.xticks(rotation=-tick_rotation)
    ax.set_ylabel("Wind speed [m/s]")
    ax.set_xlabel(dd.strftime("{site}: %A %B %d, %Y".format(site=site)))
    ax.set_xlim(xmin, xmax)
    for i in range(len(tsl) - 1):
        if i % 2 == 0:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#eeeeee', edgecolor="none", zorder=0)
        else:
            ax.axvspan(tsl[i], tsl[i+1], facecolor='#dddddd', edgecolor="none", zorder=0)

    plt.savefig(output_file)


def make_retrieval_diagnostics_figure(oof_csv_file):

    data = utils.read_tccon_file(oof_csv_file)

    dates = np.array(utils.tccon_2_datetime(data["data"][2], data["data"][3], data["data"][4]))

    delta_days = abs((dates[-1] - dates[0]).days)

    molecules = [
        dict(name="XCO2 [ppm]", index=data["fields"].index("xco2_ppm"), color="b"),
        dict(name="XCH4 [ppm]", index=data["fields"].index("xch4_ppm"), color="r"),
        dict(name="XCO [ppb]", index=data["fields"].index("xco_ppb"), color="k"),
        dict(name="XN2O [ppb]", index=data["fields"].index("xn2o_ppb"), color="g"),
        dict(name="Xair [a.u.]", index=data["fields"].index("xair"), color="grey"),
        dict(name="LSE [a.u.]", index=data["fields"].index("LSE"), color="#C4ABFE"),
    ]

    diagnostics = [
        dict(name="FVSI [%]", index=data["fields"].index("fvsi_%"), color="orange"),
        dict(name="6220 FS [mK]", index=data["fields"].index("co2_6220_FS"), color="sandybrown"),
        dict(name="7885 FS [mK]", index=data["fields"].index("o2_7885_FS"), color="sandybrown"),
        dict(name="6220 S-G [ppm]", index=data["fields"].index("co2_6220_S-G"), color="chartreuse"),
        dict(name="7885 S-G [ppm]", index=data["fields"].index("o2_7885_S-G"), color="chartreuse"),
        dict(name="6220 VSF CO2 [a.u.]", index=data["fields"].index("co2_6220_VSF_co2"), color="b"),
        dict(name="7885 VSF O2 [a.u.]", index=data["fields"].index("o2_7885_VSF_o2"), color="grey"),
        dict(name="5790 VSF HCl [a.u.]", index=data["fields"].index("hcl_5790_VSF_hcl"), color="tomato"),
        dict(name="flag", index=data["fields"].index("flag"), color="tomato")
    ]

    flags = np.array(data["data"][data["fields"].index("flag")])
    mask = flags != 0
    points = len(flags)
    flagged = len(flags[mask])

    subplots = len(molecules) + len(diagnostics)

    plt.figure(figsize=[10, 2*subplots])
    plt.figtext(0.01, 0.99, oof_csv_file[-128:])
    plt.figtext(0.01, 0.98, "Data points: {0}, Flagged: {1}".format(points, flagged))

    gs = gridspec.GridSpec(subplots, 1)
    gs.update(wspace=0.025, hspace=0.0, top=0.97, bottom=0.03, right=0.97)

    if delta_days < 1:
        marker = "o"
    elif delta_days > 11:
        marker = "."

    if delta_days < 1:
        minor = mdates.MinuteLocator(byminute=[15, 30, 45])
        major = mdates.HourLocator()
        date_format = "%H:%M"
    elif delta_days < 11:
        minor = mdates.HourLocator(byhour=[6, 12, 18])
        major = mdates.DayLocator()
        date_format = "%a %d %b, %Y"
    elif delta_days < 201:
        minor = mdates.DayLocator()
        major = mdates.MonthLocator(bymonthday=[1, 10, 20])
        date_format = "%b %d, %Y"
    elif delta_days < 401:
        minor = mdates.MonthLocator(bymonthday=[10, 20])
        major = mdates.MonthLocator(bymonthday=1)
        date_format = "%b-%Y"
    else:
        minor = mdates.MonthLocator(bymonthday=1)
        major = mdates.MonthLocator(bymonthday=1, interval=3)
        date_format = "%b-%Y"

    for no, molecule in enumerate(molecules):
        plt.subplot(gs[0 + no])
        all_dat = np.array(data["data"][int(molecule["index"])])
        plt.errorbar(dates, all_dat, yerr=data["data"][int(molecule["index"]) + 1],
                     fmt='.', color=molecule["color"])
        flag_color = "k"
        if molecule["color"] == "k":
            flag_color = "r"
        plt.plot(dates[mask], all_dat[mask], color=flag_color, marker=".", linestyle="none")
        plt.ylabel(molecule["name"])
        ax = plt.gca()
        hide_bottom_edge_ticks(ax)
        ax.xaxis.set_major_locator(major)
        ax.xaxis.set_minor_locator(minor)
        ax.axes.get_xaxis().set_ticklabels([])

    for no, diagnosis in enumerate(diagnostics):
        plt.subplot(gs[0 + no + len(molecules)])
        all_dat = np.array(data["data"][int(diagnosis["index"])])
        plt.plot(dates, all_dat, color=diagnosis["color"], marker=marker, linestyle="none")
        flag_color = "k"
        if diagnosis["color"] == "k":
            flag_color = "r"
        plt.plot(dates[mask], all_dat[mask], color=flag_color, marker=marker, linestyle="none")
        plt.ylabel(diagnosis["name"])
        ax = plt.gca()
        hide_bottom_edge_ticks(ax)
        ax.xaxis.set_major_locator(major)
        ax.xaxis.set_minor_locator(minor)
        ax.axes.get_xaxis().set_ticklabels([])

    plt.xticks(rotation=30)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))


    plt.savefig("/home/filipd/temp/test.png")


def hide_bottom_edge_ticks(ax):
    a = ax.get_yticks().tolist()
    lower = ax.get_ylim()[0]
    for ni, val in enumerate(a):
        if val <= lower:
            a[ni] = ""
        else:
            continue
    ax.set_yticklabels(a)


def tracker_diagnostics(tracker_log):
    data = utils.read_tracker_log(tracker_log)

    figs = [
        dict(col=8, label="Cam. score [pixels]", color="r"),
        dict(col=7, label="4Q score [V]", color="grey"),
        dict(col=4, label="Tracker elev. [deg.]", color="b"),
        dict(col=3, label="Tracker azim. [deg.]", color="g"),
    ]

    gs = gridspec.GridSpec(len(figs), 1)
    gs.update(wspace=0.025, hspace=0.0, top=0.97, bottom=0.03, right=0.97)

    for no, item in enumerate(figs):
        plt.subplot(gs[no])
        plt.plot(data["data"][0], data["data"][item["col"]], color=item["color"], marker='.')
        plt.ylabel(item["label"])
        ax = plt.gca()
        hide_bottom_edge_ticks(ax)
    plt.savefig("/home/filipd/temp/tracker.png")