#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   OpenBACH is a generic testbed able to control/configure multiple
   network/physical entities (under test) and collect data from them. It is
   composed of an Auditorium (HMIs), a Controller, a Collector and multiple
   Agents (one for each network entity that wants to be tested).


   Copyright © 2016 CNES


   This file is part of the OpenBACH testbed.


   OpenBACH is a free software : you can redistribute it and/or modify it under the
   terms of the GNU General Public License as published by the Free Software
   Foundation, either version 3 of the License, or (at your option) any later
   version.

   This program is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
   FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
   details.

   You should have received a copy of the GNU General Public License along with
   this program. If not, see http://www.gnu.org/licenses/.



   @file     result_filter.py
   @brief    
   @author   Adrien THIBAUD <adrien.thibaud@toulouse.viveris.com>
"""


class Operand:
    """ Generic Operand """
    def __init__(self):
        pass


class OperandStatistic(Operand):
    """ Operand that refers to a Statistic in InfluxDB """
    def __init__(self, name):
        Operand.__init__(self)
        self.name = name

    def __str__(self):
        """ Function that formate the Operand to create the request """
        return '"{}"'.format(self.name)


class OperandValue(Operand):
    """ Operand that refers to a value """
    def __init__(self, value):
        Operand.__init__(self)
        self.value = value

    def __str__(self):
        """ Function that formate the Operand to create the request """
        if isinstance(self.value, str):
            return '\'{}\''.format(self.value)
        else:
            return str(self.value)


class OperandTimestamp(OperandValue):
    """ Operand that refers to a timestamp """
    def __init__(self, timestamp, unit='ms'):
        OperandValue.__init__(self, timestamp)
        self.unit = unit

    def __str__(self):
        """ Function that formate the Operand to create the request """
        return '{}{}'.format(self.value, self.unit)


class Condition:
    """ Generic Condition """
    def __init__(self):
        pass


class ConditionAnd(Condition):
    """ Condition 'AND' """
    def __init__(self, condition1, condition2):
        Condition.__init__(self)
        self.condition1 = condition1
        self.condition2 = condition2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '({})+and+({})'.format(self.condition1, self.condition2)


class ConditionOr(Condition):
    """ Condition 'OR' """
    def __init__(self, condition1, condition2):
        Condition.__init__(self)
        self.condition1 = condition1
        self.condition2 = condition2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '({})+or+({})'.format(self.condition1, self.condition2)


class ConditionEqual(Condition):
    """ Condition 'EQUAL' """
    def __init__(self, operand1, operand2):
        Condition.__init__(self)
        self.operand1 = operand1
        self.operand2 = operand2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '{}+=+{}'.format(self.operand1, self.operand2)


class ConditionNotEqual(Condition):
    """ Condition 'NOT EQUAL' """
    def __init__(self, operand1, operand2):
        Condition.__init__(self)
        self.operand1 = operand1
        self.operand2 = operand2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '{}+!=+{}'.format(self.operand1, self.operand2)


class ConditionUpperOrEqual(Condition):
    """ Condition 'UPPER OR EQUAL' """
    def __init__(self, operand1, operand2):
        Condition.__init__(self)
        self.operand1 = operand1
        self.operand2 = operand2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '{}+>=+{}'.format(self.operand1, self.operand2)


class ConditionUpper(Condition):
    """ Condition 'UPPER' """
    def __init__(self, operand1, operand2):
        Condition.__init__(self)
        self.operand1 = operand1
        self.operand2 = operand2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '{}+>+{}'.format(self.operand1, self.operand2)


class ConditionBelowOrEqual(Condition):
    """ Condition 'BELOW OR EQUAL' """
    def __init__(self, operand1, operand2):
        Condition.__init__(self)
        self.operand1 = operand1
        self.operand2 = operand2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '{}+<=+{}'.format(self.operand1, self.operand2)


class ConditionBelow(Condition):
    """ Condition 'BELOW' """
    def __init__(self, operand1, operand2):
        Condition.__init__(self)
        self.operand1 = operand1
        self.operand2 = operand2

    def __str__(self):
        """ Function that formate the Condition to create the request """
        return '{}+<+{}'.format(self.operand1, self.operand2)
