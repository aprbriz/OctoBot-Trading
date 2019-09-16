# cython: language_level=3
#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_backtesting.backtesting cimport Backtesting
from octobot_trading.exchanges.abstract_exchange cimport AbstractExchange

cdef class ExchangeSimulator(AbstractExchange):
    cdef public bint initializing

    cdef public list symbols
    cdef public list time_frames
    cdef public list backtesting_data_files

    cdef public Backtesting backtesting

    # cdef public Backtesting backtesting

    cpdef bint symbol_exists(self, str symbol)
    cpdef bint time_frame_exists(self, object time_frame)
    cpdef str get_name(self)
    cpdef int get_progress(self)
    cpdef dict get_market_status(self, str symbol, float price_example=*, bint with_fixer=*)
    cpdef get_uniform_timestamp(self, float timestamp)
    cpdef dict get_fees(self, str symbol=*)
    cpdef dict get_trade_fee(self, str symbol, object order_type, float quantity, float price, str taker_or_maker=*)
