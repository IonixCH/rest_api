# HRIS Backend - Odoo with REST API

HRIS (Human Resource Information System) backend menggunakan Odoo dengan custom REST API module untuk integrasi dengan Flutter mobile app.

## 📋 Overview

Project ini terdiri dari:
- **Backend**: Odoo 17 dengan custom REST API module
- **Database**: PostgreSQL 
- **Infrastructure**: Docker & Docker Compose
- **API**: REST endpoints untuk authentication, employees, leaves, attendance

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- PowerShell (Windows) atau Bash (Linux/Mac)

### 1. Clone & Setup
```bash
git clone <repository-url>
cd hris_backend

# Start containers
docker-compose up -d

# Wait for containers to be ready (30-60 seconds)
docker-compose ps
```

### 2. Install REST API Module
1. Open browser: http://localhost:8070
2. Create/Login to Odoo database
3. Go to Apps > Search "HRIS REST API" > Install

### 3. Test API
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8070/api/health" -Method GET

# Run comprehensive test
.\api-modules\hris_rest_api\test-api.ps1
```

## 🏗️ Architecture

```
hris_backend/
├── api-modules/           # Custom REST API modules
│   └── hris_rest_api/    # Main API module
├── custom-addons/        # Additional Odoo addons
├── config/               # Odoo configuration
├── docker-compose.yml    # Container orchestration
└── README.md            # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout  
- `GET /api/auth/profile` - Get user profile

### Health Check
- `GET /api/health` - API health status

### Employees (Coming Soon)
- `GET /api/employees` - List employees
- `GET /api/employees/{id}` - Get employee details
- `GET /api/departments` - List departments

### Leaves (Coming Soon)
- `GET /api/leaves` - List leave requests
- `POST /api/leaves` - Create leave request
- `GET /api/leave-types` - List leave types

### Attendance (Coming Soon)
- `POST /api/attendance/checkin` - Check in
- `POST /api/attendance/checkout` - Check out
- `GET /api/attendance` - Get attendance records

## 🧪 Testing API

### Method 1: PowerShell Script (Recommended)
```bash
# Run automated test script
.\api-modules\hris_rest_api\test-api.ps1

# With custom parameters
.\api-modules\hris_rest_api\test-api.ps1 -BaseUrl "http://localhost:8070" -Username "test@test.com"
```

### Method 2: VS Code REST Client
1. Install "REST Client" extension in VS Code
2. Open `api-modules/hris_rest_api/test-api.http`
3. Click "Send Request" on any endpoint

### Method 3: Manual cURL
```bash
# Health check
curl -X GET http://localhost:8070/api/health

# Login
curl -X POST http://localhost:8070/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "apitest@test.com", "password": "test123"}'
```

## 📚 Documentation

- **API Testing**: `api-modules/hris_rest_api/TESTING.md`
- **API Documentation**: `api-modules/hris_rest_api/README.md` 
- **Module Development**: See individual module READMEs

## 🔧 Development

### Adding New Endpoints
1. Edit controllers in `api-modules/hris_rest_api/controllers/`
2. Update `__init__.py` imports
3. Restart Odoo: `docker-compose restart web`
4. Test endpoints

### Custom Addons
- Add modules to `custom-addons/` directory
- Update `docker-compose.yml` volumes if needed
- Install via Odoo Apps interface

### Database Access
```bash
# Access PostgreSQL
docker exec -it hris_backend-db-1 psql -U odoo -d odoo

# Access Odoo shell
docker exec -it hris_backend-web-1 /usr/bin/odoo shell -d odoo --no-http --config=/etc/odoo/odoo.conf
```

## 🐛 Troubleshooting

### Common Issues

#### Container Issues
```bash
# Check container status
docker-compose ps

# View logs
docker logs hris_backend-web-1 --tail 50
docker logs hris_backend-db-1 --tail 20

# Restart containers
docker-compose restart
```

#### API Issues
```bash
# Check if module is installed
# Go to http://localhost:8070 > Apps > Search "HRIS REST API"

# Create test user
# See api-modules/hris_rest_api/TESTING.md
```

#### Database Issues
```bash
# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d
```

## 🔐 Security Notes

- Default credentials are for development only
- Change passwords in production
- Use HTTPS in production
- Implement proper session management
- Add rate limiting for production

## 📝 Environment Variables

Key variables in `docker-compose.yml`:
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password  
- `POSTGRES_DB`: Database name

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test API endpoints
4. Update documentation
5. Submit pull request

## 📞 Support

- Check logs: `docker logs hris_backend-web-1`
- Review documentation in `api-modules/hris_rest_api/`
- Test API: Run `test-api.ps1` script

---

**Happy Coding! 🚀**
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
