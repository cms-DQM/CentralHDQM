from .basic import BaseMetric


class NOutsideRange(BaseMetric):
    def __init__(self, low, high):
        self.__low = low
        self.__high = high

    def calculate(self, histo):
        from math import sqrt

        s = histo.Integral(histo.FindBin(self.__low), histo.FindBin(self.__high))
        T = histo.Integral()
        B = T - s
        return (B, 0)


class MeanCh(BaseMetric):
    def __init__(self, ch):
        self.__ch = int(ch)

    def calculate(self, histo):
        tot, count = 0.0, 0

        for iX in range(0, histo.GetXaxis().GetNbins() + 1):
            tot += histo.GetBinContent(iX, self.__ch)
            count += 1

        if count < 1:
            return (0, 0)

        return (tot / float(count), 0)
