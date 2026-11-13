"""
Smart Restaurant Management and Ordering System
Administrative Password Reset Utility for Super Admin Accounts.

Usage:
    python reset_admin_password.py
"""

import sys
import getpass
from app import create_app, db
from app.models.user import User

MIN_PASSWORD_LENGTH = 8


def validate_password(password, confirm_password):
    """
    Validate password strength and confirmation.
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not password:
        return False, "Password cannot be empty."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    if password != confirm_password:
        return False, "Passwords do not match."
    return True, None


def reset_super_admin_password(app, db_instance, email, new_password, confirm_password):
    """
    Verifies that the target user exists, is active, and possesses the 'super_admin' role,
    validates the new password, and safely updates the password hash.

    Args:
        app: Flask application instance.
        db_instance: SQLAlchemy database instance.
        email: Email address of the super admin.
        new_password: New plaintext password.
        confirm_password: Password confirmation.

    Returns:
        tuple: (success: bool, message: str)
    """
    if not email or not isinstance(email, str):
        return False, "A valid email address is required."

    is_valid, err = validate_password(new_password, confirm_password)
    if not is_valid:
        return False, err

    with app.app_context():
        user = User.query.filter_by(email=email.strip()).first()
        if not user:
            return False, f"User with email '{email}' does not exist."
        if not user.is_active:
            return False, f"User account '{email}' is inactive/disabled."
        if user.role != 'super_admin':
            return False, f"User '{email}' does not have the 'super_admin' role (actual role: '{user.role}'). Access denied."

        try:
            user.set_password(new_password)
            db_instance.session.commit()
            return True, f"Password for Super Admin '{email}' was successfully updated."
        except Exception as e:
            db_instance.session.rollback()
            return False, f"Database error while updating password: {e}"


def main():
    print("=" * 64)
    print(" Smart Restaurant Management - Super Admin Password Reset")
    print("=" * 64)
    
    # Check for CLI flags or interactive choice
    visible = '--visible' in sys.argv or '--show' in sys.argv

    try:
        email = input("Enter Super Admin email [default: admin@test.com]: ").strip()
        if not email:
            email = "admin@test.com"

        if not visible:
            show_choice = input("Show password while typing on screen? [Y/n]: ").strip().lower()
            visible = (show_choice != 'n')

        if visible:
            print("[INFO] Visible typing enabled. Characters will be visible as you type.")
            new_password = input("Enter new password (min 8 characters): ")
            confirm_password = input("Confirm new password: ")
        else:
            new_password = getpass.getpass("Enter new password (min 8 characters): ")
            confirm_password = getpass.getpass("Confirm new password: ")
    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Operation cancelled by user.")
        sys.exit(1)

    app = create_app('development')
    success, message = reset_super_admin_password(app, db, email, new_password, confirm_password)

    if success:
        print(f"\n[SUCCESS] {message}")
        print("You can now log in at: http://127.0.0.1:5000/auth/login")
        sys.exit(0)
    else:
        print(f"\n[FAILED] {message}")
        sys.exit(1)


if __name__ == '__main__':
    main()
