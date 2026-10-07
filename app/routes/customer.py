"""
Customer Blueprint - Customer-facing routes.

Handles:
- Home / landing page
- Restaurant discovery and listing
- Restaurant detail view
- Table availability and reservation
- Menu browsing
- Cart
- Order placement and tracking

Implementation will be added in Phases 3-5.
"""

from flask import Blueprint, render_template

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/')
def home():
    """Landing page with Trichy location. Implementation in Phase 3."""
    return render_template('base.html')
