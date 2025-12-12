# backend/apps/ingestion/billing_protection.py
class BillingProtector:
    """Prevent accidental API cost overruns"""
    
    def __init__(self):
        self.daily_request_count = 0
        self.monthly_cost = 0
        self.max_daily_requests = int(os.getenv('MAX_REQUESTS_PER_DAY', 50))
        self.max_monthly_cost = float(os.getenv('MAX_MONTHLY_COST', 10.00))
    
    def can_make_request(self, api_name, estimated_cost=0.005):
        """Check if we can make another paid API request"""
        if os.getenv('USE_MOCK_DATA', 'True') == 'True':
            return False  # Force mock data
        
        if self.daily_request_count >= self.max_daily_requests:
            logger.warning(f"Daily limit reached for {api_name}")
            return False
        
        if self.monthly_cost + estimated_cost > self.max_monthly_cost:
            logger.error(f"Monthly cost limit would be exceeded: {api_name}")
            return False
        
        return True
    
    def record_request(self, api_name, cost=0.005):
        """Record API request for billing tracking"""
        self.daily_request_count += 1
        self.monthly_cost += cost
        
        # Alert if approaching limits
        if self.daily_request_count >= self.max_daily_requests * 0.8:
            logger.warning(f"Approaching daily request limit: {self.daily_request_count}/{self.max_daily_requests}")
        
        if self.monthly_cost >= self.max_monthly_cost * 0.8:
            logger.warning(f"Approaching monthly cost limit: ${self.monthly_cost:.2f}/${self.max_monthly_cost:.2f}")