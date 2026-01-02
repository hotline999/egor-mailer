import hashlib
import secrets
import json
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class LinkTracker:
    """Manages link tracking tokens and click tracking."""
    
    # In-memory storage (for production, use database)
    _tokens = {}
    _clicks = {}
    
    def __init__(self):
        """Initialize the tracker."""
        self.token_length = 32
        self.max_tokens = 10000
    
    def generate_token(self, target_url, email=None, campaign='default'):
        """
        Generate a unique tracking token.
        
        Args:
            target_url: URL to track clicks for
            email: Email address (optional)
            campaign: Campaign name (optional)
        
        Returns:
            Generated token string
        """
        try:
            # Generate random token
            token = secrets.token_urlsafe(self.token_length)
            
            # Store token metadata
            self._tokens[token] = {
                'target_url': target_url,
                'email': email,
                'campaign': campaign,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=90)).isoformat(),
                'click_count': 0
            }
            
            # Initialize click tracking
            self._clicks[token] = []
            
            logger.info(f'Generated token {token} for campaign {campaign}')
            return token
        
        except Exception as e:
            logger.error(f'Error generating token: {str(e)}')
            raise
    
    def track_click(self, token, ip_address, user_agent):
        """
        Record a click on a tracked link.
        
        Args:
            token: Tracking token
            ip_address: IP address of the clicker
            user_agent: User agent of the clicker
        
        Returns:
            Dictionary with tracking result
        """
        try:
            # Validate token
            if token not in self._tokens:
                logger.warning(f'Invalid token attempted: {token}')
                return {'success': False, 'error': 'Invalid token'}
            
            token_data = self._tokens[token]
            
            # Check expiration
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.utcnow() > expires_at:
                logger.warning(f'Expired token accessed: {token}')
                return {'success': False, 'error': 'Token expired'}
            
            # Record click
            click_data = {
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': datetime.utcnow().isoformat(),
                'click_hash': self._generate_click_hash(token, ip_address)
            }
            
            self._clicks[token].append(click_data)
            token_data['click_count'] += 1
            
            logger.info(f'Tracked click for token {token} from IP {ip_address}')
            
            return {
                'success': True,
                'target_url': token_data['target_url'],
                'timestamp': click_data['timestamp'],
                'click_count': token_data['click_count']
            }
        
        except Exception as e:
            logger.error(f'Error tracking click: {str(e)}')
            return {'success': False, 'error': str(e)}
    
    def get_token_info(self, token):
        """
        Get information about a token.
        
        Args:
            token: Tracking token
        
        Returns:
            Token information dictionary
        """
        if token not in self._tokens:
            return None
        
        return {
            **self._tokens[token],
            'clicks': self._clicks.get(token, [])
        }
    
    def get_click_stats(self, token):
        """
        Get click statistics for a token.
        
        Args:
            token: Tracking token
        
        Returns:
            Statistics dictionary
        """
        if token not in self._tokens:
            return None
        
        clicks = self._clicks.get(token, [])
        
        # Calculate statistics
        total_clicks = len(clicks)
        unique_ips = len(set(click['ip_address'] for click in clicks))
        
        # Group by date
        clicks_by_date = {}
        for click in clicks:
            date = click['timestamp'].split('T')[0]
            clicks_by_date[date] = clicks_by_date.get(date, 0) + 1
        
        # Group by user agent
        clicks_by_user_agent = {}
        for click in clicks:
            ua = click['user_agent'][:50]  # Truncate for readability
            clicks_by_user_agent[ua] = clicks_by_user_agent.get(ua, 0) + 1
        
        return {
            'total_clicks': total_clicks,
            'unique_ips': unique_ips,
            'clicks_by_date': clicks_by_date,
            'clicks_by_user_agent': clicks_by_user_agent,
            'first_click': clicks[0]['timestamp'] if clicks else None,
            'last_click': clicks[-1]['timestamp'] if clicks else None
        }
    
    def validate_email(self, email):
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
        
        Returns:
            Boolean indicating if email is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_url(self, url):
        """
        Validate URL format.
        
        Args:
            url: URL to validate
        
        Returns:
            Boolean indicating if URL is valid
        """
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url, re.IGNORECASE) is not None
    
    @staticmethod
    def _generate_click_hash(token, ip_address):
        """
        Generate a hash for click deduplication.
        
        Args:
            token: Tracking token
            ip_address: IP address
        
        Returns:
            Hash string
        """
        data = f"{token}:{ip_address}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def get_current_timestamp():
        """
        Get current UTC timestamp in ISO format.
        
        Returns:
            ISO format timestamp string
        """
        return datetime.utcnow().isoformat()
    
    def clear_all(self):
        """
        Clear all tokens and clicks (for testing).
        """
        self._tokens.clear()
        self._clicks.clear()
        logger.info('Cleared all tokens and clicks')
