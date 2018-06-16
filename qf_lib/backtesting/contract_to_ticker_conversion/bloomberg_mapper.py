from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker, BloombergTicker


class DummyBloombergContractTickerMapper(ContractTickerMapper):
    """
    Dummy BloombergTicker-Contract mapper.
    """
    def contract_to_ticker(self, contract: Contract) -> Ticker:
        return BloombergTicker(ticker=contract.symbol)

    def ticker_to_contract(self, ticker: Ticker) -> Contract:
        return Contract(symbol=ticker.ticker, security_type='STK', exchange='NYSE')