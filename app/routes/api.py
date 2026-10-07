"""
API Blueprint - JSON API endpoints for AJAX calls.

Handles:
- Table availability checks
- Reservation creation
- Cart operations (add, update, remove)
- Order placement
- Order status queries

All responses are JSON format.

Implementation will be added in Phases 4-5.
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__)


@api_bp.route('/status')
def api_status():
    """API status check."""
    return {
        'status': 'ok',
        'api_version': '1.0',
        'message': 'Smart Restaurant API is running'
    }
