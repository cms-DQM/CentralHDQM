from .basic import BaseMetric

VERBOSE = False

# ---- L1 Efficiency related
from math import sqrt


class EffMean(BaseMetric):
    def calculate(self, histo):
        mean = histo.GetSumOfWeights() / histo.GetEntries()
        err = mean / sqrt(histo.GetEntries())
        return (mean, err)


### to look deeper: GetMean(2) gives sumwy / sumw , with error of sqrt(sumwy2 / sumw - mean^2)
###                 each bin is fill with 1 entry? Or TEfficiency?
###        need to know what is in sumwy


def EffMeanRange(histo, ibin_min, ibin_max):
    total_entry = 0
    total_val = 0
    for ibin in range(ibin_min, ibin_max + 1):
        if histo.GetBinContent(ibin) == 0:
            continue  ## in Eff vs phi plot, the first bin and the last bin are empty
        bin_entry = (histo.GetBinContent(ibin) / histo.GetBinError(ibin)) ** 2.0
        total_entry += bin_entry
        total_val += bin_entry * histo.GetBinContent(ibin)
    if total_entry == 0:
        return (0, 0)
    mean = total_val / total_entry
    stat_err = mean / sqrt(total_entry)
    if VERBOSE:
        print(mean, stat_err)
    return (mean, stat_err)


def EffStdDev(histo, ibin_min, ibin_max):
    total_entry = 0
    total_val_sq = 0
    # val_err_calc  = 0
    for ibin in range(ibin_min, ibin_max + 1):
        if histo.GetBinContent(ibin) == 0:
            continue  ## in Eff vs phi plot, the first bin and the last bin are empty
        bin_entry = (histo.GetBinContent(ibin) / histo.GetBinError(ibin)) ** 2.0
        total_entry += bin_entry
        total_val_sq += bin_entry * histo.GetBinContent(ibin) ** 2.0
    # val_err_calc += (bin_entry ** 2.0) * (histo.GetBinContent(ibin) ** 2.0) * (histo.GetBinError(ibin) ** 2.0)
    if total_entry == 0:
        return (0, 0)
    mean, mean_err = EffMeanRange(histo, ibin_min, ibin_max)
    std = sqrt(total_val_sq / total_entry - mean**2.0)
    std_err = (mean * mean_err) / (sqrt(ibin_max + 1 - ibin_min) * std)
    ## this is the err based on the approximation that the underlying distribution
    ## each bin is the same, and that we have used mean/sqrt(total+entry) as the mean_err
    ## the actual error propagation in as following

    ## std_err = sqrt(val_err_calc) / total_entry / std
    ## simplified from the error propagation derived from the calculation of std
    ## larger than expected, need to understand the reason
    ## in the limit of infinite stats in each bin, std_err = mean_eff / sqrt(Nbins) ...
    if VERBOSE:
        print(std_err)
    return (std, std_err)


class EffMean(BaseMetric):
    def calculate(self, histo):
        if VERBOSE:
            print(histo.GetSumOfWeights())
        if VERBOSE:
            print(histo.GetEntries())
        if VERBOSE:
            print("running EffMeanTest \n\n")
        return EffMeanRange(histo, 1, histo.GetNbinsX())


class EffVariance(BaseMetric):
    def calculate(self, histo):
        #  std, err = EffStdDev(histo, 1, histo.GetNbinsX())
        #  print ("MeanError(2)")
        #  print (histo.GetMeanError(2))
        return EffStdDev(histo, 1, histo.GetNbinsX())


# ---- Efficiency Turn On related


# functions used by efficiency turn on calculations
def EffTurnOnPoint(eff, histo):
    point_bin = 0
    for ibin in range(1, histo.GetNbinsX() - 1):
        if histo.GetBinContent(ibin) <= eff and histo.GetBinContent(ibin + 1) > eff:
            point_bin = ibin
            break  # to avoid empty bins in high pt region
    if VERBOSE:
        print(point_bin)
    return point_bin


def GetYErr(ibin, histo):
    from math import sqrt

    if histo.GetBinError(ibin) < histo.GetBinContent(ibin):
        return histo.GetBinError(ibin)
    if VERBOSE:
        print(histo.GetEntries())
    return histo.GetBinContent(ibin) / sqrt(
        histo.GetBinContent(ibin) * histo.GetEntries() / (histo.GetNbinsX() * 2.0)
    )
    # simplified from binomial std from numer and denom


def EffTurnOnEtAndErr(eff, ibin, histo):
    from math import sqrt

    weight_1 = (histo.GetBinContent(ibin + 1) - eff) / (
        histo.GetBinContent(ibin + 1) - histo.GetBinContent(ibin)
    )
    weight_2 = (eff - histo.GetBinContent(ibin)) / (
        histo.GetBinContent(ibin + 1) - histo.GetBinContent(ibin)
    )
    slope_inv = (histo.GetBinCenter(ibin + 1) - histo.GetBinCenter(ibin)) / (
        histo.GetBinContent(ibin + 1) - histo.GetBinContent(ibin)
    )

    errX_1 = histo.GetBinWidth(ibin) * sqrt(1.0 / 12)
    errX_2 = histo.GetBinWidth(ibin + 1) * sqrt(1.0 / 12)
    errY_1 = GetYErr(ibin, histo)
    errY_2 = GetYErr(ibin + 1, histo)

    if (
        errY_1 / histo.GetBinContent(ibin) > 0.2
        or errY_2 / histo.GetBinContent(ibin + 1) > 0.2
    ):
        return (0, 0)

    eff_energy = weight_1 * histo.GetBinCenter(ibin) + weight_2 * histo.GetBinCenter(
        ibin + 1
    )
    energy_err = sqrt(
        pow(weight_1 * errX_1, 2.0)
        + pow(weight_2 * errX_2, 2.0)
        + pow(slope_inv * weight_1 * errY_1, 2.0)
        + pow(slope_inv * weight_2 * errY_2, 2.0)
    )

    if VERBOSE:
        print("%.2f +/- %.2f" % (eff_energy, energy_err))
    return (round(eff_energy, 2), round(energy_err, 2))


# End of functions def


class TurnOnCurveEffPoint(BaseMetric):
    def __init__(self, eff_point):
        self.__eff_point = float(eff_point)

    def calculate(self, histo):
        if self.__eff_point < 0 or self.__eff_point > 1:
            return (0, 0)
        ibin = EffTurnOnPoint(self.__eff_point, histo)
        if ibin == 0:
            return (0, 0)
        return EffTurnOnEtAndErr(self.__eff_point, ibin, histo)


class TurnOnCurveHalfWidth(BaseMetric):
    def calculate(self, histo):
        from math import sqrt

        ibin_20 = EffTurnOnPoint(0.2, histo)
        ibin_80 = EffTurnOnPoint(0.8, histo)
        if ibin_20 >= ibin_80 or ibin_20 == 0:
            return (0, 0)

        energy_20, err_20 = EffTurnOnEtAndErr(0.2, ibin_20, histo)
        energy_80, err_80 = EffTurnOnEtAndErr(0.8, ibin_80, histo)
        err_width = sqrt(err_20**2.0 + err_80**2.0)
        if energy_20 == 0 or energy_80 == 0:
            return (0, 0)
        return (energy_80 - energy_20, err_width)


class TurnOnCurveRange(BaseMetric):
    def calculate(self, histo):
        start_bin = 0
        saturate_bin = 0
        for ibin in range(1, histo.GetNbinsX() - 1):
            if histo.GetBinContent(ibin) == 0 and histo.GetBinContent(ibin + 1) > 0:
                start_bin = ibin
                break
        for ibin in range(1, histo.GetNbinsX() - 1):
            if histo.GetBinContent(ibin) != 0 and histo.GetBinContent(ibin) != 1.0:
                saturate_bin = ibin
        if saturate_bin == 0:
            return (0, 0)
        start_energy = histo.GetBinCenter(start_bin)
        saturate_energy = histo.GetBinCenter(saturate_bin)

        if VERBOSE:
            print(start_energy, saturate_energy)
        return (
            (saturate_energy + start_energy) / 2.0,
            (saturate_energy - start_energy) / 2.0,
        )


class TurnOnPlateauEff(BaseMetric):
    def calculate(self, histo):
        if VERBOSE:
            print("calculating plateau")
        TOEP = TurnOnCurveEffPoint(0.5)
        TOHW = TurnOnCurveHalfWidth()
        midpoint, mp_err = TOEP.calculate(histo)
        halfwidth, hw_err = TOHW.calculate(histo)

        if VERBOSE:
            print("got midpoint and halfwidth")
        if VERBOSE:
            print(midpoint, halfwidth)
        if midpoint == 0 or halfwidth == 0:
            return (0, 0)
        plateau_val = midpoint + 2.0 * halfwidth
        plateau_bin = 0
        for ibin in range(1, histo.GetNbinsX()):
            if (
                histo.GetBinCenter(ibin) < plateau_val
                and histo.GetBinCenter(ibin + 1) >= plateau_val
            ):
                plateau_bin = ibin + 1
                break
        if plateau_bin == 0:
            return (0, 0)

        if VERBOSE:
            print("plateau_bin = %d" % plateau_bin)
        if VERBOSE:
            print("eff and err are")
        if VERBOSE:
            print(EffMeanRange(histo, plateau_bin, histo.GetNbinsX()))
        return EffMeanRange(histo, plateau_bin, histo.GetNbinsX())


class TauSavePlots(BaseMetric):
    def calculate(self, histo):
        return (0, 0)
