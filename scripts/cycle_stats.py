"""Per-cycle statistics from a force-coefficient time series.

The motion table (constant/motion.dat) has 400 points per cycle and OpenFOAM interpolates it linearly, so the
foil's acceleration arrives as a small kick every 5 steps (10 at T/4000) and the forces carry a matching saw-tooth.
Sampling the series at fixed phases can land on those kicks every time (it did, before 27 Nov 2026: the old
post-processing sampled exactly at the table points and over-weighted the kicks, e.g. Case II eta 11.23 % instead
of 10.90 %). Here every raw sample is used: each cycle is split into NBIN equal phase bins and averaged per bin.
Means are then exact time averages; peaks use a 7-bin moving average (3.5 % of a cycle), as before.
"""
import math
import numpy as np

NBIN = 200


def phase_bins(t, y, T, k, nbin=NBIN):
    """Bin-averaged values of y over cycle k (0-based); empty bins are filled by interpolation."""
    m = (t > k * T) & (t <= (k + 1) * T)
    ph = (t[m] - k * T) / T
    idx = np.minimum((ph * nbin).astype(int), nbin - 1)
    s = np.bincount(idx, weights=y[m], minlength=nbin); n = np.bincount(idx, minlength=nbin)
    out = np.full(nbin, np.nan); out[n > 0] = s[n > 0] / n[n > 0]
    if np.isnan(out).any():
        x = np.arange(nbin); good = ~np.isnan(out)
        out[~good] = np.interp(x[~good], x[good], out[good])
    return out


def peak(y):
    return float(np.max(np.abs(np.convolve(y, np.ones(7) / 7, mode="same"))))


def cycle_table(t, CX, CY, CM, CP, T, d, w):
    """One dict per complete cycle: eta (%), CP, CX (means), CY_peak, CM_peak, lift timing (deg)."""
    ncyc = int(np.floor(t[-1] / T + 1e-3))                    # tolerance: the last saved time can fall a hair short of n*T
    ph = (np.arange(NBIN) + 0.5) / NBIN
    rows = []
    for k in range(ncyc):
        m = (t > k * T) & (t <= (k + 1) * T)
        if m.sum() < 20:
            continue
        cy = phase_bins(t, CY, T, k); cm = phase_bins(t, CM, T, k)
        A, B = np.mean(cy * np.cos(2 * math.pi * ph)), np.mean(cy * np.sin(2 * math.pi * ph))
        timing = (math.degrees(math.atan2(B, A)) + 90 + 180) % 360 - 180   # heave velocity ~ cos(ph + 90 deg)
        cp = float(np.mean(CP[m]))
        rows.append(dict(cycle=k + 1, eta=100 * cp / d, CP=cp, CX=float(np.mean(CX[m])), CY_peak=peak(cy), CM_peak=peak(cm),
                         lift_timing_deg=timing))
    return rows


def phase_average(t, series, T, first, last):
    """Bin-averaged cycle shape over cycles first+1 .. last (1-based), for plotting."""
    ph = (np.arange(NBIN) + 0.5) / NBIN
    return ph, np.mean([phase_bins(t, series, T, k) for k in range(first, last)], axis=0)
