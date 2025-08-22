"""
Legacy compatibility layer for project details.

This module provides backward compatibility by re-exporting the new modular
ProjectDetailsView, while the actual implementation logic has been moved to
the controllers and widgets packages.

For new code, prefer using ProjectDetailsController directly:
    from src.gui.project_details.controllers.controller import ProjectDetailsController
    ctrl = ProjectDetailsController(session, project, modal=False)
    ctrl.open()
"""

# Re-export the view for backward compatibility
from .project_details.view import ProjectDetailsView

__all__ = ["ProjectDetailsView"]
