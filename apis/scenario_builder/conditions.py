#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OpenBACH is a generic testbed able to control/configure multiple
# network/physical entities (under test) and collect data from them.
# It is composed of an Auditorium (HMIs), a Controller, a Collector
# and multiple Agents (one for each network entity that wants to be
# tested).
#
#
# Copyright © 2016-2023 CNES
#
#
# This file is part of the OpenBACH testbed.
#
#
# OpenBACH is a free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

import enum
from collections import namedtuple


class Operator(enum.Enum):
    """Enumeration for the various supported operands
    in the `if` and `while` openbach functions.
    """

    Equal = '='
    DoubleEqual = '=='
    LowerOrEqual = '<='
    LowerThan = '<'
    GreaterOrEqual = '>='
    GreaterThan = '>'
    Different = '!='
    And = 'and'
    Or = 'or'
    Xor = 'xor'
    Not = 'not'

    def build(self, *args):
        """Helper function to simplify usage in `Condition`.

        Construct a string representing this operator (hint:
        uses its name).
        """

        return self.value


class Condition:
    """Representation of a condition to be used by some openbach functions"""

    def __init__(self, operator, left_operand=None, right_operand=None):
        switch = {
            Operator.Equal: self._init_two_operands,
            Operator.DoubleEqual: self._init_two_operands,
            Operator.LowerOrEqual: self._init_two_operands,
            Operator.LowerThan: self._init_two_operands,
            Operator.GreaterOrEqual: self._init_two_operands,
            Operator.GreaterThan: self._init_two_operands,
            Operator.Different: self._init_two_operands,
            Operator.And: self._init_two_conditions,
            Operator.Or: self._init_two_conditions,
            Operator.Xor: self._init_two_conditions,
            Operator.Not: self._init_one_condition,
        }

        self._operator = Operator(operator)
        self._inner = {'type': self._operator}
        switch[self._operator](left_operand, right_operand)

    def _init_one_condition(self, condition, *args):
        if not isinstance(condition, Condition):
            raise TypeError('operand for the {} operator must be of type '
                            'OpenBachCondition'.format(self._operator.name))

        self._inner['condition'] = condition

    def _init_two_conditions(self, left_condition, right_condition):
        conditions = (left_condition, right_condition)
        if not all(isinstance(c, Condition) for c in conditions):
            raise TypeError('operands for the {} operator must be of type '
                            'OpenBachCondition'.format(self._operator.name))

        self._inner['left_condition'] = left_condition
        self._inner['right_condition'] = right_condition

    def _init_two_operands(self, left_operand, right_operand):
        operands = (left_operand, right_operand)
        if not all(isinstance(o, Operand) for o in operands):
            raise TypeError('operands for the {} operator must be of type Open'
                            'BachConditionOperand'.format(self._operator.name))

        self._inner['left_operand'] = left_operand
        self._inner['right_operand'] = right_operand

    def build(self, functions):
        """Construct a dictionary representing this condition.

        This dictionary is suitable to be included as a condition
        for an openbach functions accepting them.
        """
        return {key: value.build(functions) for key, value in self._inner.items()}


class OperandDescription(enum.Enum):
    """Enumeration describing the various fields
    expected by each kind of operand.
    """

    database = 'name key attribute'
    value = 'value'
    statistic = 'measurement field'


class Operand:
    """Representation of an operand to be used by some `Condition`s"""

    def __init__(self, kind, *args, **kwargs):
        try:
            self._type = OperandDescription[kind]
        except KeyError:
            raise ValueError('{} is not a valid operand type'
                             .format(kind)) from None

        values_factory = namedtuple('Operand', self._type.value)
        self._values = values_factory(*args, **kwargs)

    def build(self, functions):
        """Construct a dictionary representing this operand.

        This dictionary is suitable to be included as a left
        or right operand for conditions accepting them.
        """

        context = {'type': self._type.name}
        context.update(zip(self._values._fields, self._values))

        # TODO: uncomment when OpenBach accepts openbach function IDs
        # instead of strings for `measurement`

        # if self._type == OperandDescription.statistic:
        #     ids = context['measurement'],
        #     try:
        #         context['measurement'], = safe_indexor(functions, ids)
        #     except ValueError:
        #         raise ValueError('configured function in operand \'{}\' '
        #                          'does not reference a valid openbach_'
        #                          'function for this scenario'
        #                          .format(self._type.name)) from None
        return context
