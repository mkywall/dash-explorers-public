import numpy as np
import lmfit as lm
from scipy.optimize import curve_fit as curve_fit
import h5py as h5
from lmfit.models import ExponentialModel, GaussianModel, LorentzianModel, VoigtModel, LinearModel
import matplotlib.pyplot as plt


def linear(x, m, b):
    x = np.array(x)
    return m*x + b

def normalize_data(arr, by_mean=False, id1=None, id2=None):
    """ Normalize ydata in an array/list to go from 0 to 1

    Args:
        arr (list/np.ndarray): array to normalize

    Returns:
        (np.ndarray) Scaled arr on range [0,1]
    """
    arr = np.array(arr)
    if by_mean:
         return (arr-np.mean(arr[id1:id2]))/(np.max(arr)-np.mean(arr[id1:id2]))
    else:
        return (arr-np.min(arr))/(np.max(arr)-np.min(arr))

def wv_range(x, wv1, wv2):
    """
    For a given array of energies, find index closest to specific start/stop points

    Args:
        x (np.ndarray) : array of energies
        wv1 (float or int) : first energy in range
        wv2 (float or int) : last energy in range

    Returns:
        start, stop (int): indices in x to get nearest to wv1, wv2
    """
    start = np.argmin(np.abs(x - wv1))
    stop = np.argmin(np.abs(x - wv2))
    return start, stop

def custom_function( x:np.ndarray, y:np.ndarray, npeaks:int, peakfunction:lm.models, backgroundfunction:lm.models, centers:list | np.ndarray, peaktol:float | int=100, diffpeaks:bool=False):
        """"
        Function to build custom lmfit model for an arbitrary spectra given spectra data, number of peaks to fit,
        function to fit background, function to fit peaks (currently all peaks fit with same function)

        Args:
            x: xdata / energies
            y: ydata / spectra to fit
            npeaks (int): Number of peaks to fit
            peakfunction (lmfit.models): Model to fit all peaks, typically LorenzianModel, GaussianModel, VoigtModel
            backgroundfuction (lmfit.models): Model to fit background, typically ExponentialModel, LinearModel
            centers (list): Initial guess for peak centers
            peaktol (int or float): Min/max range for peak center in fitting
            diffpeaks (bool): If you want to fit each peak to specific lorentzian/gaussian/voigt model

        Returns:
            out (lmfit.model.ModelResult): Model result
        """

        bg_pre_dir = {ExponentialModel:'bgexp_', LinearModel:'bglin_'}
        model = backgroundfunction(prefix=bg_pre_dir[backgroundfunction])
        pars = model.guess(y, x=x)

        if diffpeaks == False:
            pre_dir = {ExponentialModel:'exp', GaussianModel:'g', LorentzianModel:'l', VoigtModel:'v'}
            pre = pre_dir[peakfunction]

            for n in np.arange(npeaks):
                mod = peakfunction(prefix=f'{pre}{n}_')
                init_center = centers[n]

                pars += mod.guess(y, x=x, center=init_center)
                pars[f'{pre}{n}_amplitude'].min = 0
                pars[f'{pre}{n}_center'].min = init_center - peaktol
                pars[f'{pre}{n}_center'].max = init_center + peaktol
                # other constraints
                model += mod

        out = model.fit(y, pars, x=x)
        return out


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


class Raman_Thermometry:
    """
    For fitting MoS2 raman spectra from HiP microscope
    """
    def __init__(self, tool='HiP', filename = None, power_mw = [], wa = []):
        file = h5.File(filename)
        self.fn = filename
        self.tool = tool

        # The day of the experiment I will manually measure and record the power of the laser for specific ND filter wheel positions
        self.power_mw = power_mw #1009

        #ND filter wheel angles
        self.angles = wa
        self.power_dict = {angle:float(power) for angle, power in zip(self.angles, self.power_mw)}

        #postiion of filter wheel
        pos = dict(file[f'/hardware/power_wheel/settings'].attrs.items())['position']
        pos = find_nearest(self.angles, pos)
        self.power = self.power_dict[pos]


        if self.tool == 'HiP':
            self.wl = np.array(file['/measurement/picam_readout/raman_shifts'])
            self.spec = np.array(file['/measurement/picam_readout/spectrum'])

        self.pre_dir = {ExponentialModel:'exp', GaussianModel:'g', LorentzianModel:'l', VoigtModel:'v'}

    def fit_E_A(self, wv1=350, wv2=450, peakfunction=GaussianModel, backgroundfunction=ExponentialModel):
        """
        Function to fit E' and A' modes in raman spectra of MoS2
        Fit on a custom range
        The out result from custom func actually contains all the fitting parameters, here just looking at the peak locations, but may be worthwile to store
        all the pars if needed later, since they are available?

        Args:
            wv1: starting cm-1 of fit
            wv2: ending cm-1 of fit
            peakfunction (lmfit.models): Model to fit all peaks, typically LorenzianModel, GaussianModel, VoigtModel
            backgroundfuction (lmfit.models): Model to fit background, typically ExponentialModel, LinearModel
        Returns:
            peak1: E' fitted peak location
            peak1_err: Error on E'
            peak2: A' fitted peak location
            peak2_err: Error on A'
            x, y : selected raw data x and y to fit
            out.best_fit: best fit

        """
        start, stop = wv_range(self.wl, wv1,wv2)
        x = self.wl[start:stop]
        if self.tool == 'HiP':
            y = self.spec[start:stop]

            ###
            out = custom_function(x, y, 2, peakfunction, backgroundfunction, [390,410], peaktol=5)
            # just selecting the parameters of interest
            pre = self.pre_dir[peakfunction]
            peak1 = out.params[f'{pre}0_center'].value
            peak2 = out.params[f'{pre}1_center'].value
            peak1_err = out.params[f'{pre}0_center'].stderr
            peak2_err = out.params[f'{pre}1_center'].stderr
            # print(out.fit_report())
            if peak1_err == None:
                peak1_err = 0
                print('peak1_err returned None')
                print(self.fn)
            if peak2_err == None:
                peak2_err = 0
                print('peak2_err returned None')
                print(self.fn)
            return peak1, peak1_err, peak2, peak2_err, x, y, out.best_fit
