# Egor Mailer - Email Link Tracking System

A Flask-based email link tracking application that monitors email opens and link clicks using Google Sheets as a backend database.

## Features

- **Email Link Tracking**: Generate unique tracking tokens for email campaigns
- **Click Analytics**: Track clicks with IP addresses and user agent information
- **Google Sheets Integration**: Store and analyze data in Google Sheets
- **Campaign Management**: Track different email campaigns separately
- **Real-time Statistics**: Get click statistics for any tracking token
- **Health Monitoring**: Built-in health check endpoint for monitoring

## Prerequisites

- Python 3.7+
- Google Cloud Project with Sheets API enabled
- Service account credentials (or OAuth 2.0 credentials)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hotline999/egor-mailer.git
   cd egor-mailer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Sheets API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create OAuth 2.0 credentials (Service Account or Desktop Application)
   - Download credentials as JSON and save as `credentials.json`

5. **Create environment file**
   ```bash
   cp .env.example .env
   ```

6. **Configure .env file**
   ```env
   FLASK_ENV=development
   FLASK_DEBUG=True
   SECRET_KEY=your-secret-key-here
   GOOGLE_SHEETS_ID=your-google-sheets-id
   GOOGLE_CREDENTIALS_FILE=credentials.json
   TRACKER_BASE_URL=http://localhost:5000
   PORT=5000
   HOST=0.0.0.0
   ```

## Usage

### Running the Application

```bash
python main.py
```

The application will start on `http://localhost:5000`

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-02T22:00:14.123456"
}
```

#### 2. Generate Tracking Token
```bash
POST /generate-token
Content-Type: application/json

{
  "target_url": "https://example.com/offer",
  "email": "user@example.com",
  "campaign": "winter-sale-2026"
}
```

Response:
```json
{
  "token": "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890",
  "tracker_url": "http://localhost:5000/track/AbCdEfGhIjKlMnOpQrStUvWxYz1234567890",
  "target_url": "https://example.com/offer",
  "campaign": "winter-sale-2026"
}
```

#### 3. Track Click
```bash
GET /track/{token}
```

Automatically redirects to the target URL and logs the click.

Response (if no target URL): 
```json
{
  "message": "Click tracked successfully"
}
```

#### 4. Get Click Statistics
```bash
GET /stats/{token}
```

Response:
```json
{
  "token": "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890",
  "total_clicks": 42,
  "unique_ips": 38,
  "clicks_by_date": {
    "2026-01-02": 15,
    "2026-01-03": 27
  },
  "clicks_by_user_agent": {
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...": 20,
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)...": 22
  }
}
```

## Project Structure

```
egor-mailer/
├── main.py              # Flask application and routes
├── config.py            # Configuration management
├── tracker.py           # Click tracking logic
├── sheets_api.py        # Google Sheets integration
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Environment variables (not in git)
├── credentials.json    # Google API credentials (not in git)
├── token.json          # OAuth token cache (not in git)
└── README.md           # This file
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `FLASK_ENV` | Flask environment | development |
| `FLASK_DEBUG` | Enable Flask debug mode | False |
| `SECRET_KEY` | Flask secret key | dev-secret-key-change-in-production |
| `GOOGLE_SHEETS_ID` | Google Sheets document ID | - |
| `GOOGLE_CREDENTIALS_FILE` | Path to Google credentials JSON | credentials.json |
| `TRACKER_BASE_URL` | Base URL for tracking links | http://localhost:5000 |
| `PORT` | Application port | 5000 |
| `HOST` | Application host | 0.0.0.0 |
| `TOKEN_EXPIRY_DAYS` | Token expiration in days | 90 |
| `TOKEN_LENGTH` | Token length in bytes | 32 |
| `MAX_REDIRECTS` | Maximum redirect limit | 10 |
| `LOG_LEVEL` | Logging level | INFO |

## Email Integration Example

### Generate a tracking link:

```python
import requests

response = requests.post('http://localhost:5000/generate-token', json={
    'target_url': 'https://example.com/special-offer',
    'email': 'customer@example.com',
    'campaign': 'new-year-promo'
})

tracking_data = response.json()
tracking_url = tracking_data['tracker_url']
print(f"Include this link in email: {tracking_url}")
```

### Use in email template:

```html
<a href="{tracking_url}">Click here for your exclusive offer!</a>
```

## Google Sheets Data Structure

### Tokens Sheet
Columns:
- Timestamp: When the token was created
- Token: The unique tracking token
- Target URL: URL that will be redirected to
- Email: Recipient email address
- Campaign: Campaign name
- Status: Token status (Active/Inactive)

### Clicks Sheet
Columns:
- Timestamp: When the click occurred
- Token: Associated tracking token
- IP Address: Clicker's IP address
- User Agent: Clicker's browser info
- Click Count: Number of clicks (aggregate)

## Security Considerations

1. **Secret Key**: Change `SECRET_KEY` in production to a strong random value
2. **Credentials**: Never commit `credentials.json` or `token.json` to git
3. **HTTPS**: Use HTTPS in production (configure with reverse proxy)
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Input Validation**: All user inputs are validated
6. **Access Control**: Protect sensitive endpoints with authentication

## Logging

Logs are output to console and optionally to a file. Configure logging level in `.env`:

```env
LOG_LEVEL=INFO
LOG_FILE=egor_mailer.log
```

## Error Handling

The application includes comprehensive error handling:

- **404**: Not found errors
- **400**: Invalid requests
- **500**: Internal server errors
- **503**: Service unavailable (Sheets API issues)

## Testing

Test the application with curl:

```bash
# Health check
curl http://localhost:5000/health

# Generate token
curl -X POST http://localhost:5000/generate-token \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com", "campaign": "test"}'

# Get stats
curl http://localhost:5000/stats/{token}
```

## Troubleshooting

### Google Sheets API Errors

1. **File not found**: Ensure `credentials.json` exists and `GOOGLE_SHEETS_ID` is set
2. **Permission denied**: Check Google Cloud service account permissions
3. **API not enabled**: Enable Sheets API in Google Cloud Console

### Connection Issues

1. Check internet connection
2. Verify Google API credentials are valid
3. Check firewall and proxy settings
4. Review application logs for detailed errors

## Performance Tips

1. Use environment variables for configuration
2. Enable Flask debug mode only in development
3. Consider adding caching for statistics queries
4. Monitor Google Sheets API quota usage
5. Implement database backend for better scalability

## Future Enhancements

- [ ] Database backend (PostgreSQL/MongoDB)
- [ ] Email verification and tracking
- [ ] Advanced analytics and reporting
- [ ] A/B testing support
- [ ] Webhook notifications
- [ ] API authentication and rate limiting
- [ ] Web dashboard for analytics
- [ ] Bulk token generation
- [ ] Custom tracking parameters
- [ ] Export statistics to various formats

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Changelog

### Version 1.0.0 (2026-01-02)
- Initial release
- Basic link tracking functionality
- Google Sheets integration
- Click statistics and analytics
- Health check and monitoring endpoints

---

**Made with ❤️ by Egor Mailer Team**
