#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them. It is
# composed of an Auditorium (HMIs), a Controller, a Collector and multiple
# Agents (one for each network entity that wants to be tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.

"""Sources of the compute_mos.py file"""

__author__ = 'Antoine AUGER'
__credits__ = 'Antoine AUGER <antoine.auger@tesa.prd.fr>'

from math import log, exp, sqrt
from codec import CodecConstants


def compute_r_value(c: CodecConstants, T, Ta, Ppl, jitter, use_jitter=True):
    """
    Method to compute the transmission rating factor R

    See ITU-T G.107 recommendation (06/2015)
    https://www.itu.int/rec/T-REC-G.107-201506-I

    :param c: the codec object with default and specific values
    :type c: CodecConstants
    :param T: the mean one-way delay of the echo path (ms)
    :type T: float
    :param Ta: the absolute delay (ms)
    :type Ta: float
    :param Ppl: the random packet-loss probability
    :type Ppl: float
    :param jitter: the average jitter measured
    :type jitter: float
    :param use_jitter: whether or not the MOS computation should take the jitter into account
    :type use_jitter: bool
    :return: the transmission rating factor R-value
    :rtype: float
    """
    T = float(T)
    Ta = float(Ta)
    Ppl = float(Ppl)

    if use_jitter:
        T += 2 * jitter
        Ta += 2 * jitter

    SLR = float(c.SLR)
    RLR = float(c.RLR)
    Pr = float(c.Pr)
    LSTR = float(c.LSTR)
    Ps = float(c.Ps)
    Ds = float(c.Ds)
    NC = float(c.NC)
    Nfo = float(c.Nfo)
    STMR = float(c.STMR)
    TELR = float(c.TELR)
    Ie = float(c.Ie)
    Bpl = float(c.Bpl)
    BurstR = float(c.BurstR)
    A = float(c.A)

    OLR = SLR + RLR
    Pre = Pr + 10 * log(1 + pow(10, (10 - LSTR) / 10), 10)
    Nos = Ps - SLR - Ds - 100 + 0.004 * pow(Ps - OLR - Ds - 14, 2)
    Nor = RLR - 121 + Pre + 0.008 * pow(Pre - 35, 2)
    No = 10 * log(pow(10, NC / 10) + pow(10, Nos / 10) + pow(10, Nor / 10) + pow(10, Nfo / 10), 10)

    Xolr = OLR + 0.2 * (64 + No - RLR)
    STMRo = -10 * log(pow(10, -STMR / 10) + exp(-T / 4) * pow(10, -TELR / 10), 10)
    Ist = 12 * (pow(1 + pow((STMRo - 13) / 6, 8), 1 / 8)) \
          - 28 * pow(1 + pow(((STMRo + 1) / 19.4), 35), 1 / 35) \
          - 13 * pow(1 + pow(((STMRo - 3) / 33), 13), 1 / 13) + 29

    Ro = compute_ro(c, No)
    Is = compute_is(c, Ro, Xolr, Ist)
    Id = compute_id(c, T, Ta, No, Ro, Ist)
    Ie_eff = compute_ie_eff(Ie, Ppl, Bpl, BurstR)

    return Ro - Is - Id - Ie_eff + A


def compute_ro(c, No):
    """
    Ro corresponds to the basic signal-to-noise ratio

    See ITU-T G.107 recommendation (06/2015)
    https://www.itu.int/rec/T-REC-G.107-201506-I

    :param c: the codec object with default and specific values
    :type c: CodecConstants
    :param No: the power addition of different noise sources
    :type No: float
    :return: the basic signal-to-noise ratio Ro
    :rtype: float
    """
    No = float(No)
    SLR = float(c.SLR)

    return 15 - 1.5 * (SLR + No)


def compute_is(c, Ro, Xolr, Ist):
    """
    Is corresponds to the sum of all impairments which may occur more or less simultaneously with the voice transmission

    See ITU-T G.107 recommendation (06/2015)
    https://www.itu.int/rec/T-REC-G.107-201506-I

    :param c: the codec object with default and specific values
    :type c: CodecConstants
    :param Ro: the basic signal-to-noise ratio
    :type Ro: float
    :param Xolr: Xolr
    :type Xolr: float
    :param Ist: the impairment caused by non-optimum sidetone
    :type Ist: float
    :return: the sum of all impairments Is
    :rtype: float
    """
    qdu = float(c.qdu)

    Iolr = 20 * (pow(1 + pow(Xolr / 8, 8), 1 / 8) - Xolr / 8)
    Q = 37 - 15 * log(qdu, 10)
    G = 1.07 + 0.258 * Q + 0.0602 * pow(Q, 2)
    Y = (Ro - 100) / 15 + 46 / 8.4 - G / 9
    Z = 46 / 30 - G / 40
    Iq = 15 * log(1 + pow(10, Y) + pow(10, Z), 10)
    return Iolr + Ist + Iq


def compute_id(c, T, Ta, No, Ro, Ist):
    """
    Id corresponds to an estimation for the impairments due to the talker echo

    See ITU-T G.107 recommendation (06/2015)
    https://www.itu.int/rec/T-REC-G.107-201506-I

    :param c: the codec object with default and specific values
    :type c: CodecConstants
    :param T: the mean one-way delay of the echo path (ms)
    :type T: float
    :param No: the power addition of different noise sources
    :type No: float
    :param Ro: the basic signal-to-noise ratio
    :type Ro: float
    :param Ist: the impairment caused by non-optimum sidetone
    :type Ist: float
    :return: an estimation for the impairments due to the talker echo Id
    :rtype: float
    """
    RLR = float(c.RLR)
    STMR = float(c.STMR)
    TELR = float(c.TELR)
    WEPL = float(c.WEPL)
    Tr = float(c.Tr)
    mT = float(c.mT)
    sT = float(c.sT)

    Roe = -1.5 * (No - RLR)
    Rle = 10.5 * (WEPL + 7) * pow(Tr + 1, -0.25)
    Idle = (Ro - Rle) / 2 + sqrt((pow(Ro - Rle, 2) / 4) + 169)
    TERV = TELR - 40 * log((1 + T / 10) / (1 + T / 150), 10) + 6 * exp(-0.3 * pow(T, 2))

    Re = 80 + 2.5 * (TERV - 14)
    if STMR < 9:
        Re = 80 + 2.5 * (TERV + Ist / 2 - 14)

    Idte = 0
    if T >= 1:
        Idte = ((Roe - Re) / 2 + sqrt(pow(Roe - Re, 2) / 4 + 100) - 1) * (1 - exp(-T))

    Idd = 0
    if Ta > mT:
        X = log(Ta / mT, 10) / log(2, 10)
        Idd = 25 * (pow(1 + pow(X, 6 * sT), 1 / (6 * sT)) - 3 * pow(1 + pow(X / 3, 6 * sT), 1 / (6 * sT)) + 2)

    Id = Idte + Idle + Idd
    if STMR > 20:
        Id = sqrt(pow(Idte, 2) + pow(Ist, 2)) + Idle + Idd

    return Id


def compute_ie_eff(Ie, Ppl, Bpl, BurstR):
    """
    Ie-eff corresponds to the effective equipment impairment factor

    See ITU-T G.107 recommendation (06/2015)
    https://www.itu.int/rec/T-REC-G.107-201506-I/fr

    :param Ie: the equipment impairment factor (depends on the codec used)
    :type Ie: float
    :param Ppl: the packet-loss probability
    :type Ppl: float
    :param Bpl: the packet-loss robustness factor
    :type Bpl: float
    :param BurstR: the so-called burst ratio
    :type BurstR: float
    :return: the effective equipment impairment factor Ie-eff
    :rtype: float
    """
    return Ie + (95 - Ie) * (Ppl / ((Ppl/BurstR) + Bpl))


def compute_mos_value(r_value):
    """
    Method to convert a R-factor value into a MOS value

    :param r_value: a float between 0 and 120 (R-factor)
    :type r_value: float
    :return: the Mean Opinion Score (MOS), i.e., a float between 0 and 5
    :rtype: float
    """
    MOS = 1
    if 0 < r_value < 100:
        MOS = 1 + 0.035 * r_value + r_value * (r_value - 60) * (100 - r_value) * 7 * 1e-6
    elif r_value >= 100:
        MOS = 4.5
    return MOS


def estimate_user_satisfaction(mos_value):
    """
    Method that returns a textual user satisfaction from a MOS value

    :param mos_value: a float between 0 and 5 (MOS)
    :type mos_value: float
    :return: a user satisfaction
    :rtype: str
    """
    if mos_value > 4.34:
        return "Very satisfied"
    elif mos_value > 4.03:
        return "Satisfied"
    elif mos_value > 3.60:
        return "Some users dissatisfied"
    elif mos_value > 3.10:
        return "Many users dissatisfied"
    elif mos_value > 2.58:
        return "Nearly all users dissatisfied"
    else:
        return "All users dissatisfied"
