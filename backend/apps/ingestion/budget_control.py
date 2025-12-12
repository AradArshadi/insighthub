"""
Budget control system to prevent API cost overruns.
"""

import os
import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BudgetTracker:
    """Track API usage and costs in real-time."""
    
    def __init__(self):
        self.budget_file = 'data/api_budget.json'
        self._load_budget()
        
        # Default limits (safe for portfolio project)
        self.daily_limits = {
            'google_places': 100,  # $0.50/day max
            'yelp': 500,           # Free tier limit
            'foursquare': 100,     # Well below free tier
        }
        
        self.cost_per_request = {
            'google_places_details': 0.005,      # $0.005 per call
            'google_places_search': 0.017,       # $0.017 per call
            'google_places_photos': 0.007,       # $0.007 per call
            'yelp_business': 0.0,                # Free (within limits)
            'yelp_search': 0.0,                  # Free (within limits)
            'foursquare_venues': 0.0,            # Free (within limits)
        }
    
    def _load_budget(self):
        """Load or initialize budget tracking."""
        if os.path.exists(self.budget_file):
            with open(self.budget_file, 'r') as f:
                self.budget_data = json.load(f)
        else:
            self.budget_data = {
                'total_cost': 0.0,
                'daily_usage': {},
                'monthly_usage': {},
                'alerts_sent': []
            }
            self._save_budget()
    
    def _save_budget(self):
        """Save budget tracking data."""
        os.makedirs(os.path.dirname(self.budget_file), exist_ok=True)
        with open(self.budget_file, 'w') as f:
            json.dump(self.budget_data, f, indent=2)
    
    def can_make_request(self, api_name, endpoint):
        """Check if we can make an API request within budget."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Initialize today's usage
        if today not in self.budget_data['daily_usage']:
            self.budget_data['daily_usage'][today] = {}
        
        if api_name not in self.budget_data['daily_usage'][today]:
            self.budget_data['daily_usage'][today][api_name] = 0
        
        # Check daily limit
        daily_count = self.budget_data['daily_usage'][today][api_name]
        daily_limit = self.daily_limits.get(api_name, 50)
        
        if daily_count >= daily_limit:
            logger.warning(f"Daily limit reached for {api_name}: {daily_count}/{daily_limit}")
            return False
        
        # Check estimated cost
        cost_key = f"{api_name}_{endpoint}"
        estimated_cost = self.cost_per_request.get(cost_key, 0.01)
        
        if self.budget_data['total_cost'] + estimated_cost > 5.0:  # $5 max budget
            logger.error(f"Budget limit would be exceeded: ${self.budget_data['total_cost']:.2f} + ${estimated_cost:.2f}")
            return False
        
        return True
    
    def record_request(self, api_name, endpoint):
        """Record an API request and its cost."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Initialize if needed
        if today not in self.budget_data['daily_usage']:
            self.budget_data['daily_usage'][today] = {}
        if api_name not in self.budget_data['daily_usage'][today]:
            self.budget_data['daily_usage'][today][api_name] = 0
        
        # Update counts
        self.budget_data['daily_usage'][today][api_name] += 1
        
        # Update cost
        cost_key = f"{api_name}_{endpoint}"
        cost = self.cost_per_request.get(cost_key, 0.01)
        self.budget_data['total_cost'] += cost
        
        # Save and check alerts
        self._save_budget()
        self._check_alerts()
        
        return cost
    
    def _check_alerts(self):
        """Check if we need to send budget alerts."""
        alerts = []
        
        # Daily usage alerts
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.budget_data['daily_usage']:
            for api_name, count in self.budget_data['daily_usage'][today].items():
                limit = self.daily_limits.get(api_name, 50)
                if count >= limit * 0.8:  # 80% of limit
                    alerts.append(f"{api_name}: {count}/{limit} daily requests")
        
        # Cost alerts
        if self.budget_data['total_cost'] >= 1.0:  # $1 spent
            alerts.append(f"Total cost: ${self.budget_data['total_cost']:.2f}")
        
        # Send alerts (log for now, could email/SMS in production)
        for alert in alerts:
            if alert not in self.budget_data['alerts_sent']:
                logger.warning(f"BUDGET ALERT: {alert}")
                self.budget_data['alerts_sent'].append(alert)
        
        self._save_budget()
    
    def get_usage_summary(self):
        """Get current usage summary."""
        today = datetime.now().strftime('%Y-%m-%d')
        today_usage = self.budget_data['daily_usage'].get(today, {})
        
        return {
            'total_cost': self.budget_data['total_cost'],
            'today_usage': today_usage,
            'daily_limits': self.daily_limits
        }


class RateLimiter:
    """Rate limiting to prevent API throttling."""
    
    def __init__(self, requests_per_minute=10):
        self.requests_per_minute = requests_per_minute
        self.request_times = []
    
    def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        from time import sleep, time
        
        now = time()
        
        # Remove old requests (older than 1 minute)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = min(self.request_times)
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                sleep(wait_time)
        
        # Record this request
        self.request_times.append(now)