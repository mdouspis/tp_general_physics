from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import leastsq
from scipy.optimize import curve_fit
from scipy import asarray as ar,exp
from astropy import constants as const
from astropy import units as u
import h5py

plt.ion()

def gauss(x, a, x0, sigma):
    return a*exp(-(x-x0)**2/(2*sigma**2))

# Constant values
mh    = 1.6737236e-27 # kg
mu    = 1.25 * mh
k     = 1.38064852e-23 # J.K-1 --> m2.kg.s-2.K-1
G     = const.G.value # m3.kg-1.s-2
M_sun = const.M_sun.value # kg 

# Convertion tools
kpc2m  = u.kpc.to(u.m)
pc2cm  = u.pc.to(u.cm)

# HI4PI channel separation
dv = 1.29 #km.s-1
'''________________________________________________________________________________________________________'''
# The first step is to read the data using the HDF5 format. We can use the following link to see the documentation :
# Doc https://www.getdatajoy.com/learn/Read_and_Write_HDF5_from_Python
with h5py.File('data.h5','r') as hf:
    print('List of arrays in this file: \n', hf.keys())
    data        = hf.get('temperature')
    velocity    = hf.get('velocity')

    np_data     = np.array(data)
    np_velocity = np.array(velocity)
    print('Shape of the array data: \n', np_data.shape)
    print('Shape of the array velocity: \n', np_velocity.shape)

rms = 43.e-3

idx = np.where((np_velocity < -185000.) & (np_velocity > -225000.))
subcube = np_data[idx]
# hvc = subcube[:, 146:155, 175:199]
hvc = subcube[:, 144:158, 172:202]
clean_hvc = np.copy(hvc)
clean_hvc[np.where(hvc < 3. * rms)] = 0.

sum_clean_hvc = np.sum(clean_hvc, axis=0)
fig = plt.figure(1, figsize=(10,10))
ax1 = fig.add_subplot(111) 
ax1.imshow(sum_clean_hvc, interpolation = 'none')
plt.show()

spectra     = np.mean(clean_hvc, axis=(1,2))
vel_spectra = np_velocity[idx]

# http://stackoverflow.com/questions/10143905/python-two-curve-gaussian-fitting-with-non-linear-least-squares
x      = vel_spectra*1.e-3
y_real = spectra

n     = len(x)
mean  = np.sum(x * y_real) / np.sum(y_real) 
sigma = np.sqrt(np.sum((x - mean)**2 * y_real) / np.sum(y_real)) 

popt, pcov = curve_fit(gauss, x, y_real, p0 = [1, mean, sigma])
            
fig = plt.figure(2, figsize=(16,9))
ax1 = fig.add_subplot(111) 
ax1.plot(x, spectra, '.b', markersize=8)
ax1.plot(x, gauss(x,*popt), color='r')


theta = np.radians(15. * (51-29)/266.)

NHI = 1.82243e18 * np.sum(spectra) * dv # in cm-2
density_surf = NHI * mh * pc2cm**2 / M_sun # Msun.pc-2
dispersion = popt[2] * 1.e3 # m/s
Tk  = mh * dispersion**2 / k # K

d    = np.arange(1000) + 1 # kpc

b    = 41 # deg
z    = d * np.sin(np.radians(b))

nHI  = (NHI/1.e-4) / theta / (d * kpc2m) *1.e-6 # cm-3
Ps_k = (nHI * Tk) - ((mu**2 * G * (NHI/1.e-4)**2 * np.pi / 15. / k)*1.e-6)# K.cm-3

def P_k_Wolfire(z):
    return 2250. * (1. + (z**2 / 19.6))**(-1.35)

Ps_k_theory = P_k_Wolfire(z)

fig = plt.figure(3, figsize=(16,9))
ax1 = fig.add_subplot(111)
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_xlabel('$z (kpc)$', fontsize=18)
ax1.set_ylabel('$P_s.k^{-1} (K.cm^{-3})$', fontsize=18)
ax1.plot(z, Ps_k, color='r', linewidth=2., label='HVC stability')
ax1.plot(z, Ps_k_theory, color='b', linewidth=2., label='HIM (Wolfire et al. 1995)')
legend = ax1.legend(loc=1, shadow=True)
frame = legend.get_frame()
frame.set_facecolor('0.90')
for label in legend.get_texts():
    label.set_fontsize('large')
for label in legend.get_lines():
    label.set_linewidth(1.5)
plt.show()

