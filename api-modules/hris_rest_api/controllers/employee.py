import json
import logging
import base64
from odoo import http # type: ignore
from odoo.http import request # type: ignore
from .base_controller import BaseController

_logger = logging.getLogger(__name__)

class EmployeeController(BaseController):
    @http.route('/api/employees/<int:user_id>', type='http', auth='none', methods=['PUT', 'OPTIONS'], csrf=False)
    def update_employee(self, user_id):
        """Update employee data based on user_id"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session using our authentication method
            auth_user = self._get_user_from_session()
            if not auth_user:
                return self._error_response("Authentication required", 401)
            
            # Security: user can only update their own profile
            if auth_user.id != user_id:
                return self._error_response("Access denied: You can only update your own profile", 403)
            
            # Get user record
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._error_response("User not found", 404)
                
            # Get or create employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
            if not employee:
                # Create employee if not exists
                default_company = request.env['res.company'].sudo().search([], limit=1)
                employee = request.env['hr.employee'].sudo().create({
                    'name': user.name,
                    'user_id': user_id,
                    'work_email': user.email,
                    'company_id': default_company.id if default_company else 1,
                })
                _logger.info(f"Created new employee record for user {user_id}")

            raw_data = request.httprequest.data.decode('utf-8')
            _logger.info(f"[UPDATE PROFILE] Raw data: {raw_data}")
            data = json.loads(raw_data)
            
            # Fields for hr.employee table
            employee_fields = [
                'job_title', 'birthday', 'work_phone', 'mobile_phone', 'department_id', 'job_id', 
                'parent_id', 'address_id', 'employee_type', 'gender', 'marital', 'country_id', 
                'identification_id', 'passport_id', 'private_email', 'emergency_contact', 'emergency_phone'
            ]
            
            # Fields for res.users table
            user_fields = ['name', 'email']
            
            # Handle username separately
            if 'username' in data:
                user_fields.append('username')
            
            relasi_fields = ['department_id', 'job_id', 'parent_id', 'address_id', 'country_id']
            
            employee_vals = {}
            user_vals = {}
            
            for k, v in data.items():
                if k in employee_fields:
                    if k in relasi_fields:
                        try:
                            employee_vals[k] = int(v) if v is not None and v != '' else False
                        except Exception:
                            employee_vals[k] = False
                    else:
                        employee_vals[k] = v
                elif k in user_fields:
                    # Handle username field mapping
                    if k == 'username':
                        user_vals['login'] = v
                    else:
                        user_vals[k] = v
                        
            # Update employee record
            if employee_vals:
                _logger.info(f"[UPDATE EMPLOYEE] Employee vals: {employee_vals}")
                employee.sudo().write(employee_vals)
                
            # Update user record  
            if user_vals:
                _logger.info(f"[UPDATE USER] User vals: {user_vals}")
                user.sudo().write(user_vals)
                
            # Also update employee name if user name changed
            if 'name' in user_vals:
                employee.sudo().write({'name': user_vals['name']})
                
            # Also update employee work_email if user email changed
            if 'email' in user_vals:
                employee.sudo().write({'work_email': user_vals['email']})
                
            _logger.info(f"Profile updated for user {user_id}")
            
            return self._json_response(
                data={
                    'user_id': user_id,
                    'employee_id': employee.id,
                    'updated_fields': list(set(list(employee_vals.keys()) + list(user_vals.keys())))
                },
                message="Profile updated successfully"
            )
        except Exception as e:
            _logger.error(f"Employee update error: {str(e)}")
            return self._error_response("Failed to update employee", 500)
    
    @http.route('/api/employees', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def list_employees(self):
        """List all employees with pagination"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get query parameters
            args = request.httprequest.args
            limit = int(args.get('limit', 20))
            offset = int(args.get('offset', 0))
            search = args.get('search', '')
            
            # Build domain for search
            domain = []
            if search:
                domain = ['|', '|', ('name', 'ilike', search), ('work_email', 'ilike', search), ('job_title', 'ilike', search)]
            
            # Get employees with limit and offset
            employees = request.env['hr.employee'].search(domain, limit=limit, offset=offset, order='name asc')
            total_count = request.env['hr.employee'].search_count(domain)
            
            # Format employee data
            employee_list = []
            for emp in employees:
                employee_data = {
                    'id': emp.id,
                    'name': emp.name,
                    'work_email': emp.work_email or '',
                    'work_phone': emp.work_phone or '',
                    'mobile_phone': emp.mobile_phone or '',
                    'job_title': emp.job_title or '',
                    'department': emp.department_id.name if emp.department_id else '',
                    'user_id': emp.user_id.id if emp.user_id else None,
                    'active': emp.active,
                    'birthday': emp.birthday.strftime('%Y-%m-%d') if emp.birthday else None,
                    'gender': emp.gender or '',
                    'image_url': f'/web/image/hr.employee/{emp.id}/image_1920' if emp.image_1920 else None,
                }
                employee_list.append(employee_data)
            
            return self._json_response(
                data={
                    'employees': employee_list,
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset
                },
                message="Employees retrieved successfully"
            )
        except Exception as e:
            _logger.error(f"Employee list error: {str(e)}")
            return self._error_response("Failed to retrieve employees", 500)
    
    @http.route('/api/employees/<int:employee_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_employee(self, employee_id):
        """Get employee details by ID"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get employee
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return self._error_response("Employee not found", 404)
            
            # Format employee data
            employee_data = {
                'id': employee.id,
                'name': employee.name,
                'work_email': employee.work_email or '',
                'work_phone': employee.work_phone or '',
                'mobile_phone': employee.mobile_phone or '',
                'job_title': employee.job_title or '',
                'department': employee.department_id.name if employee.department_id else '',
                'department_id': employee.department_id.id if employee.department_id else None,
                'job_id': employee.job_id.id if employee.job_id else None,
                'user_id': employee.user_id.id if employee.user_id else None,
                'active': employee.active,
                'birthday': employee.birthday.strftime('%Y-%m-%d') if employee.birthday else None,
                'gender': employee.gender or '',
                'marital': employee.marital or '',
                'country_id': employee.country_id.id if employee.country_id else None,
                'identification_id': employee.identification_id or '',
                'passport_id': employee.passport_id or '',
                'private_email': employee.private_email or '',
                'emergency_contact': employee.emergency_contact or '',
                'emergency_phone': employee.emergency_phone or '',
                'image_url': f'/web/image/hr.employee/{employee.id}/image_1920' if employee.image_1920 else None,
            }
            
            return self._json_response(
                data=employee_data,
                message="Employee retrieved successfully"
            )
        except Exception as e:
            _logger.error(f"Employee get error: {str(e)}")
            return self._error_response("Failed to retrieve employee", 500)
    
    @http.route('/api/employees/<int:user_id>/photo', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def upload_employee_photo(self, user_id):
        """Upload employee photo"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        
        try:
            # Get user from session
            auth_user = self._get_user_from_session()
            if not auth_user:
                return self._error_response("Authentication required", 401)
            
            # Security: user can only update their own photo
            if auth_user.id != user_id:
                return self._error_response("Access denied: You can only update your own photo", 403)
            
            # Get user record
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._error_response("User not found", 404)
                
            # Get or create employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
            if not employee:
                # Create employee if not exists
                default_company = request.env['res.company'].sudo().search([], limit=1)
                employee = request.env['hr.employee'].sudo().create({
                    'name': user.name,
                    'user_id': user_id,
                    'work_email': user.email,
                    'company_id': default_company.id if default_company else 1,
                })
                _logger.info(f"Created new employee record for user {user_id}")

            # Handle file upload
            if 'photo' not in request.httprequest.files:
                return self._error_response("No photo file provided", 400)
            
            photo_file = request.httprequest.files['photo']
            if photo_file.filename == '':
                return self._error_response("No photo file selected", 400)
            
            # Check file type
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_extension = photo_file.filename.lower().split('.')[-1] if '.' in photo_file.filename else ''
            if file_extension not in allowed_extensions:
                return self._error_response(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}", 400)
            
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            photo_file.seek(0, 2)  # Seek to end
            file_size = photo_file.tell()
            photo_file.seek(0)  # Seek back to beginning
            
            if file_size > max_size:
                return self._error_response("File size too large. Maximum 5MB allowed", 400)
            
            # Read and encode file
            photo_data = photo_file.read()
            photo_base64 = base64.b64encode(photo_data).decode('utf-8')
            
            # Update employee photo
            employee.sudo().write({
                'image_1920': photo_base64
            })
            
            _logger.info(f"Photo uploaded for employee {employee.id} (user {user_id})")
            
            return self._json_response(
                data={
                    'employee_id': employee.id,
                    'user_id': user_id,
                    'image_url': f'/web/image/hr.employee/{employee.id}/image_1920',
                    'file_size': file_size,
                    'file_name': photo_file.filename
                },
                message="Photo uploaded successfully"
            )
        
        except Exception as e:
            _logger.error(f"Photo upload error: {str(e)}")
            return self._error_response("Failed to upload photo", 500)
    
    @http.route('/api/employees/<int:user_id>/photo', type='http', auth='none', methods=['DELETE', 'OPTIONS'], csrf=False)
    def delete_employee_photo(self, user_id):
        """Delete employee photo"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        
        try:
            # Get user from session
            auth_user = self._get_user_from_session()
            if not auth_user:
                return self._error_response("Authentication required", 401)
            
            # Security: user can only delete their own photo
            if auth_user.id != user_id:
                return self._error_response("Access denied: You can only delete your own photo", 403)
            
            # Get employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
            if not employee:
                return self._error_response("Employee not found", 404)
            
            # Remove photo
            employee.sudo().write({
                'image_1920': False
            })
            
            _logger.info(f"Photo deleted for employee {employee.id} (user {user_id})")
            
            return self._json_response(
                data={
                    'employee_id': employee.id,
                    'user_id': user_id
                },
                message="Photo deleted successfully"
            )
        
        except Exception as e:
            _logger.error(f"Photo delete error: {str(e)}")
            return self._error_response("Failed to delete photo", 500)
    
    @http.route('/api/employees/<int:user_id>/photo', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_employee_photo(self, user_id):
        """Get employee photo URL"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        
        try:
            # Get user from session
            auth_user = self._get_user_from_session()
            if not auth_user:
                return self._error_response("Authentication required", 401)
            
            # Get employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
            if not employee:
                return self._error_response("Employee not found", 404)
            
            # Return photo info with custom download URL
            photo_data = {
                'employee_id': employee.id,
                'user_id': user_id,
                'has_photo': bool(employee.image_1920),
                'image_url': f'/api/employees/{user_id}/photo/download' if employee.image_1920 else None
            }
            
            return self._json_response(
                data=photo_data,
                message="Photo info retrieved successfully"
            )
        
        except Exception as e:
            _logger.error(f"Photo get error: {str(e)}")
            return self._error_response("Failed to retrieve photo info", 500)
    
    @http.route('/api/employees/<int:user_id>/photo/download', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def download_employee_photo(self, user_id):
        """Download employee photo directly"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        
        try:
            # Get user from session
            auth_user = self._get_user_from_session()
            if not auth_user:
                return self._error_response("Authentication required", 401)
            
            # Get employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)], limit=1)
            if not employee:
                return self._error_response("Employee not found", 404)
            
            if not employee.image_1920:
                return self._error_response("No photo found", 404)
            
            # Return image data directly
            import base64
            from werkzeug.wrappers import Response
            
            image_data = base64.b64decode(employee.image_1920)
            
            # Create response with image
            response = Response(
                image_data,
                mimetype='image/jpeg',
                headers={
                    'Content-Type': 'image/jpeg',
                    'Cache-Control': 'public, max-age=3600',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie',
                    'Access-Control-Allow-Credentials': 'true'
                }
            )
            
            return response
        
        except Exception as e:
            _logger.error(f"Photo download error: {str(e)}")
            return self._error_response("Failed to download photo", 500)
    
    def _json_response(self, data=None, success=True, message="", status=200):
        """Standard JSON response format"""
        from datetime import datetime
        response_data = {
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        response = request.make_response(
            json.dumps(response_data, default=str),
            headers={
                'Content-Type': 'application/json',
                **self._cors_headers()
            }
        )
        response.status_code = status
        return response
    
    def _error_response(self, message, status=400):
        """Standard error response format"""
        return self._json_response(data=None, success=False, message=message, status=status)

    def _get_user_from_session(self):
        """Get authenticated user from session token"""
        from .session_manager import session_manager
        
        try:
            # Get session token from Authorization header
            auth_header = request.httprequest.headers.get('Authorization', '')
            _logger.info(f"Auth header received: {auth_header[:50]}...")
            
            if not auth_header.startswith('Bearer '):
                _logger.warning("No Bearer token found in Authorization header")
                return None
            
            session_token = auth_header.replace('Bearer ', '')
            _logger.info(f"Employee request with Bearer token: {session_token[:10]}...")
            
            # Get user ID from session manager
            uid = session_manager.get_user_id(session_token)
            _logger.info(f"Session manager returned user ID: {uid}")
            
            if not uid:
                _logger.warning("Session token not found in session manager")
                available_sessions = []
                try:
                    # Debug: show available sessions (first 5 chars only for security)
                    available_sessions = [token[:5] + '...' for token in session_manager._sessions.keys()]
                except:
                    pass
                _logger.warning(f"Available sessions: {available_sessions}")
                return None
            
            # Get user record
            user = request.env['res.users'].sudo().browse(uid)
            if user.exists():
                _logger.info(f"Found user: {user.login} (ID: {user.id})")
                return user
            else:
                _logger.warning(f"User with ID {uid} not found in database")
                return None
                
        except Exception as e:
            _logger.error(f"Error in _get_user_from_session: {str(e)}")
            return None
