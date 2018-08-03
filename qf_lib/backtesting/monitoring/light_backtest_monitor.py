# it is important to import the matplotlib first and then switch the interactive/dynamic mode on.
import matplotlib.pyplot as plt
plt.ion()  # required for dynamic chart

from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings
from datetime import datetime
from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult


class LightBacktestMonitor(BacktestMonitor):
    """
    This Monitor will be used to monitor backtest run from the script.
    It will display the portfolio value as the backtest progresses and generate a PDF at the end.
    It is not suitable for the Web application
    """

    def __init__(self, backtest_result: BacktestResult, settings: Settings,
                 pdf_exporter: PDFExporter, excel_exporter: ExcelExporter):
        super().__init__(backtest_result, settings, pdf_exporter, excel_exporter)

        self._nr_of_days = 10
        self._ctr = 0

    def end_of_day_update(self, timestamp: datetime=None):
        """
        Update line chart with current timeseries, buy only once in self._nr_of_days
        """
        self._ctr += 1
        if self._ctr % self._nr_of_days == 0:
            portfolio_tms = self.backtest_result.portfolio.get_portfolio_timeseries()
            self._ax.grid()

            # Set the data on x and y
            self._line.set_xdata(portfolio_tms.index)
            self._line.set_ydata(portfolio_tms.values)

            # Need both of these in order to rescale
            self._ax.relim()
            self._ax.autoscale_view()

            # We need to draw and flush
            self._figure.canvas.draw()
            self._figure.canvas.flush_events()

            self._ax.grid()  # we need two grid() calls in order to keep the grid on the chart

    def record_trade(self, transaction: Transaction):
        """ Do not record trades to save execution time, for more details use BacktestMonitor"""
        pass
