# backend/apps/ingestion/mock_providers.py
import random
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

class MockBusinessData:
    """Generate realistic mock business data"""
    
    BUSINESS_NAMES = [
        "Joe's Pizza", "Mario's Italian Kitchen", "Taste of Tokyo",
        "Burger Palace", "Cafe Central", "Golden Dragon",
        "Mediterranean Grill", "Taco Fiesta", "Steak House Prime",
        "Vegetarian Delight", "Seafood Harbor", "BBQ Smokehouse"
    ]
    
    CATEGORIES = [
        "Italian", "Japanese", "American", "Chinese", 
        "Mexican", "Mediterranean", "Steakhouse", 
        "Vegetarian", "Seafood", "BBQ", "Cafe", "Bakery"
    ]
    
    CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    
    @classmethod
    def generate_business(cls, business_id=None):
        """Generate a single mock business"""
        name = random.choice(cls.BUSINESS_NAMES)
        category = random.choice(cls.CATEGORIES)
        city = random.choice(cls.CITIES)
        
        return {
            'id': business_id or f"mock_{random.randint(10000, 99999)}",
            'name': name,
            'address': f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St, {city}",
            'city': city,
            'category': category,
            'rating': round(random.uniform(3.0, 5.0), 1),
            'review_count': random.randint(10, 2000),
            'price_range': random.choice(['$', '$$', '$$$', '$$$$']),
            'phone': f"({random.randint(200, 999)})-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'website': f"https://www.{name.lower().replace(' ', '').replace("'", '')}.com",
            'hours': cls._generate_hours(),
            'coordinates': {
                'latitude': random.uniform(40.5, 41.0) if city == "New York" else random.uniform(33.5, 34.5),
                'longitude': random.uniform(-74.5, -73.5) if city == "New York" else random.uniform(-118.5, -117.5)
            },
            'source': 'mock',
            'last_updated': datetime.now().isoformat()
        }
    
    @classmethod
    def generate_reviews(cls, business_id, count=10):
        """Generate mock reviews for a business"""
        reviews = []
        for i in range(count):
            days_ago = random.randint(0, 365)
            review_date = datetime.now() - timedelta(days=days_ago)
            
            reviews.append({
                'id': f"review_{business_id}_{i}",
                'business_id': business_id,
                'rating': random.choice([1, 2, 3, 4, 5]),
                'text': cls._generate_review_text(),
                'user': f"User_{random.randint(1000, 9999)}",
                'date': review_date.isoformat(),
                'source': 'mock'
            })
        return reviews
    
    @staticmethod
    def _generate_hours():
        """Generate random business hours"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = {}
        for day in days:
            open_hour = random.randint(6, 11)
            close_hour = random.randint(17, 23)
            hours[day] = f"{open_hour}:00 AM - {close_hour}:00 PM"
        return hours
    
    @staticmethod
    def _generate_review_text():
        """Generate realistic review text"""
        positives = [
            "Great food and excellent service!",
            "Loved the atmosphere, will definitely return.",
            "Best in town, highly recommended!",
            "Fresh ingredients and friendly staff.",
            "Worth every penny, amazing experience."
        ]
        
        negatives = [
            "Food was cold and service was slow.",
            "Overpriced for what you get.",
            "Not as good as the reviews suggested.",
            "Wait time was too long.",
            "Average at best, won't return."
        ]
        
        neutrals = [
            "Decent place, nothing special.",
            "Good for a quick meal.",
            "Average experience overall.",
            "Food was okay, service was fine.",
            "Met expectations but didn't exceed them."
        ]
        
        # Weighted random selection
        choice = random.choices(
            [positives, negatives, neutrals],
            weights=[0.6, 0.2, 0.2]
        )[0]
        
        return random.choice(choice)