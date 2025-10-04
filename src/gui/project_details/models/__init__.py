"""
Models Package

Data models for the project details interface.
Handles table model implementations and proxy models for filtering/sorting.
"""

from .cabinet_table_model import CabinetTableModel
from .cabinet_proxy_model import CabinetProxyModel

__all__ = [
    "CabinetTableModel",
    "CabinetProxyModel",
]
