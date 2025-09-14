import json
import logging
from datetime import datetime, timedelta
from odoo import http  # type: ignore
from odoo.http import request  # type: ignore
from .session_manager import session_manager
from .base_controller import BaseController

_logger = logging.getLogger(__name__)

class AuthController(BaseController):
    # Removed duplicate methods - using from BaseController

    @http.route('/api/auth/login', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def login(self):
        """Login endpoint with proper session management"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            username = data.get('username') or data.get('email')
            password = data.get('password')
            if not username or not password:
                return self._error_response("Username and password are required", 400)
            uid = request.session.authenticate(request.session.db, username, password)
            if uid:
                user = request.env['res.users'].sudo().browse(uid)
                employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
                partner = user.partner_id
                # Jika employee belum ada, buat otomatis
                if not employee:
                    _logger.info(f"Creating employee record for user: {user.login}")
                    try:
                        default_company = request.env['res.company'].sudo().search([], limit=1)
                        if not default_company:
                            default_company = request.env.ref('base.main_company')
                        resource = request.env['resource.resource'].sudo().create({
                            'name': user.name,
                            'user_id': user.id,
                            'company_id': default_company.id,
                        })
                        employee = request.env['hr.employee'].sudo().create({
                            'name': user.name,
                            'user_id': user.id,
                            'work_email': user.email,
                            'company_id': default_company.id,
                            'resource_id': resource.id,
                        })
                        _logger.info(f"Employee created successfully with ID: {employee.id}")
                    except Exception as emp_error:
                        _logger.error(f"Failed to create employee: {str(emp_error)}")
                session_token = request.session.sid
                session_manager.store_session(session_token, uid)
                request.session['user_id'] = uid
                request.session['login_time'] = datetime.now().isoformat()
                user_data = {
                    'user_id': uid,
                    'username': user.login,
                    'name': user.name,
                    'email': user.email,
                    'phone': employee.work_phone or partner.phone or '',
                    'session_token': session_token,
                    'employee_id': employee.id if employee else None,
                    'employee_name': employee.name if employee else None,
                    'department_id': employee.department_id.id if employee and employee.department_id else None,
                    'department_name': employee.department_id.name if employee and employee.department_id else "",
                }
                response = self._json_response(
                    data=user_data,
                    message="Login successful"
                )
                response.set_cookie(
                    'session_id',
                    session_token,
                    max_age=60*60*24*7,
                    httponly=False,
                    secure=False,
                    samesite='Lax'
                )
                return response
            else:
                return self._error_response("Invalid username or password", 401)
        except Exception as e:
            _logger.error(f"Login error: {str(e)}")
            return self._error_response("Internal server error", 500)

    @http.route('/api/auth/logout', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def logout(self):
        """Logout endpoint"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        try:
            auth_header = request.httprequest.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                session_token = auth_header.replace('Bearer ', '')
                session_manager.remove_session(session_token)
                try:
                    if hasattr(request, 'session') and request.session:
                        request.session.logout()
                except:
                    pass
            return self._json_response(message="Logout successful")
        except Exception as e:
            _logger.error(f"Logout error: {str(e)}")
            return self._json_response(message="Logout completed")

    @http.route('/api/auth/profile', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_profile(self):
        """Get current user profile"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        try:
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return self._error_response("Session token required", 401)
            session_token = auth_header.replace('Bearer ', '')
            _logger.info(f"Profile request with token: {session_token}")
            uid = session_manager.get_user_id(session_token)
            if not uid:
                return self._error_response("Invalid or expired session", 401)
            user = request.env['res.users'].sudo().browse(uid)
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            partner = user.partner_id
            profile_data = {
                'user_id': user.id,
                'username': user.login,
                'name': user.name,
                'email': user.email,
                'session_token': session_token,
                'employee_id': employee.id if employee else None,
                'employee_name': employee.name if employee else None,
                'department_id': employee.department_id.id if employee and employee.department_id else None,
                'department_name': employee.department_id.name if employee and employee.department_id else "",
                'job_id': employee.job_id.id if employee and employee.job_id else None,
                'job_name': employee.job_id.name if employee and employee.job_id else "",
                'phone': employee.work_phone or partner.phone or '',
            }
            return self._json_response(
                data=profile_data,
                message="Profile retrieved successfully"
            )
        except Exception as e:
            _logger.error(f"Profile error: {str(e)}")
            return self._error_response("Failed to retrieve profile", 500)

    @http.route('/api/auth/register', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def register(self):
        """Register new user endpoint"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            name = data.get('name')
            confirm_password = data.get('confirm_password')
            phone = data.get('phone')
            if not all([username, email, password, name]):
                return self._error_response("Username, email, password, and name are required", 400)
            if confirm_password and password != confirm_password:
                return self._error_response("Password and confirm password do not match", 400)
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return self._error_response("Invalid email format", 400)
            existing_user_by_login = request.env['res.users'].sudo().search([('login', '=', username)], limit=1)
            existing_user_by_email = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
            if existing_user_by_login:
                return self._error_response("Username already exists", 409)
            if existing_user_by_email:
                return self._error_response("Email already exists", 409)
            try:
                _logger.info(f"Register data: username={username}, email={email}, phone={phone}, name={name}")
                default_company = request.env['res.company'].sudo().search([], limit=1)
                if not default_company:
                    return self._error_response("No company found in system", 500)
                with request.env.cr.savepoint():
                    # Create partner
                    request.env.cr.execute("""
                        INSERT INTO res_partner (name, email, phone, is_company, company_id, create_date, write_date)
                        VALUES (%s, %s, %s, false, %s, NOW(), NOW())
                        RETURNING id
                    """, (name, email, phone, default_company.id))
                    partner_id = request.env.cr.fetchone()[0]
                    _logger.info(f"Partner created with ID: {partner_id}")
                    # Create user
                    request.env.cr.execute("""
                        INSERT INTO res_users (
                            login, password, partner_id, active, 
                            company_id, create_date, write_date, notification_type
                        )
                        VALUES (%s, %s, %s, true, %s, NOW(), NOW(), 'email')
                        RETURNING id
                    """, (username, password, partner_id, default_company.id))
                    user_id = request.env.cr.fetchone()[0]
                    _logger.info(f"User created with ID: {user_id}")
                    # Add user to company
                    request.env.cr.execute("""
                        INSERT INTO res_company_users_rel (user_id, cid)
                        VALUES (%s, %s)
                    """, (user_id, default_company.id))
                    # Add user to group Internal User
                    internal_group_id = request.env.ref('base.group_user').id
                    request.env.cr.execute("""
                        INSERT INTO res_groups_users_rel (gid, uid)
                        VALUES (%s, %s)
                    """, (internal_group_id, user_id))
                    # Create resource
                    request.env.cr.execute("""
                        INSERT INTO resource_resource (
                            name, user_id, company_id, active, tz,
                            create_date, write_date, resource_type, time_efficiency
                        )
                        VALUES (%s, %s, %s, true, 'Asia/Jakarta', NOW(), NOW(), 'user', 100)
                        RETURNING id
                    """, (name, user_id, default_company.id))
                    resource_id = request.env.cr.fetchone()[0]
                    _logger.info(f"Resource created with ID: {resource_id}")
                    # Create employee
                    request.env.cr.execute("""
                        INSERT INTO hr_employee (
                            name, user_id, work_email, work_phone, company_id, resource_id,
                            active, employee_type, create_date, write_date
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, true, 'employee', NOW(), NOW())
                        RETURNING id
                    """, (name, user_id, email, phone, default_company.id, resource_id))
                    employee_id = request.env.cr.fetchone()[0]
                    _logger.info(f"Employee created with ID: {employee_id}")
                    # Update join date
                    join_date = datetime.now().date().isoformat()
                    request.env.cr.execute("""
                        UPDATE hr_employee SET first_contract_date = %s, joining_date = %s WHERE id = %s
                    """, (join_date, join_date, employee_id))
                    _logger.info(f"Set first_contract_date & joining_date for employee {employee_id} to {join_date}")
                    _logger.info(f"User registered successfully: {username} (ID: {user_id}, Employee ID: {employee_id})")
                user_data = {
                    'user_id': user_id,
                    'username': username,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'employee_id': employee_id,
                    'created_at': datetime.now().isoformat(),
                }
                return self._json_response(
                    data=user_data,
                    message="User registered successfully"
                )
            except Exception as e:
                _logger.error(f"User creation error: {str(e)}")
                return self._error_response(f"Failed to create user: {str(e)}", 500)
        except json.JSONDecodeError:
            return self._error_response("Invalid JSON data", 400)
        except Exception as e:
            _logger.error(f"Registration error: {str(e)}")
            return self._error_response("Internal server error", 500)

    @http.route('/api/auth/change-password', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def change_password(self):
        """Change user password endpoint"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        try:
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return self._error_response("Session token required", 401)
            session_token = auth_header.replace('Bearer ', '')
            data = json.loads(request.httprequest.data.decode('utf-8'))
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            if not current_password or not new_password:
                return self._error_response("Current password and new password are required", 400)
            if len(new_password) < 6:
                return self._error_response("New password must be at least 6 characters", 400)
            user_id = session_manager.get_user_id(session_token)
            if not user_id:
                return self._error_response("Invalid or expired session", 401)
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._error_response("User not found", 404)
            try:
                uid = request.session.authenticate(request.session.db, user.login, current_password)
                if not uid:
                    return self._error_response("Current password is incorrect", 401)
            except Exception:
                return self._error_response("Current password is incorrect", 401)
            try:
                user.sudo().write({'password': new_password})
                return self._json_response(
                    data={'message': 'Password changed successfully'},
                    message="Password changed successfully"
                )
            except Exception as e:
                _logger.error(f"Password update error: {str(e)}")
                return self._error_response("Failed to update password", 500)
        except json.JSONDecodeError:
            return self._error_response("Invalid JSON data", 400)
        except Exception as e:
            _logger.error(f"Change password error: {str(e)}")
            return self._error_response("Failed to change password", 500)