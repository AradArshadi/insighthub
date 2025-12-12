"""
Enhanced mock data provider that mimics Foursquare API structure.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MockDataSource(DataSource):
    """
    Mock data source for development and testing.
    Generates realistic business data that mimics Foursquare structure.
    """
    
    # Enhanced business data
    BUSINESS_TEMPLATES = [
        {
            'name': 'Central Perk',
            'categories': ['Coffee Shop', 'Cafe'],
            'price': 2,  # $$ on Foursquare scale
            'typical_rating': 8.5,
            'popular_items': ['Latte', 'Cappuccino', 'Croissant']
        },
        {
            'name': 'Monk\'s Cafe',
            'categories': ['American Restaurant', 'Diner'],
            'price': 2,
            'typical_rating': 7.8,
            'popular_items': ['Burger', 'Fries', 'Milkshake']
        },
        {
            'name': 'Pizza Palace',
            'categories': ['Pizza Place', 'Italian Restaurant'],
            'price': 1,
            'typical_rating': 8.2,
            'popular_items': ['Margherita Pizza', 'Garlic Bread', 'Salad']
        },
        {
            'name': 'Sushi Zen',
            'categories': ['Japanese Restaurant', 'Sushi Restaurant'],
            'price': 3,
            'typical_rating': 9.1,
            'popular_items': ['Salmon Sushi', 'Miso Soup', 'Tempura']
        },
        {
            'name': 'Burger Joint',
            'categories': ['Burger Joint', 'Fast Food Restaurant'],
            'price': 1,
            'typical_rating': 7.5,
            'popular_items': ['Cheeseburger', 'Onion Rings', 'Soda']
        },
        {
            'name': 'Green Leaf',
            'categories': ['Vegetarian Restaurant', 'Healthy Restaurant'],
            'price': 2,
            'typical_rating': 8.7,
            'popular_items': ['Avocado Toast', 'Smoothie Bowl', 'Salad']
        },
        {
            'name': 'Steak House',
            'categories': ['Steakhouse', 'Fine Dining'],
            'price': 4,
            'typical_rating': 9.3,
            'popular_items': ['Ribeye Steak', 'Mashed Potatoes', 'Red Wine']
        },
        {
            'name': 'Taco Fiesta',
            'categories': ['Mexican Restaurant', 'Taco Place'],
            'price': 1,
            'typical_rating': 8.0,
            'popular_items': ['Taco Platter', 'Guacamole', 'Margarita']
        }
    ]
    
    CITIES = {
        'New York': {'lat': 40.7128, 'lng': -74.0060},
        'Los Angeles': {'lat': 34.0522, 'lng': -118.2437},
        'Chicago': {'lat': 41.8781, 'lng': -87.6298},
        'Houston': {'lat': 29.7604, 'lng': -95.3698},
        'Miami': {'lat': 25.7617, 'lng': -80.1918},
        'London': {'lat': 51.5074, 'lng': -0.1278},
        'Tokyo': {'lat': 35.6762, 'lng': 139.6503},
        'Sydney': {'lat': -33.8688, 'lng': 151.2093}
    }
    
    ADDRESS_PARTS = {
        'streets': ['Main', 'Oak', 'Pine', 'Maple', 'Elm', 'Cedar', 'Washington', 'Broadway'],
        'suffixes': ['St', 'Ave', 'Blvd', 'Rd', 'Ln', 'Dr'],
        'cities': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami']
    }
    
    def __init__(self):
        logger.info("✅ Mock data source initialized")
        self.generated_businesses = {}  # Cache generated businesses by ID
    
    def search_businesses(self, location: str, query: str = "", 
                         category: str = "", radius: int = 5000, 
                         limit: int = 20) -> List[Dict]:
        """
        Generate mock businesses for a location.
        Mimics Foursquare API response structure.
        """
        logger.info(f"Generating mock data for: {location} (limit: {limit})")
        
        # Determine city from location
        city = self._extract_city(location)
        
        businesses = []
        for i in range(min(limit, 20)):  # Max 20 mock businesses
            business = self._generate_business(city, i)
            
            # Apply filters
            if query and query.lower() not in business['name'].lower():
                continue
            if category and category not in business['category_names']:
                continue
            
            businesses.append(business)
        
        logger.info(f"Generated {len(businesses)} mock businesses")
        return businesses
    
    def get_business_details(self, business_id: str) -> Optional[Dict]:
        """Get detailed mock business information."""
        if business_id in self.generated_businesses:
            base_business = self.generated_businesses[business_id]
        else:
            # Generate a new one
            city = random.choice(list(self.CITIES.keys()))
            base_business = self._generate_business(city, int(business_id.split('_')[-1]))
        
        # Enhance with detailed information
        details = base_business.copy()
        details.update({
            'website': f"https://www.{details['name'].lower().replace(' ', '').replace("'", '')}.com",
            'phone': f"({random.randint(200, 999)})-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'email': f"contact@{details['name'].lower().replace(' ', '').replace("'", '')}.com",
            'description': self._generate_description(details['name'], details['category_names']),
            'social_media': {
                'facebook': f"https://facebook.com/{details['name'].lower().replace(' ', '')}",
                'instagram': f"https://instagram.com/{details['name'].lower().replace(' ', '')}",
                'twitter': f"https://twitter.com/{details['name'].lower().replace(' ', '')}"
            },
            'photos': self._generate_photos(details['name'], limit=5),
            'tips_count': random.randint(10, 500),
            'users_count': random.randint(100, 5000),
            'checkins_count': random.randint(1000, 20000),
            'here_now': random.randint(0, 50),
            'menu': self._generate_menu(details['category_names']),
            'attributes': self._generate_attributes(),
            'verified': random.choice([True, False]),
            'hours': self._generate_detailed_hours(),
            'popularity': random.uniform(0.5, 1.0),
            'tastes': self._generate_tastes(details['category_names'])
        })
        
        return details
    
    def get_reviews(self, business_id: str, limit: int = 20) -> List[Dict]:
        """Generate mock reviews/tips."""
        reviews = []
        for i in range(min(limit, 20)):
            days_ago = random.randint(0, 365)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            reviews.append({
                'id': f"tip_{business_id}_{i}",
                'text': self._generate_review_text(),
                'rating': None,  # Foursquare tips don't have ratings
                'user': random.choice(['Alex Johnson', 'Sam Smith', 'Taylor Swift', 
                                      'Jamie Wilson', 'Casey Brown', 'Jordan Lee']),
                'user_photo': f"https://i.pravatar.cc/100?img={random.randint(1, 70)}",
                'likes_count': random.randint(0, 50),
                'created_at': created_at.isoformat(),
                'source': 'mock'
            })
        
        return reviews
    
    def _generate_business(self, city: str, index: int) -> Dict:
        """Generate a single mock business with Foursquare-like structure."""
        template = random.choice(self.BUSINESS_TEMPLATES)
        business_id = f"mock_{city.lower().replace(' ', '')}_{index}"
        
        # Generate location with some variation
        city_coords = self.CITIES.get(city, self.CITIES['New York'])
        lat = city_coords['lat'] + random.uniform(-0.05, 0.05)
        lng = city_coords['lng'] + random.uniform(-0.05, 0.05)
        
        categories = []
        for cat_name in template['categories']:
            categories.append({
                'id': f"cat_{cat_name.lower().replace(' ', '_')}",
                'name': cat_name,
                'short_name': cat_name[:10],
                'icon': f"https://ss3.4sqi.net/img/categories_v2/food/{random.choice(['coffee', 'american', 'pizza', 'sushi', 'burger', 'vegetarian', 'steak', 'mexican'])}_"
            })
        
        business = {
            'id': business_id,
            'name': template['name'],
            'address': f"{random.randint(100, 999)} {random.choice(self.ADDRESS_PARTS['streets'])} {random.choice(self.ADDRESS_PARTS['suffixes'])}",
            'city': city,
            'state': self._get_state(city),
            'country': 'US' if city in ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami'] else 'Other',
            'postal_code': str(random.randint(10000, 99999)),
            'latitude': lat,
            'longitude': lng,
            'categories': categories,
            'category_names': template['categories'],
            'distance': random.randint(100, 5000),  # meters
            'rating': round(template['typical_rating'] + random.uniform(-0.3, 0.3), 1),
            'price': template['price'],
            'stats': {
                'tip_count': random.randint(10, 500),
                'users_count': random.randint(100, 5000),
                'checkins_count': random.randint(1000, 20000)
            },
            'hours': self._generate_hours(),
            'popularity': round(random.uniform(0.5, 1.0), 2),
            'tastes': self._generate_tastes(template['categories']),
            'source': 'mock',
            'raw_data': {'generated': True, 'template': template['name']}
        }
        
        # Cache for later retrieval
        self.generated_businesses[business_id] = business
        
        return business
    
    def _extract_city(self, location: str) -> str:
        """Extract city name from location string."""
        location_lower = location.lower()
        for city in self.CITIES.keys():
            if city.lower() in location_lower:
                return city
        return random.choice(list(self.CITIES.keys()))
    
    def _get_state(self, city: str) -> str:
        """Get state abbreviation for city."""
        states = {
            'New York': 'NY',
            'Los Angeles': 'CA',
            'Chicago': 'IL',
            'Houston': 'TX',
            'Miami': 'FL',
            'London': 'LDN',
            'Tokyo': 'TK',
            'Sydney': 'NSW'
        }
        return states.get(city, 'NA')
    
    def _generate_hours(self) -> Dict:
        """Generate business hours."""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = {}
        for day in days:
            open_hour = random.randint(6, 11)
            close_hour = random.randint(17, 23)
            hours[day] = {
                'open': f"{open_hour:02d}:00",
                'close': f"{close_hour:02d}:00",
                'renderedTime': f"{open_hour}:00 AM - {close_hour}:00 PM"
            }
        return {
            'regular': hours,
            'isOpen': random.choice([True, False])
        }
    
    def _generate_detailed_hours(self) -> Dict:
        """Generate detailed hours with timeframes."""
        hours = self._generate_hours()
        hours['timeframes'] = []
        
        # Add some timeframes
        timeframe_types = ['Breakfast', 'Lunch', 'Dinner', 'Late Night']
        for timeframe in random.sample(timeframe_types, random.randint(1, 3)):
            hours['timeframes'].append({
                'days': random.choice(['Mon-Fri', 'Mon-Sun', 'Sat-Sun']),
                'open': [{'renderedTime': f"{random.randint(6, 22)}:00"}],
                'segments': []
            })
        
        return hours
    
    def _generate_tastes(self, categories: List[str]) -> List[Dict]:
        """Generate taste profiles."""
        tastes = []
        food_tastes = ['Sweet', 'Savory', 'Spicy', 'Umami', 'Bitter', 'Sour']
        vibe_tastes = ['Cozy', 'Trendy', 'Loud', 'Quiet', 'Romantic', 'Family-friendly']
        
        for taste in random.sample(food_tastes, random.randint(1, 3)):
            tastes.append({
                'name': taste,
                'value': round(random.uniform(0.5, 1.0), 2)
            })
        
        for taste in random.sample(vibe_tastes, random.randint(1, 2)):
            tastes.append({
                'name': taste,
                'value': round(random.uniform(0.5, 1.0), 2)
            })
        
        return tastes
    
    def _generate_description(self, name: str, categories: List[str]) -> str:
        """Generate business description."""
        descriptors = {
            'Coffee Shop': ['artisanal coffee', 'cozy atmosphere', 'fresh pastries'],
            'Restaurant': ['farm-to-table ingredients', 'exquisite cuisine', 'excellent service'],
            'Pizza Place': ['wood-fired pizza', 'authentic recipes', 'family-owned'],
            'Sushi Restaurant': ['fresh fish', 'traditional techniques', 'omakase experience'],
            'Burger Joint': ['grass-fed beef', 'hand-cut fries', 'craft beers']
        }
        
        desc_parts = []
        for category in categories:
            if category in descriptors:
                desc_parts.extend(descriptors[category])
        
        if not desc_parts:
            desc_parts = ['delicious food', 'friendly staff', 'great atmosphere']
        
        return f"{name} offers {random.choice(desc_parts)} with {random.choice(desc_parts)}. {random.choice(['Perfect for any occasion!', 'A local favorite!', 'Highly recommended!'])}"
    
    def _generate_photos(self, business_name: str, limit: int = 5) -> List[Dict]:
        """Generate mock photo URLs."""
        photos = []
        for i in range(limit):
            photos.append({
                'id': f"photo_{uuid.uuid4().hex[:8]}",
                'prefix': 'https://images.unsplash.com/photo-',
                'suffix': f'?w=400&h=300&fit=crop&crop=entropy&q=80',
                'width': 400,
                'height': 300,
                'visibility': 'public'
            })
        return photos
    
    def _generate_menu(self, categories: List[str]) -> Dict:
        """Generate mock menu."""
        menu_types = {
            'Coffee Shop': ['Coffee', 'Tea', 'Pastries', 'Sandwiches'],
            'Restaurant': ['Appetizers', 'Main Courses', 'Desserts', 'Drinks'],
            'Pizza Place': ['Pizzas', 'Calzones', 'Salads', 'Drinks'],
            'Sushi Restaurant': ['Sushi Rolls', 'Sashimi', 'Appetizers', 'Sake'],
            'Burger Joint': ['Burgers', 'Fries', 'Shakes', 'Sides']
        }
        
        menu_sections = []
        for category in categories:
            if category in menu_types:
                for section in menu_types[category]:
                    menu_sections.append({
                        'name': section,
                        'description': f"Our selection of {section.lower()}",
                        'items': [{'name': f"Item {j}", 'price': random.randint(5, 20)} for j in range(3, 8)]
                    })
        
        if not menu_sections:
            menu_sections = [{
                'name': 'Main Menu',
                'items': [{'name': 'Special Dish', 'price': random.randint(10, 30)} for _ in range(5)]
            }]
        
        return {
            'type': 'Menu',
            'label': 'Menu',
            'anchor': 'View Menu',
            'url': 'https://example.com/menu',
            'mobileUrl': 'https://example.com/menu/mobile',
            'externalUrl': 'https://example.com/menu',
            'sections': menu_sections[:3]  # Limit to 3 sections
        }
    
    def _generate_attributes(self) -> Dict:
        """Generate business attributes."""
        return {
            'payment': {
                'creditCards': random.choice(['Visa, Mastercard', 'All major cards']),
                'applePay': random.choice([True, False]),
                'googlePay': random.choice([True, False])
            },
            'services': {
                'delivery': random.choice([True, False]),
                'takeout': random.choice([True, False]),
                'reservations': random.choice([True, False])
            },
            'accessibility': {
                'wheelchair': random.choice([True, False]),
                'parking': random.choice(['Street', 'Lot', 'Valet'])
            }
        }
    
    def _generate_review_text(self) -> str:
        """Generate realistic review text."""
        positives = [
            "Absolutely loved this place! The atmosphere was perfect and the food was exceptional.",
            "Great spot with friendly staff. Will definitely be coming back soon!",
            "One of the best dining experiences I've had. Highly recommend!",
            "Fresh ingredients and creative dishes. Worth every penny.",
            "Cozy ambiance and delicious food. Perfect for a date night."
        ]
        
        negatives = [
            "Food was okay but service was very slow. Might try again.",
            "Overpriced for what you get. Expected better quality.",
            "Nice atmosphere but the food was underwhelming.",
            "Wait time was excessive and food arrived cold.",
            "Average experience, nothing special compared to other places."
        ]
        
        neutrals = [
            "Decent place for a quick meal. Nothing extraordinary.",
            "Good food, standard service. Would return if in the area.",
            "Met expectations but didn't exceed them.",
            "Solid choice for the price point.",
            "Clean place with acceptable food. Does the job."
        ]
        
        # Weighted selection (60% positive, 20% negative, 20% neutral)
        pool = random.choices([positives, negatives, neutrals], weights=[0.6, 0.2, 0.2])[0]
        return random.choice(pool)
    
    def get_categories(self) -> List[Dict]:
        """Get mock Foursquare categories."""
        categories = []
        for i, template in enumerate(self.BUSINESS_TEMPLATES):
            for cat_name in template['categories']:
                if not any(c['name'] == cat_name for c in categories):
                    categories.append({
                        'id': f"mock_cat_{i}_{cat_name.lower().replace(' ', '_')}",
                        'name': cat_name,
                        'short_name': cat_name[:10],
                        'icon': f"https://ss3.4sqi.net/img/categories_v2/food/default_",
                        'categories': []
                    })
        return categories