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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import decimal
import os
import pytest

import octobot_trading.constants as constants
import octobot_trading.errors as errors
from tests.test_utils.random_numbers import decimal_random_quantity, decimal_random_price, random_price

from tests.exchanges import backtesting_trader, backtesting_config, backtesting_exchange_manager, fake_backtesting
from tests import event_loop

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_get_current_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {'BTC': constants.ONE, 'USDT': constants.ZERO}
    portfolio_manager.portfolio.update_portfolio_from_balance({
        'BTC': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'ETH': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'XRP': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'DOT': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'MATIC': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()},
        'USDT': {'available': decimal_random_quantity(), 'total': decimal_random_quantity()}
    }, True)
    portfolio_manager.handle_balance_updated()

    assert portfolio_value_holder.get_current_crypto_currencies_values() == {
        'BTC': constants.ONE,
        'ETH': constants.ZERO,
        'XRP': constants.ZERO,
        'DOT': constants.ZERO,
        'MATIC': constants.ZERO,
        'USDT': constants.ZERO
    }

    exchange_manager.client_symbols.append("MATIC/BTC")
    exchange_manager.client_symbols.append("XRP/BTC")
    if not os.getenv('CYTHON_IGNORE'):
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XRP")
        portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal("0.005"))
        exchange_manager.client_symbols.append("DOT/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("DOT")
        portfolio_manager.handle_mark_price_update("DOT/BTC", decimal.Decimal("0.05"))
        exchange_manager.client_symbols.append("BTC/USDT")

        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': constants.ZERO,
            'USDT': constants.ZERO
        }
        matic_btc_price = decimal_random_price(max_value=decimal.Decimal(0.05))
        portfolio_value_holder.missing_currency_data_in_exchange.remove("MATIC")
        portfolio_manager.handle_mark_price_update("MATIC/BTC", matic_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': matic_btc_price,
            'USDT': constants.ZERO
        }
        usdt_btc_price = decimal_random_price(max_value=decimal.Decimal('0.01'))
        portfolio_value_holder.missing_currency_data_in_exchange.remove("USDT")
        portfolio_manager.handle_mark_price_update("BTC/USDT", usdt_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': constants.ZERO,
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': matic_btc_price,
            'USDT': constants.ONE / usdt_btc_price
        }
        eth_btc_price = decimal_random_price(max_value=constants.ONE)
        exchange_manager.client_symbols.append("ETH/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("ETH")
        portfolio_manager.handle_mark_price_update("ETH/BTC", eth_btc_price)
        assert portfolio_value_holder.get_current_crypto_currencies_values() == {
            'BTC': constants.ONE,
            'ETH': decimal.Decimal(str(eth_btc_price)),
            'XRP': decimal.Decimal("0.005"),
            'DOT': decimal.Decimal("0.05"),
            'MATIC': matic_btc_price,
            'USDT': constants.ONE / usdt_btc_price
        }


async def test_get_current_holdings_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    exchange_manager.client_symbols.append("ETH/BTC")
    portfolio_manager.portfolio.update_portfolio_from_balance({
        'BTC': {'available': decimal.Decimal("10"), 'total': decimal.Decimal("10")},
        'ETH': {'available': decimal.Decimal("100"), 'total': decimal.Decimal("100")},
        'XRP': {'available': decimal.Decimal("10000"), 'total': decimal.Decimal("10000")},
        'USDT': {'available': decimal.Decimal("1000"), 'total': decimal.Decimal("1000")}
    }, True)
    portfolio_manager.handle_balance_updated()
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': constants.ZERO,
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    portfolio_manager.handle_mark_price_update("ETH/BTC", 50)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    portfolio_manager.handle_mark_price_update("XRP/USDT", 2.5)
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal('0.00001'))
    assert portfolio_value_holder.get_current_holdings_values() == {
        'BTC': decimal.Decimal("10"),
        'ETH': decimal.Decimal("5000"),
        'XRP': constants.ZERO,
        'USDT': constants.ZERO
    }
    if not os.getenv('CYTHON_IGNORE'):
        exchange_manager.client_symbols.append("XRP/BTC")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("XRP")
        portfolio_manager.handle_mark_price_update("XRP/BTC", decimal.Decimal('0.00001'))
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': decimal.Decimal(10),
            'ETH': decimal.Decimal(5000),
            'XRP': decimal.Decimal(str(0.1)),
            'USDT': constants.ZERO
        }
        exchange_manager.client_symbols.append("BTC/USDT")
        portfolio_value_holder.missing_currency_data_in_exchange.remove("USDT")
        portfolio_manager.handle_mark_price_update("BTC/USDT", 5000)
        assert portfolio_value_holder.get_current_holdings_values() == {
            'BTC': decimal.Decimal(10),
            'ETH': decimal.Decimal(5000),
            'XRP': decimal.Decimal(str(0.1)),
            'USDT': decimal.Decimal(str(0.2))
        }


async def test_get_origin_portfolio_current_value(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == decimal.Decimal(str(10))


async def test_get_origin_portfolio_current_value_with_different_reference_market(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    portfolio_manager.reference_market = "USDT"
    portfolio_manager.handle_profitability_recalculation(True)
    assert portfolio_value_holder.get_origin_portfolio_current_value() == decimal.Decimal(str(1000))


async def test_update_origin_crypto_currencies_values(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    assert portfolio_value_holder.update_origin_crypto_currencies_values("ETH/BTC", decimal.Decimal(str(0.1))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["ETH"] == decimal.Decimal(str(0.1))
    assert portfolio_value_holder.last_prices_by_trading_pair["ETH/BTC"] == decimal.Decimal(str(0.1))
    # ETH is now priced and BTC is the reference market
    assert portfolio_value_holder.update_origin_crypto_currencies_values("ETH/BTC", decimal.Decimal(str(0.1))) is False

    assert portfolio_value_holder.update_origin_crypto_currencies_values("BTC/USDT", decimal.Decimal(str(100))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["USDT"] == \
           decimal.Decimal(constants.ONE / decimal.Decimal(100))
    assert portfolio_value_holder.last_prices_by_trading_pair["BTC/USDT"] == decimal.Decimal(str(100))
    # USDT is now priced and BTC is the reference market
    assert portfolio_value_holder.update_origin_crypto_currencies_values("BTC/USDT", decimal.Decimal(str(100))) is False

    # with bridge pair (DOT/ETH -> ETH/BTC to compute DOT/BTC)
    assert portfolio_value_holder.update_origin_crypto_currencies_values("DOT/ETH", decimal.Decimal(str(0.015))) is True
    assert portfolio_value_holder.origin_crypto_currencies_values["DOT"] == \
           decimal.Decimal(str(0.015)) * decimal.Decimal(str(0.1))
    assert portfolio_value_holder.last_prices_by_trading_pair["DOT/ETH"] == decimal.Decimal(str(0.015))
    # USDT is now priced and BTC is the reference market
    assert portfolio_value_holder.update_origin_crypto_currencies_values("DOT/ETH", decimal.Decimal(str(0.015))) is False


def test_try_convert_currency_value_using_multiple_pairs(backtesting_trader):
    config, exchange_manager, trader = backtesting_trader
    portfolio_manager = exchange_manager.exchange_personal_data.portfolio_manager
    portfolio_value_holder = portfolio_manager.portfolio_value_holder

    # try_convert_currency_value_using_multiple_pairs uses last_prices_by_trading_pair
    # try without last_prices_by_trading_pair
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("ETH", constants.ONE) is None
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("BTC", constants.ONE) is None
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("USDT", constants.ONE) is None
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("DOT", constants.ONE) is None
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("ADA", constants.ONE) is None

    # 1 ETH = 0.5 BTC
    portfolio_value_holder.last_prices_by_trading_pair["ETH/BTC"] = decimal.Decimal("0.5")
    # 1 DOT = 0.2 ETH
    portfolio_value_holder.last_prices_by_trading_pair["DOT/ETH"] = decimal.Decimal("0.2")
    # therefore 1 DOT = 0.2 ETH = 0.5 * 0.2 BTC = 0.1 BTC
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("DOT", decimal.Decimal("2")) \
        == decimal.Decimal("0.2")

    # with reversed pair in bridge
    portfolio_value_holder.last_prices_by_trading_pair["BTC/USDT"] = decimal.Decimal("10000")
    portfolio_value_holder.last_prices_by_trading_pair["ADA/USDT"] = decimal.Decimal("2")
    # 1 ADA = 2 USDT == 2/10000 BTC
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("ADA", decimal.Decimal(1)) \
        == decimal.Decimal(2) / decimal.Decimal(10000)
    # now using bridges cache
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("ADA", decimal.Decimal(2)) \
        == decimal.Decimal(4) / decimal.Decimal(10000)
    # bridge is saved
    if not os.getenv('CYTHON_IGNORE'):
        assert portfolio_value_holder._price_bridge_by_currency["ADA"] == [("ADA", "USDT"), ("USDT", "BTC")]
        assert portfolio_value_holder._convert_currency_value_from_saved_price_bridges("ADA", decimal.Decimal(10)) \
               == decimal.Decimal(20) / decimal.Decimal(10000)
    # without enough data
    portfolio_value_holder.last_prices_by_trading_pair["CRO/PLOP"] = decimal.Decimal("2")
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("CRO", constants.ONE) is None
    # second time to make sure bridge cache is not creating issues
    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("CRO", constants.ONE) is None
    if not os.getenv('CYTHON_IGNORE'):
        assert "CRO" not in portfolio_value_holder._price_bridge_by_currency
        with pytest.raises(errors.MissingPriceDataError):
            portfolio_value_holder._convert_currency_value_from_saved_price_bridges("CRO", constants.ONE)
        with pytest.raises(errors.MissingPriceDataError):
            portfolio_value_holder._convert_currency_value_from_saved_price_bridges("PLOP", constants.ONE)

    exchange_manager.exchange_config.traded_symbol_pairs.append("NANO/BTC")
    # 1 part of bridge data that has not been update but are in exchange config therefore will be available
    with pytest.raises(errors.PendingPriceDataError):
        portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("NANO", constants.ONE)

    assert portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("XRP", constants.ONE) is None
    # provide first part of the bridge
    exchange_manager.exchange_config.traded_symbol_pairs.append("XRP/USDT")
    with pytest.raises(errors.PendingPriceDataError):
        portfolio_value_holder.try_convert_currency_value_using_multiple_pairs("XRP", constants.ONE)

