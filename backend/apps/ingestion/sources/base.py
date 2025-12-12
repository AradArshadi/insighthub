"""
Abstract base class for all data sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DataSource(ABC):
    """Abstract base class for all data sources."""
    
    @abstractmethod
    def search_businesses(self, location: str, query: str = "", 
                         category: str = "", radius: int = 5000, 
                         limit: int = 20) -> List[Dict]:
        """Search for businesses/places."""
        pass
    
    @abstractmethod
    def get_business_details(self, business_id: str) -> Optional[Dict]:
        """Get detailed business information."""
        pass
    
    @abstractmethod
    def get_reviews(self, business_id: str, limit: int = 20) -> List[Dict]:
        """Get reviews/tips for a business."""
        pass
    
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        return self.__class__.__name__.replace('Source', '').lower()