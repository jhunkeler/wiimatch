"""
A module that provides core algorithm for optimal matching of backgrounds of
N-dimensional images using (multi-variate) polynomials.

:Author: Mihai Cara (contact: help@stsci.edu)

:License: :doc:`../LICENSE`

"""
from __future__ import (absolute_import, division, unicode_literals,
                        print_function)

import copy
import sets

import numpy as np

from .utils import create_coordinate_arrays


__all__ = ['build_lsq_eqs', 'lsq_solve']


def build_lsq_eqs(images, masks, sigmas, degree, center=None,
                  image2world=None):
    """
    Build system of linear equations whose solution would provide image
    intensity matching in the least squares sense.

    Parameters
    ----------
    images : list of numpy.ndarray
        A list of 1D, 2D, etc. `numpy.ndarray` data array whose "intensities"
        must be "matched". All arrays must have identical shapes.

    masks : list of numpy.ndarray
        A list of `numpy.ndarray` arrays of same length as ``images``.
        Non-zero mask elements indicate valid data in the corresponding
        ``images`` array. Mask arrays must have identical shape to that of
        the arrays in input ``images``.

    sigmas : list of numpy.ndarray
        A list of `numpy.ndarray` data array of same length as ``images``
        representing the uncertainties of the data in the corresponding array
        in ``images``. Uncertainty arrays must have identical shape to that of
        the arrays in input ``images``.

    degree : iterable
        A list of polynomial degrees for each dimension of data arrays in
        ``images``. The length of the input list must match the dimensionality
        of the input images.

    center : iterable, None
        An iterable of length equal to the number of dimensions in
        ``images`` data arrays that indicates the center of the coordinate
        system in **image** coordinates. When ``center`` is `None` then
        ``center`` is set to the middle of the "image" as
        ``center[i]=image_shape[i]//2``. If ``image2world`` is not `None`,
        then center will first be converted to world coordinates.

    image2world : function, None
        Image-to-world coordinates transformation function. This function
        must be of the form ``f(x,y,z,...)`` and accept a number of arguments
        `numpy.ndarray` arguments equal to the dimensionality of images.

    Returns
    -------
    a : numpy.ndarray
        A 2D `numpy.ndarray` that holds the coefficients of the linear system
        of equations.

    b : numpy.ndarray
        A 1D `numpy.ndarray` that holds the free terms of the linear system of
        equations.

    Notes
    -----
    :py:func:`build_lsq_eqs` builds a system of linear equations

    .. math::
        a \\cdot c = b

    whose solution :math:`c` is a set of coefficients of (multivariate)
    polynomials that represent the "background" in each input image (these are
    polynomials that are "corrections" to intensities of input images) such
    that the following sum is minimized:

    .. math::
        L = \sum^N_{n,m=1,n \\neq m} \sum_k\
\\frac{\\left[I_n(k) - I_m(k) - P_n(k) + P_m(k)\\right]^2}\
{\sigma^2_n(k) + \sigma^2_m(k)}.

    In the above equation, index :math:`k=(k_1,k_2,...)` labels a position
    in input image's pixel grid [NOTE: all input images share a common
    pixel grid].

    "Background" polynomials :math:`P_n(k)` are defined through the
    corresponding coefficients as:

    .. math::
        P_n(k_1,k_2,...) = \sum_{d_1=0,d_2=0,...}^{D_1,D_2,...} \
c_{d_1,d_2,...}^n \\cdot k_1^{d_1} \\cdot k_2^{d_2}  \\cdot \\ldots .

    Coefficients :math:`c_{d_1,d_2,...}^n` are arranged in the vector :math:`c`
    in the following order:

    .. math::
        (c_{0,0,\\ldots}^1,c_{1,0,\\ldots}^1,\\ldots,c_{0,0,\\ldots}^2,\
c_{1,0,\\ldots}^2,\\ldots).

    Examples
    --------
>>> import wiimatch
>>> import numpy as np
>>> im1 = np.zeros((5, 5, 4), dtype=np.float)
>>> cbg = 1.32 * np.ones_like(im1)
>>> ind = np.indices(im1.shape, dtype=np.float)
>>> im3 = cbg + 0.15 * ind[0] + 0.62 * ind[1] + 0.74 * ind[2]
>>> mask = np.ones_like(im1, dtype=np.int8)
>>> sigma = np.ones_like(im1, dtype=np.float)
>>> a, b = wiimatch.lsq_optimizer.build_lsq_eqs([im1, im3], [mask, mask],
... [sigma, sigma], degree=(1,1,1), center=(0,0,0))
>>> print(a)
[[   50.   100.   100.   200.    75.   150.   150.   300.   -50.  -100.
   -100.  -200.   -75.  -150.  -150.  -300.]
 [  100.   300.   200.   600.   150.   450.   300.   900.  -100.  -300.
   -200.  -600.  -150.  -450.  -300.  -900.]
 [  100.   200.   300.   600.   150.   300.   450.   900.  -100.  -200.
   -300.  -600.  -150.  -300.  -450.  -900.]
 [  200.   600.   600.  1800.   300.   900.   900.  2700.  -200.  -600.
   -600. -1800.  -300.  -900.  -900. -2700.]
 [   75.   150.   150.   300.   175.   350.   350.   700.   -75.  -150.
   -150.  -300.  -175.  -350.  -350.  -700.]
 [  150.   450.   300.   900.   350.  1050.   700.  2100.  -150.  -450.
   -300.  -900.  -350. -1050.  -700. -2100.]
 [  150.   300.   450.   900.   350.   700.  1050.  2100.  -150.  -300.
   -450.  -900.  -350.  -700. -1050. -2100.]
 [  300.   900.   900.  2700.   700.  2100.  2100.  6300.  -300.  -900.
   -900. -2700.  -700. -2100. -2100. -6300.]
 [  -50.  -100.  -100.  -200.   -75.  -150.  -150.  -300.    50.   100.
    100.   200.    75.   150.   150.   300.]
 [ -100.  -300.  -200.  -600.  -150.  -450.  -300.  -900.   100.   300.
    200.   600.   150.   450.   300.   900.]
 [ -100.  -200.  -300.  -600.  -150.  -300.  -450.  -900.   100.   200.
    300.   600.   150.   300.   450.   900.]
 [ -200.  -600.  -600. -1800.  -300.  -900.  -900. -2700.   200.   600.
    600.  1800.   300.   900.   900.  2700.]
 [  -75.  -150.  -150.  -300.  -175.  -350.  -350.  -700.    75.   150.
    150.   300.   175.   350.   350.   700.]
 [ -150.  -450.  -300.  -900.  -350. -1050.  -700. -2100.   150.   450.
    300.   900.   350.  1050.   700.  2100.]
 [ -150.  -300.  -450.  -900.  -350.  -700. -1050. -2100.   150.   300.
    450.   900.   350.   700.  1050.  2100.]
 [ -300.  -900.  -900. -2700.  -700. -2100. -2100. -6300.   300.   900.
    900.  2700.   700.  2100.  2100.  6300.]]
>>> print(b)
[ -198.5  -412.   -459.   -948.   -344.   -710.5  -781.  -1607.    198.5
   412.    459.    948.    344.    710.5   781.   1607. ]

    """
    nimages = len(images)

    if nimages != len(sigmas):
        raise ValueError("Length of sigmas list must match the length of the "
                         "image list.")

    # exclude pixels that have non-positive associated sigmas except the case
    # when all sigmas are non-positive
    for m, s in zip(masks, sigmas):
        ps = (s > 0)
        if not np.all(~ps):
            m &= ps

    # compute squares of sigmas for repeated use later
    sigmas2 = [s**2 for s in sigmas]

    degree1 = tuple([d + 1 for d in degree])

    npolycoeff = 1
    for d in degree1:
        npolycoeff *= d
    sys_eq_array_size = nimages * npolycoeff

    gshape = (nimages,) + degree1

    # pre-compute coordinate arrays:
    coord_arrays = create_coordinate_arrays(images[0].shape, center=center,
                                            image2world=image2world)

    # allocate array for the coefficients of the system of equations (a*x=b):
    a = np.zeros((sys_eq_array_size, sys_eq_array_size), dtype=np.float)
    b = np.zeros(sys_eq_array_size, dtype=np.float)

    for i in range(sys_eq_array_size):
        # decompose first (row, or eq) flat index into "original" indices:
        lp = np.unravel_index(i, gshape)
        l = lp[0]
        p = lp[1:]

        # compute known terms:
        for m in range(nimages):
            if m == l:
                continue

            # compute array elements for m!=l:
            b[i] += _image_pixel_sum(
                image_l = images[l],
                image_m = images[m],
                mask_l = masks[l],
                mask_m = masks[m],
                sigma2_l = sigmas2[l],
                sigma2_m = sigmas2[m],
                coord_arrays=coord_arrays,
                p=p
            )

        for j in range(sys_eq_array_size):

            # decompose second (col, or cf) flat index into "original" indices:
            mp = np.unravel_index(j, gshape)
            m = mp[0]
            pp = mp[1:]

            if l == m:  # we will deal with this case in the next iteration
                continue

            a[i, j] = -_sigma_pixel_sum(
                mask_l = masks[l],
                mask_m = masks[m],
                sigma2_l = sigmas2[l],
                sigma2_m = sigmas2[m],
                coord_arrays=coord_arrays,
                p=p,
                pp=pp
            )

    # now compute coefficients of array 'a' for l==m:
    zero_deg = tuple(len(degree) * [0])
    for i in range(sys_eq_array_size):
        # decompose first (row, or eq) flat index into "original" indices:
        lp = np.unravel_index(i, gshape)
        l = lp[0]
        p = lp[1:]

        for ppi in range(npolycoeff):
            pp = np.unravel_index(ppi, degree1)
            j = np.ravel_multi_index((l,) + pp, gshape)

            for m in range(nimages):
                if m == l:
                    continue
                k = np.ravel_multi_index((m,) + pp, gshape)
                a[i, j] -= a[i, k]

    return a, b


def lsq_solve(matrix, free_term, nimages=None):
    """
    Computes least-square solution of a system of linear equations

    .. math::
        a \\cdot c = b.

    Parameters
    ----------
    matrix : numpy.ndarray
        A 2D array containing coefficients of the system.

    free_term : numpy.ndarray
        A 1D array containing free terms of the system of the equations.

    nimages : int, None
        Number of images for which the system is being solved.

    Returns
    -------
    bkg_poly_coeff : numpy.ndarray
        When ``nimages`` is `None`, this function returns a 1D `numpy.ndarray`
        that holds the solution (polynomial coefficients) to the system.

        When ``nimages`` is **not** `None`, this function returns a 2D
        `numpy.ndarray` that holds the solution (polynomial coefficients)
        to the system. The solution is grouped by image.

    Examples
    --------
>>> import wiimatch
>>> import numpy as np
>>> im1 = np.zeros((5, 5, 4), dtype=np.float)
>>> cbg = 1.32 * np.ones_like(im1)
>>> ind = np.indices(im1.shape, dtype=np.float)
>>> im3 = cbg + 0.15 * ind[0] + 0.62 * ind[1] + 0.74 * ind[2]
>>> mask = np.ones_like(im1, dtype=np.int8)
>>> sigma = np.ones_like(im1, dtype=np.float)
>>> a, b = wiimatch.lsq_optimizer.build_lsq_eqs([im1, im3], [mask, mask],
... [sigma, sigma], degree=(1,1,1), center=(0,0,0))
>>> wiimatch.lsq_optimizer.lsq_solve(a, b, 2)
array([[ -6.60000000e-01,  -7.50000000e-02,  -3.10000000e-01,
          3.33066907e-15,  -3.70000000e-01,   5.44009282e-15,
          7.88258347e-15,  -2.33146835e-15],
       [  6.60000000e-01,   7.50000000e-02,   3.10000000e-01,
         -4.44089210e-15,   3.70000000e-01,  -4.21884749e-15,
         -7.43849426e-15,   1.77635684e-15]])

    """
    v = np.dot(np.linalg.pinv(matrix), free_term)
    bkg_poly_coeff = v.reshape((nimages, v.size // nimages))
    return bkg_poly_coeff


def _image_pixel_sum(image_l, image_m, mask_l, mask_m,
                     sigma2_l, sigma2_m, coord_arrays=None, p=None):
    # Compute sum of:
    # coord_arrays^(p) * (image_l - image_m) / (sigma_l**2 + sigma_m**2)
    #
    # If coord_arrays is None, replace it with 1 (this allows code optimization)
    # for the case of constant background (polynomials of zero degree).
    #
    # NOTE: this function does not check that sigma2 arrays have same shapes
    #       as the coord_arrays arrays (for efficiency purpose).

    cmask = np.logical_and(mask_l, mask_m)

    if coord_arrays is None:
        if p is not None:
            raise ValueError("When pixel indices are None then exponent list "
                             "must be None as well.")

        return np.sum((image_l[cmask] - image_m[cmask]) /
                      (sigma2_l[cmask] + sigma2_m[cmask]),
                      dtype=np.float)

    if len(coord_arrays) != len(p):
        raise ValueError("Lengths of the list of pixel index arrays and "
                         "list of the exponents 'p' must be equal.")

    if len(coord_arrays) == 0:
        raise ValueError("There has to be at least one pixel index.")

    i = coord_arrays[0]**p[0]

    for c, ip in zip(coord_arrays[1:], p[1:]):
        i *= c**ip

    return np.sum(i[cmask] * (image_l[cmask] - image_m[cmask]) /
                  (sigma2_l[cmask] + sigma2_m[cmask]),
                  dtype=np.float)


def _sigma_pixel_sum(mask_l, mask_m, sigma2_l, sigma2_m,
                     coord_arrays=None, p=None, pp=None):
    # Compute sum of coord_arrays^(p+pp) ()/ (sigma_l**2 + sigma_m**2)
    #
    # If coord_arrays is None, replace it with 1 (this allows code optimization)
    # for the case of constant background (polynomials of zero degree).
    #
    # NOTE: this function does not check that sigma2 arrays have same shapes
    #       as the coord_arrays arrays (for efficiency purpose).

    cmask = np.logical_and(mask_l, mask_m)

    if coord_arrays is None:
        if p is not None or pp is not None:
            raise ValueError("When pixel indices are None then exponent lists "
                             "must be None as well.")

        return np.sum(1.0 / (sigma2_l[cmask] + sigma2_m[cmask]),
                      dtype=np.float)

    if len(coord_arrays) != len(p) or len(p) != len(pp):
        raise ValueError("Lengths of the list of pixel index arrays and "
                         "lists of the exponents 'p' and 'pp' must be "
                         "equal.")

    if len(coord_arrays) == 0:
        raise ValueError("There has to be at least one pixel index.")

    i = coord_arrays[0]**(p[0] + pp[0])

    for c, ip, ipp in zip(coord_arrays[1:], p[1:], pp[1:]):
        i *= c**(ip + ipp)

    return np.sum(i[cmask] / (sigma2_l[cmask] + sigma2_m[cmask]),
                  dtype=np.float)
