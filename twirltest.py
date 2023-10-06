import numpy as np

from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
import twirl

# Open some FITS image
hdu = fits.open("solve.fits")[0]

# get the center of the image
ra, dec = hdu.header["RA"], hdu.header["DEC"]
center = SkyCoord(ra, dec, unit=["deg", "deg"])

# and the size of its field of view
pixel = 0.66 * u.arcsec  # known pixel scale
shape = hdu.data.shape
fov = np.max(shape) * pixel.to(u.deg)

sky_coords = twirl.gaia_radecs(center, 1.2 * fov)[0:12]

# detect stars in the image
pixel_coords = twirl.find_peaks(hdu.data)[0:12]

# compute the World Coordinate System
wcs = twirl.compute_wcs(pixel_coords, sky_coords)

print(wcs)