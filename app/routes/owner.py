"""
Owner Blueprint - Restaurant Owner routes.

Handles (own restaurant only):
- Owner dashboard
- Restaurant profile management
- Staff management (create, edit, deactivate)
- Customer view (who interacted with restaurant)
- Table management
- Reservation management
- Menu management (categories, items)
- Order management
- Restaurant-level reports

Data Isolation: Every query filters by current_user.restaurant_id.
An owner can NEVER access another restaurant's data.

Implementation will be added in Phases 4-6.
"""

from flask import Blueprint

owner_bp = Blueprint('owner', __name__)


@owner_bp.route('/dashboard')
def dashboard():
    """Owner dashboard. Implementation in Phase 6."""
    return {'message': 'Owner dashboard - coming in Phase 6'}
