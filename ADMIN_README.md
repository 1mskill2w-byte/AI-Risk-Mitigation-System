# AI Risk Mitigation System - Admin Panel

## Overview

The AI Risk Mitigation System now includes comprehensive admin panels for both main administrators and client administrators, along with a middleware system for seamless integration with client chatbots.

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Client Chatbot    │◄───┤  Risk Mitigation    │◄───┤   Admin Panels     │
│   (Your System)     │    │   Middleware        │    │                     │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • Frontend UI       │    │ • Risk Detection    │    │ • Main Admin        │
│ • Backend API       │    │ • Auto-Mitigation   │    │ • Client Admin      │
│ • User Management   │    │ • Usage Tracking    │    │ • Registration      │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Features

### For Main Company Owner (Main Admin)
- **Company Management**: View, create, edit, and delete client companies
- **Usage Analytics**: Monitor API usage across all clients
- **System Health**: Track system performance and error rates
- **Registration Oversight**: Manage client registrations and approvals
- **Global Reports**: Access comprehensive risk reports across all clients

### For Client Administrators
- **Risk Dashboard**: View detected risks specific to your company
- **Usage Monitoring**: Track your API quota and request statistics
- **Company Settings**: Configure chatbot URLs and integration settings
- **Risk Reports**: Detailed analysis of detected risks and mitigations
- **API Management**: Regenerate API keys and manage access credentials

### Risk Mitigation Middleware
- **Real-time Analysis**: Intercept and analyze requests before processing
- **Auto-Mitigation**: Apply appropriate risk mitigation strategies
- **Seamless Integration**: Works with any chatbot or AI system
- **API-First Design**: RESTful API for easy integration

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd AI-Risk-Mitigation-System

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the System

```bash
# Start both main API and admin panel
python start_system.py
```

### 3. Access Points

- **Main API & Dashboard**: http://localhost:8000
- **Admin Panel**: http://localhost:8001/admin/
- **API Documentation**: http://localhost:8000/docs
- **Admin API Docs**: http://localhost:8001/docs

### 4. Default Credentials

**Main Admin Login:**
- Username: `mainadmin`
- Password: `admin123`

## Client Registration Process

### Step 1: Company Registration
1. Visit: http://localhost:8001/admin/register
2. Fill out company information:
   - Company name and contact details
   - Industry and website
   - Admin account details

### Step 2: Chatbot Integration URLs
Configure your chatbot endpoints:
- **Frontend URL**: Your chatbot's user interface
- **Backend URL**: Your chatbot's API endpoint  
- **Webhook URL**: (Optional) For receiving risk notifications

### Step 3: API Credentials
After registration, you'll receive:
- **API Key**: For authentication
- **API Secret**: For secure access
- **Admin Login**: Access to your company dashboard

## Integration Examples

### Python Integration
```python
import requests

def check_risk(text_input):
    url = "http://localhost:8000/api/analyze"
    headers = {
        "X-API-Key": "your-api-key",
        "X-API-Secret": "your-api-secret"
    }
    data = {"text": text_input}
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Usage
risk_result = check_risk("User input text")
if risk_result["risk_detected"]:
    print(f"Risk Level: {risk_result['risk_level']}")
```

### JavaScript Integration
```javascript
async function checkRisk(textInput) {
    const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your-api-key',
            'X-API-Secret': 'your-api-secret'
        },
        body: JSON.stringify({ text: textInput })
    });
    
    return await response.json();
}
```

## Admin Panel Features

### Main Admin Dashboard
- **Company Overview**: Total companies, active users, system health
- **Usage Analytics**: Request volumes, risk detection rates
- **Recent Activity**: New registrations, recent risk reports
- **System Monitoring**: Performance metrics and error tracking

### Client Admin Dashboard  
- **Risk Overview**: Company-specific risk statistics
- **API Usage**: Quota tracking and request monitoring
- **Company Profile**: Manage company information and URLs
- **Risk Reports**: Detailed risk analysis and trends

## Database Schema

### Core Tables
- **admin_users**: Admin account information
- **companies**: Client company details and API credentials
- **risk_reports**: Detected risks and mitigation actions
- **system_usage**: API usage tracking and metrics
- **api_quotas**: Rate limiting and quota management

### Key Relationships
```sql
companies (1) ──► (n) admin_users
companies (1) ──► (n) risk_reports  
companies (1) ──► (1) api_quotas
```

## Security Features

### Authentication
- **JWT Token-based**: Secure session management
- **Password Hashing**: bcrypt for password security
- **API Key Authentication**: Secure client API access

### Authorization
- **Role-based Access**: Main admin vs client admin permissions
- **Company Isolation**: Clients can only access their own data
- **API Rate Limiting**: Prevent abuse and ensure fair usage

### Data Protection
- **Input Sanitization**: All inputs validated and sanitized
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Output encoding and CSP headers

## API Reference

### Risk Analysis Endpoint
```
POST /api/analyze
Headers:
  X-API-Key: string
  X-API-Secret: string
  Content-Type: application/json

Body:
{
  "text": "Text to analyze",
  "context": "optional context",
  "user_id": "optional user ID"
}

Response:
{
  "risk_detected": boolean,
  "risk_level": "low|medium|high|critical",
  "risk_score": float,
  "detected_risks": {...},
  "recommendations": [...]
}
```

### Admin API Endpoints
- `GET /admin/main/dashboard` - Main admin dashboard data
- `GET /admin/main/companies` - List all companies
- `POST /admin/main/companies` - Create new company
- `GET /admin/client/dashboard` - Client dashboard data
- `GET /admin/client/reports` - Client risk reports

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./admin_panel.db

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480

# API Settings
DEFAULT_DAILY_LIMIT=100
DEFAULT_MONTHLY_LIMIT=1000
```

### Risk Thresholds
```json
{
  "bias": {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
  },
  "pii": {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8
  }
}
```

## Deployment

### Production Setup
```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export SECRET_KEY=your-production-secret-key

# Run with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker admin_app:admin_app --bind 0.0.0.0:8001
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8001

CMD ["python", "start_system.py"]
```

## Monitoring & Maintenance

### Health Checks
- `GET /health` - Main API health
- `GET /admin/health` - Admin panel health

### Logging
- Structured logging with JSON format
- Request/response logging for debugging
- Error tracking and alerting

### Backup & Recovery
- Regular database backups
- Configuration backup
- Disaster recovery procedures

## Support & Documentation

### Additional Resources
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **API Documentation**: http://localhost:8001/docs
- **Client Examples**: `examples/` directory

### Troubleshooting
1. **Database Issues**: Check DATABASE_URL and permissions
2. **Authentication Errors**: Verify API keys and secrets
3. **Rate Limiting**: Check quota usage in admin dashboard
4. **Performance**: Monitor CPU/memory usage and scale accordingly

### Contact
- **Issues**: Create GitHub issues for bug reports
- **Features**: Submit feature requests through admin panel
- **Security**: Report security issues privately

## License

This project is licensed under the MIT License - see the LICENSE file for details.
