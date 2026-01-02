import os
import logging
from flask import Flask, request, redirect, jsonify
from dotenv import load_dotenv
from config import Config
from tracker import LinkTracker
from sheets_api import SheetsAPI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
tracker = LinkTracker()
sheets_api = SheetsAPI()


@app.route('/')
def index():
    """Home page with API documentation."""
    return jsonify({
        'name': 'Egor Mailer - Email Link Tracker',
        'version': '1.0.0',
        'endpoints': {
            'track': '/track/<token>',
            'stats': '/stats/<token>',
            'health': '/health',
            'generate': '/generate-token'
        }
    })


@app.route('/track/<token>')
def track_click(token):
    """Track email link clicks."""
    try:
        # Get IP and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Track the click
        result = tracker.track_click(token, ip_address, user_agent)
        
        if result['success']:
            # Get target URL
            target_url = result.get('target_url')
            
            # Log click to Google Sheets
            sheets_api.log_click(
                token=token,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=result.get('timestamp'),
                target_url=target_url
            )
            
            # Redirect to target URL if available
            if target_url:
                return redirect(target_url)
            else:
                return jsonify({'message': 'Click tracked successfully'})
        else:
            logger.warning(f'Invalid or expired token: {token}')
            return jsonify({'error': 'Invalid or expired token'}), 404
    
    except Exception as e:
        logger.error(f'Error tracking click for token {token}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/stats/<token>')
def get_stats(token):
    """Get click statistics for a token."""
    try:
        stats = sheets_api.get_click_stats(token)
        
        if stats is not None:
            return jsonify({
                'token': token,
                'total_clicks': stats.get('total_clicks', 0),
                'unique_ips': stats.get('unique_ips', 0),
                'clicks_by_date': stats.get('clicks_by_date', {}),
                'clicks_by_user_agent': stats.get('clicks_by_user_agent', {})
            })
        else:
            return jsonify({'error': 'Token not found'}), 404
    
    except Exception as e:
        logger.error(f'Error getting stats for token {token}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        sheets_api.check_connection()
        return jsonify({
            'status': 'healthy',
            'timestamp': tracker.get_current_timestamp()
        })
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


@app.route('/generate-token', methods=['POST'])
def generate_token():
    """Generate a new tracking token."""
    try:
        data = request.get_json() or {}
        target_url = data.get('target_url')
        email = data.get('email')
        campaign = data.get('campaign', 'default')
        
        if not target_url:
            return jsonify({'error': 'target_url is required'}), 400
        
        # Generate token
        token = tracker.generate_token(target_url, email, campaign)
        
        # Log to sheets
        sheets_api.log_token_creation(
            token=token,
            target_url=target_url,
            email=email,
            campaign=campaign
        )
        
        tracker_url = f"{Config.TRACKER_BASE_URL}/track/{token}"
        
        return jsonify({
            'token': token,
            'tracker_url': tracker_url,
            'target_url': target_url,
            'campaign': campaign
        }), 201
    
    except Exception as e:
        logger.error(f'Error generating token: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f'Internal server error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', False) == 'True'
    
    logger.info(f'Starting Egor Mailer on {host}:{port}')
    app.run(host=host, port=port, debug=debug)
