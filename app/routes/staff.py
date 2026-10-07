"""
Staff Blueprint - Restaurant Staff routes.

Handles (own restaurant only):
- Staff operational dashboard
- Table availability management
- Reservation viewing and updating
- Order viewing and status updates

Data Isolation: Every query filters by current_user.restaurant_id.
A staff member can NEVER access another restaurant's data.

Implementation will be added in Phases 4-6.
"""

from flask import Blueprint

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/dashboard')
def dashboard():
    """Staff dashboard. Implementation in Phase 6."""
    return {'message': 'Staff dashboard - coming in Phase 6'}
