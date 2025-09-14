import json
import logging
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class ResignationController(http.Controller):

    def _cors_headers(self):
        """Return CORS headers for API responses"""
        return {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400',
        }

    def _json_response(self, data=None, success=True, message="", status=200):
        """Standard JSON response format"""
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
        """Standard error response"""
        return self._json_response(
            data=None,
            success=False,
            message=message,
            status=status
        )

    @http.route('/api/departments', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_departments(self):
        """Get department list for dropdown"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())

        try:
            departments = request.env['hr.department'].sudo().search([])
            result = [{'id': d.id, 'name': d.name} for d in departments]
            return self._json_response(
                data=result,
                message="Departments retrieved successfully"
            )
        except Exception as e:
            _logger.error(f"Get departments error: {str(e)}")
            return self._error_response("Failed to retrieve departments", 500)

    @http.route('/api/resignation', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_resignation(self):
        """Create resignation request"""
        # Handle preflight CORS
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())

        try:
            # --- Ambil session token dari Authorization header ---
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return self._error_response("Session token required", 401)
            session_token = auth_header.replace('Bearer ', '')

            # --- Validasi session token ---
            from .session_manager import session_manager
            uid = session_manager.get_user_id(session_token)
            if not uid:
                return self._error_response("Invalid or expired session", 401)

            user = request.env['res.users'].sudo().browse(uid)
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not employee:
                return self._error_response("Employee not found", 404)

            data = json.loads(request.httprequest.data.decode('utf-8'))
            vals = {
                'employee_id': employee.id,
                'department_id': employee.department_id.id if employee.department_id else False,
                'expected_revealing_date': data.get('resign_date'),
                'reason': data.get('reason'),
                'joined_date': employee.joining_date,  # <-- tambahkan ini!
            }
            resignation = request.env['hr.resignation'].with_user(user).create(vals)
            return self._json_response(
                data={'id': resignation.id},
                message="Resignation request created successfully"
            )
        except Exception as e:
            _logger.error(f"Create resignation error: {str(e)}")
            return self._error_response("Failed to create resignation", 500)