"""
Project Details module - Modern UI structure for project management.

This package provides a clean separation between UI components and business logic
for the project details dialog functionality.

Public API:
- ProjectDetailsView: Main dialog view (UI only)
- ProjectDetailsController: Business logic controller
"""

from .view import ProjectDetailsView
from .controllers.controller import ProjectDetailsController

__all__ = [
    "ProjectDetailsView",
    "ProjectDetailsController",
]
