from datetime import datetime
from typing import List, Dict

from numpy import sign

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.transaction import Transaction
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class Portfolio(object):
    def __init__(self, data_handler: DataHandler, initial_cash: float, timer: Timer,
                 contract_ticker_mapper: ContractTickerMapper):
        """
        On creation, the Portfolio object contains no positions and all values are "reset" to the initial
        cash, with no PnL.
        """
        self.initial_cash = initial_cash
        self.data_handler = data_handler
        self.timer = timer
        self.contract_ticker_mapper = contract_ticker_mapper

        """cash value includes futures P&L + stock value + securities options value + bond value + fund value."""
        self.net_liquidation = initial_cash

        """equals the sum of the absolute value of all positions except cash """
        self.gross_value_of_positions = 0

        # dates and portfolio values are keep separately because it is inefficient to append to the QFSeries
        # use get_portfolio_timeseries() to get them as a series.
        self.dates = []                 # type: List[datetime]
        self.portfolio_values = []      # type: List[float]
        self.current_cash = initial_cash

        self._leverage = []              # type: List[float]

        self.open_positions_dict = {}   # type: Dict[Contract, BacktestPosition]
        self.closed_positions = []      # type: List[BacktestPosition]
        self.transactions = []          # type: List[Transaction]
        self.trades = []                # type: List[Trade]

    def transact_transaction(self, transaction: Transaction):
        """
        Adjusts positions to account for a transaction.
        Handles any new position or modification to a current position
        """

        position = self._get_or_create_position(transaction.contract)
        transaction_cost = position.transact_transaction(transaction)
        self.current_cash -= transaction_cost

        self._record_trade_and_transaction(position, transaction)

        # if the position was closed: remove it from open positions and place in closed positions
        if position.is_closed:
            self.open_positions_dict.pop(transaction.contract)
            self.closed_positions.append(position)

    def update(self):
        """
        Updates the value of all positions that are currently open by getting the most recent price.
        """
        self.net_liquidation = self.current_cash
        self.gross_value_of_positions = 0

        contracts = self.open_positions_dict.keys()
        contract_to_ticker_dict = {
            contract: self.contract_ticker_mapper.contract_to_ticker(contract) for contract in contracts
        }

        all_tickers_in_portfolio = list(contract_to_ticker_dict.values())
        current_prices_series = self.data_handler.get_last_available_price(tickers=all_tickers_in_portfolio)

        for contract, position in self.open_positions_dict.items():
            ticker = contract_to_ticker_dict[contract]
            security_price = current_prices_series[ticker]
            position.update_price(bid_price=security_price, ask_price=security_price)  # TODO: Model with Bid/Ask
            self.net_liquidation += position.market_value
            self.gross_value_of_positions += abs(position.market_value)

        self.dates.append(self.timer.now())
        self.portfolio_values.append(self.net_liquidation)
        self._leverage.append(self.gross_value_of_positions / self.net_liquidation)

    def get_portfolio_timeseries(self) -> PricesSeries:
        """
        Returns a timeseries of value of the portfolio expressed in currency units
        """
        portfolio_timeseries = PricesSeries(data=self.portfolio_values, index=self.dates)
        return portfolio_timeseries

    def leverage(self) -> QFSeries:
        """
        Leverage = GrossPositionValue / NetLiquidation
        """
        return QFSeries(data=self._leverage, index=self.dates)

    def _get_or_create_position(self, contract: Contract) -> BacktestPosition:
        position = self.open_positions_dict.get(contract, None)
        if position is None:
            position = BacktestPosition(contract)
            self.open_positions_dict[contract] = position

        return position

    def _record_trade_and_transaction(self, position: BacktestPosition, transaction: Transaction):
        """
        Trade is defined as a transaction that goes in the direction of making your position smaller.
        For example:
           selling part or entire long position is a trade
           buying back part or entire short position is a trade
           buying additional shares of existing long position is NOT a trade
        """
        self.transactions.append(transaction)

        is_a_trade = sign(transaction.quantity) != sign(position.quantity())
        if is_a_trade:
            time = transaction.time
            contract = transaction.contract

            # only the part that goes in the opposite direction is considered as a trade
            quantity = min([abs(transaction.quantity), abs(position.quantity())])
            quantity *= sign(transaction.quantity)  # sign of the transaction should be preserved

            entry_price = position.avg_cost_per_share()
            exit_price = transaction.average_price_including_commission()
            trade = Trade(time=time,
                          contract=contract,
                          quantity=quantity,
                          entry_price=entry_price,
                          exit_price=exit_price)
            self.trades.append(trade)
