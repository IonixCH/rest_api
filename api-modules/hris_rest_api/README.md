# HRIS REST API Module

This module provides REST API endpoints for the HRIS Flutter application.

## Features

- **Authentication**: Login/logout with session management
- **Employee Management**: CRUD operations for employee data
- **Leave Management**: Create, approve, and track leave requests
- **Attendance Tracking**: Check-in/check-out functionality
- **CORS Support**: Full CORS support for Flutter apps
- **Error Handling**: Comprehensive error handling and logging

## API Endpoints

### Health Check
- `GET /api/health` - API health check
- `GET /api/version` - API version and endpoint information

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get current user profile
- `POST /api/auth/change-password` - Change user password

### Employees
- `GET /api/employees` - Get all employees (with pagination, search, filters)
- `GET /api/employees/<id>` - Get specific employee details
- `GET /api/departments` - Get all departments

### Leaves
- `GET /api/leaves` - Get leave requests (with filters)
- `POST /api/leaves` - Create new leave request
- `POST /api/leaves/<id>/approve` - Approve leave request
- `GET /api/leave-types` - Get available leave types
- `GET /api/leave-balance/<employee_id>` - Get employee leave balance

### Attendance
- `POST /api/attendance/checkin` - Employee check-in
- `POST /api/attendance/checkout` - Employee check-out
- `GET /api/attendance` - Get attendance records (with filters)
- `GET /api/attendance/status/<employee_id>` - Get current attendance status

## Installation

1. Place this module in your `api-modules` directory
2. Update `docker-compose.yml` to include the api-modules path
3. Update the addons list in Odoo
4. Install the module
5. The API endpoints will be available at your Odoo base URL

## API Response Format

All API endpoints return JSON responses in the following format:

```json
{
    "success": true/false,
    "message": "Response message",
    "data": { ... },
    "timestamp": "2025-06-24T10:30:00"
}
```

## Error Codes

- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## Usage Examples

### Health Check
```bash
# Test API availability
curl -X GET http://localhost:8070/api/health
```

### Authentication

#### Login
```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8070/api/auth/login" -Method POST -ContentType "application/json" -Body '{"username": "apitest@test.com", "password": "test123"}'

# cURL
curl -X POST http://localhost:8070/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "apitest@test.com", "password": "test123"}'

# Example Response
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user_id": 8,
    "username": "apitest@test.com",
    "session_token": "5a32652eafab0f5cdf22b070687eb813f68a44d6",
    "login_time": "2025-06-24T06:31:13.520036"
  },
  "timestamp": "2025-06-24T06:31:13.520045"
}
```

#### Logout
```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8070/api/auth/logout" -Method POST -Headers @{"Cookie"="session_id=YOUR_SESSION_TOKEN"}

# cURL
curl -X POST http://localhost:8070/api/auth/logout \
  -H "Cookie: session_id=YOUR_SESSION_TOKEN"
```

#### Get Profile
```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8070/api/auth/profile" -Method GET -Headers @{"Cookie"="session_id=YOUR_SESSION_TOKEN"}

# cURL
curl -X GET http://localhost:8070/api/auth/profile \
  -H "Cookie: session_id=YOUR_SESSION_TOKEN"
```

### Get Employees
```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8070/api/employees" -Method GET

# cURL
curl -X GET "http://localhost:8070/api/employees?limit=10&search=john" \
  -H "Cookie: session_id=your_session_id"
```

### Create Leave Request
```bash
# PowerShell
$leaveData = @{
  employee_id = 1
  holiday_status_id = 1
  request_date_from = "2025-07-01"
  request_date_to = "2025-07-05"
  name = "Summer Vacation"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8070/api/leaves" -Method POST -ContentType "application/json" -Body $leaveData -Headers @{"Cookie"="session_id=YOUR_SESSION_TOKEN"}

# cURL
curl -X POST http://localhost:8070/api/leaves \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=your_session_id" \
  -d '{
    "employee_id": 1,
    "holiday_status_id": 1,
    "request_date_from": "2025-07-01",
    "request_date_to": "2025-07-05",
    "name": "Summer Vacation"
  }'
```

## Testing Guide

### Prerequisites
1. **Docker Setup**: Make sure Docker containers are running
   ```bash
   cd f:\KULIAH\B\Magang\WIBICON\haris\hris_backend
   docker-compose up -d
   ```

2. **Module Installation**: Install HRIS REST API module in Odoo
   - Go to http://localhost:8070
   - Login to Odoo admin
   - Go to Apps > Search "HRIS REST API" > Install

3. **Test User**: Create a test user for API testing
   ```bash
   # Using Odoo shell
   docker exec -it hris_backend-web-1 /usr/bin/odoo shell -d odoo --no-http --config=/etc/odoo/odoo.conf
   
   # In shell, create user:
   user_vals = {
       'name': 'API Test User',
       'login': 'apitest@test.com',
       'password': 'test123'
   }
   new_user = env['res.users'].sudo().create(user_vals)
   env.cr.commit()
   print('Created user:', new_user.login, 'ID:', new_user.id)
   exit()
   ```

### Testing Steps

#### 1. Test Health Check
```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8070/api/health" -Method GET

# Expected Response
{
  "status": "ok",
  "message": "HRIS REST API is running"
}
```

#### 2. Test Authentication
```bash
# PowerShell - Login
$loginData = @{
  username = "apitest@test.com"
  password = "test123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8070/api/auth/login" -Method POST -ContentType "application/json" -Body $loginData

# Save session token for other requests
$sessionToken = $response.data.session_token
Write-Host "Session Token: $sessionToken"
```

#### 3. Test Authenticated Endpoints
```bash
# PowerShell - Get Profile
Invoke-RestMethod -Uri "http://localhost:8070/api/auth/profile" -Method GET -Headers @{"Cookie"="session_id=$sessionToken"}

# PowerShell - Get Employees
Invoke-RestMethod -Uri "http://localhost:8070/api/employees" -Method GET -Headers @{"Cookie"="session_id=$sessionToken"}

# PowerShell - Logout
Invoke-RestMethod -Uri "http://localhost:8070/api/auth/logout" -Method POST -Headers @{"Cookie"="session_id=$sessionToken"}
```

### Testing with Postman

1. **Import Collection**: Create a new collection in Postman
2. **Set Base URL**: `http://localhost:8070`
3. **Add Authentication**: 
   - Type: Cookie
   - Cookie: `session_id={{session_token}}`

#### Request Examples:

**Health Check**
- Method: GET
- URL: `{{base_url}}/api/health`

**Login**
- Method: POST
- URL: `{{base_url}}/api/auth/login`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
  ```json
  {
    "username": "apitest@test.com",
    "password": "test123"
  }
  ```

**Get Profile**
- Method: GET
- URL: `{{base_url}}/api/auth/profile`
- Headers: `Cookie: session_id={{session_token}}`

### Testing with HTTPie

```bash
# Install HTTPie
pip install httpie

# Health Check
http GET localhost:8070/api/health

# Login
http POST localhost:8070/api/auth/login username=apitest@test.com password=test123

# Get Profile (with session)
http GET localhost:8070/api/auth/profile Cookie:session_id=YOUR_SESSION_TOKEN
```

### Troubleshooting

#### Common Issues:

1. **404 Not Found**
   - Check if module is installed
   - Verify container is running
   - Check route registration

2. **401 Unauthorized**
   - Check username/password
   - Verify user exists in database
   - Check session token

3. **500 Internal Server Error**
   - Check Odoo logs: `docker logs hris_backend-web-1 --tail 50`
   - Verify database connection
   - Check module dependencies

#### Debug Commands:

```bash
# Check container status
docker-compose ps

# View Odoo logs
docker logs hris_backend-web-1 --tail 50

# Check database users
docker exec -it hris_backend-db-1 psql -U odoo -d odoo -c "SELECT id, login, active FROM res_users WHERE active = true;"

# Restart containers
docker-compose restart
```
### Module yang harus di install
- Open HRMS Core
- Open HRMS Overtime
- eLearning
- Skills Management 
- Skills eLearning
- hris_attendance_gps
- HRIS REST API
