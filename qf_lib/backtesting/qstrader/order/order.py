from qf_lib.backtesting.qstrader.contract.contract import Contract
from qf_lib.backtesting.qstrader.order.execution_style import ExecutionStyle


class Order(object):
    """"
    Order generated by a strategy, then processed by PositionSizer and RiskManager.
    Finally executed by ExecutionHandler.
    """

    def __init__(self, contract: Contract, quantity: int, execution_style: ExecutionStyle,
                 tif: str='DAY', order_state: str=''):
        """
        This __init__ shouldn't be used anywhere beyond this module. User OrderFactory for creating Order objects.
        """
        self.id = None  # type:int
        self.contract = contract
        self.quantity = quantity
        self.tif = tif
        self.execution_style = execution_style
        self.order_state = order_state

    def __str__(self):
        return 'Order:\n' \
               '\tid: {}\n' \
               '\tcontract: {}\n' \
               '\tquantity: {}\n' \
               '\ttif: {}\n' \
               '\texecution_style: {}\n' \
               '\torder_state: {}\n'.format(
                    self.id, str(self.contract), self.quantity, self.tif, self.execution_style, self.order_state)

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Order):
            return False

        if other.id == self.id:
            return True

        return (self.contract, self.quantity, self.tif, self.execution_style, self.order_state) == \
               (other.contract, other.quantity, other.tif, other.execution_style, other.order_state)

    def __hash__(self):
        return hash((self.contract, self.quantity, self.tif, self.execution_style, self.order_state))
