"""
Location Service - Handles city/location detection.

Phase 1: Hardcoded Tiruchirappalli (Trichy), Tamil Nadu.
Phase 2: Browser Geolocation API + Google Maps integration.

The architecture abstracts location detection so that swapping
from hardcoded to geolocation requires no refactoring of
dependent modules.
"""


class LocationService:
    """Service for location detection and restaurant filtering by city."""

    DEFAULT_CITY = "Tiruchirappalli"
    DEFAULT_STATE = "Tamil Nadu"
    DEFAULT_LAT = 10.7905
    DEFAULT_LNG = 78.7047

    @staticmethod
    def get_current_city():
        """
        Get the current city for the user.

        Phase 1: Returns hardcoded Trichy.
        Phase 2: Will use browser Geolocation API coordinates
                 sent from the frontend to determine the city.

        Returns:
            dict: City information with name, state, and coordinates.
        """
        return {
            "city": LocationService.DEFAULT_CITY,
            "state": LocationService.DEFAULT_STATE,
            "latitude": LocationService.DEFAULT_LAT,
            "longitude": LocationService.DEFAULT_LNG
        }

    @staticmethod
    def get_supported_cities():
        """
        Get list of cities supported by the platform.

        Phase 1: Only Trichy.
        Future: Chennai, Madurai, Coimbatore, etc.

        Returns:
            list: List of supported city dictionaries.
        """
        return [
            {
                "city": "Tiruchirappalli",
                "state": "Tamil Nadu",
                "latitude": 10.7905,
                "longitude": 78.7047,
                "is_active": True
            }
        ]
