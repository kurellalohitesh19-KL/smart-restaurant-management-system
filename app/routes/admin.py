"""
Admin Blueprint - Super Admin routes.

Handles (platform-wide):
- Super Admin dashboard
- Restaurant management (all restaurants)
- Owner management
- Staff management (all staff)
- Customer management
- Menu oversight (all restaurants)
- Table oversight (all restaurants)
- Reservation monitoring (all restaurants)
- Order monitoring (all restaurants)

Access: Only users with role='super_admin' can access these routes.
No restaurant_id scoping — full platform access.

Implementation will be added in Phase 6.
"""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
def dashboard():
    """Super Admin dashboard. Implementation in Phase 6."""
    return {'message': 'Super Admin dashboard - coming in Phase 6'}
