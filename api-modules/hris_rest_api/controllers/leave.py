import json
import logging
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class LeaveController(http.Controller):
    
    def _cors_headers(self):
        """Return CORS headers for API responses"""
        return {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
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
    
    @http.route('/api/leaves', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_leaves(self):
        """Get leave requests"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get query parameters
            limit = int(request.httprequest.args.get('limit', 20))
            offset = int(request.httprequest.args.get('offset', 0))
            employee_id = request.httprequest.args.get('employee_id')
            status = request.httprequest.args.get('status')
            date_from = request.httprequest.args.get('date_from')
            date_to = request.httprequest.args.get('date_to')
            
            # Build domain
            domain = []
            if employee_id:
                domain.append(('employee_id', '=', int(employee_id)))
            if status:
                domain.append(('state', '=', status))
            if date_from:
                domain.append(('request_date_from', '>=', date_from))
            if date_to:
                domain.append(('request_date_to', '<=', date_to))
            
            # Get leave requests
            leaves = request.env['hr.leave'].search(domain, limit=limit, offset=offset, order='create_date desc')
            total_count = request.env['hr.leave'].search_count(domain)
            
            leave_data = []
            for leave in leaves:
                leave_data.append({
                    'id': leave.id,
                    'employee_name': leave.employee_id.name,
                    'employee_id': leave.employee_id.id,
                    'leave_type': leave.holiday_status_id.name,
                    'leave_type_id': leave.holiday_status_id.id,
                    'request_date_from': leave.request_date_from.strftime('%Y-%m-%d') if leave.request_date_from else None,
                    'request_date_to': leave.request_date_to.strftime('%Y-%m-%d') if leave.request_date_to else None,
                    'number_of_days': leave.number_of_days,
                    'state': leave.state,
                    'state_label': dict(leave._fields['state'].selection).get(leave.state),
                    'name': leave.name,
                    'notes': leave.notes,
                    'create_date': leave.create_date.strftime('%Y-%m-%d %H:%M:%S') if leave.create_date else None,
                    'can_approve': leave.can_approve,
                    'can_cancel': leave.can_cancel,
                })
            
            return self._json_response(
                data={
                    'leaves': leave_data,
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                },
                message="Leave requests retrieved successfully"
            )
            
        except Exception as e:
            _logger.error(f"Leave list error: {str(e)}")
            return self._error_response("Failed to retrieve leave requests", 500)
    
    @http.route('/api/leaves', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_leave(self):
        """Create new leave request"""
        # Handle preflight CORS request
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            # Get session token from Authorization header
            auth_header = request.httprequest.headers.get('Authorization', '')
            _logger.info(f"DEBUG LEAVE API - Auth header: {auth_header}")
            
            if not auth_header.startswith('Bearer '):
                _logger.error("DEBUG LEAVE API - No Bearer token found")
                return self._error_response("Silakan login terlebih dahulu untuk mengajukan cuti.", 401)
            
            session_token = auth_header.replace('Bearer ', '')
            _logger.info(f"DEBUG LEAVE API - Session token: {session_token}")
            
            # Validate session token
            from .session_manager import session_manager
            uid = session_manager.get_user_id(session_token)
            _logger.info(f"DEBUG LEAVE API - User ID from session: {uid}")
            
            if not uid:
                _logger.error("DEBUG LEAVE API - Invalid session token")
                return self._error_response("Sesi login Anda telah berakhir. Silakan login kembali.", 401)
            
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                _logger.error(f"DEBUG LEAVE API - User {uid} not found")
                return self._error_response("User not found", 404)
            
            _logger.info(f"DEBUG LEAVE API - User found: {user.name}")
            
            # Get employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not employee:
                _logger.error(f"DEBUG LEAVE API - Employee record not found for user {user.name}")
                return self._error_response("Profil karyawan tidak ditemukan. Silakan hubungi bagian HR untuk melengkapi profil Anda.", 404)
            
            _logger.info(f"DEBUG LEAVE API - Employee found: {employee.name}")
            
            # Get request data
            data = json.loads(request.httprequest.data.decode('utf-8'))
            _logger.info(f"DEBUG LEAVE API - Request data: {data}")
            
            # Auto-create allocation if not exists
            holiday_status_id = data.get('holiday_status_id')
            if holiday_status_id:
                existing_allocation = request.env['hr.leave.allocation'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', holiday_status_id),
                    ('state', '=', 'validate')
                ], limit=1)
                
                if not existing_allocation:
                    _logger.info(f"DEBUG LEAVE API - No allocation found, creating auto allocation")
                    # Create allocation
                    allocation_vals = {
                        'name': f'Auto Allocation - {employee.name}',
                        'employee_id': employee.id,
                        'holiday_status_id': holiday_status_id,
                        'number_of_days': 30,  # Default 30 days
                        'allocation_type': 'regular',
                    }
                    allocation = request.env['hr.leave.allocation'].sudo().create(allocation_vals)
                    _logger.info(f"DEBUG LEAVE API - Auto allocation created: {allocation.id}")
                    
                    # Simple direct state update for allocation
                    try:
                        allocation.sudo().write({'state': 'validate'})
                        _logger.info(f"DEBUG LEAVE API - Auto allocation validated: {allocation.id}")
                    except Exception as validate_error:
                        _logger.error(f"DEBUG LEAVE API - Allocation validation error: {str(validate_error)}")
            
            required_fields = ['holiday_status_id', 'request_date_from', 'request_date_to']
            for field in required_fields:
                if field not in data:
                    return self._error_response(f"Field '{field}' is required", 400)
            
            # Validate dates
            try:
                date_from = datetime.strptime(data['request_date_from'], '%Y-%m-%d').date()
                date_to = datetime.strptime(data['request_date_to'], '%Y-%m-%d').date()
                
                if date_from > date_to:
                    return self._error_response("Tanggal mulai tidak boleh lebih besar dari tanggal selesai. Silakan periksa kembali tanggal yang dipilih.", 400)
                    
            except ValueError:
                return self._error_response("Format tanggal tidak valid. Silakan gunakan format YYYY-MM-DD (contoh: 2025-07-26).", 400)
            
            # Create leave request
            leave_vals = {
                'employee_id': employee.id,
                'holiday_status_id': data['holiday_status_id'],
                'request_date_from': date_from,
                'request_date_to': date_to,
                'name': data.get('name', ''),
                'notes': data.get('notes', ''),
            }
            
            _logger.info(f"DEBUG LEAVE API - Leave values: {leave_vals}")
            
            # Create leave request using the authenticated user
            leave = request.env['hr.leave'].with_user(user).create(leave_vals)
            
            # Just create without submission - simple approach
            _logger.info(f"DEBUG LEAVE API - Leave created successfully: ID {leave.id}, State: {leave.state}")
            
            return self._json_response(
                data={
                    'id': leave.id,
                    'employee_name': leave.employee_id.name,
                    'leave_type': leave.holiday_status_id.name,
                    'request_date_from': leave.request_date_from.strftime('%Y-%m-%d'),
                    'request_date_to': leave.request_date_to.strftime('%Y-%m-%d'),
                    'number_of_days': leave.number_of_days,
                    'state': leave.state,
                },
                message="Leave request created successfully"
            )
            
        except json.JSONDecodeError:
            _logger.error("DEBUG LEAVE API - Invalid JSON data received")
            return self._error_response("Format data tidak valid. Silakan periksa kembali data yang dikirim.", 400)
        except Exception as e:
            error_str = str(e).lower()
            _logger.error(f"Create leave error: {str(e)}")
            
            # Provide more specific error messages based on error type
            if 'resource.calendar' in error_str or 'calendar' in error_str:
                return self._error_response("Jadwal kerja Anda belum diatur dalam sistem. Silakan hubungi bagian HR untuk pengaturan jadwal kerja.", 500)
            elif 'rpc_error' in error_str or 'server configuration' in error_str:
                return self._error_response("Sistem sedang mengalami gangguan. Silakan coba lagi dalam beberapa saat atau hubungi administrator.", 500)
            elif 'allocation' in error_str or 'insufficient' in error_str:
                return self._error_response("Saldo cuti Anda tidak mencukupi untuk periode yang dipilih. Silakan periksa sisa cuti Anda.", 400)
            elif 'duplicate' in error_str or 'already exists' in error_str or 'overlapping' in error_str:
                return self._error_response("Permohonan cuti untuk periode tersebut sudah ada sebelumnya. Silakan periksa riwayat cuti Anda atau pilih tanggal yang berbeda.", 400)
            elif 'date' in error_str:
                return self._error_response("Format tanggal atau rentang tanggal tidak valid. Silakan periksa kembali tanggal yang dipilih.", 400)
            elif 'employee' in error_str and 'not found' in error_str:
                return self._error_response("Data karyawan tidak ditemukan. Silakan hubungi administrator.", 404)
            elif 'permission' in error_str or 'access' in error_str:
                return self._error_response("Anda tidak memiliki izin untuk melakukan tindakan ini.", 403)
            else:
                # For any other error, suggest that the leave might already exist
                return self._error_response("Permohonan cuti mungkin sudah berhasil dibuat sebelumnya atau terjadi kesalahan pada sistem. Silakan periksa riwayat cuti Anda untuk memastikan.", 500)
    
    @http.route('/api/leaves/<int:leave_id>/approve', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False)
    def approve_leave(self, leave_id):
        """Approve leave request"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            leave = request.env['hr.leave'].browse(leave_id)
            
            if not leave.exists():
                return self._error_response("Leave request not found", 404)
            
            if not leave.can_approve:
                return self._error_response("You don't have permission to approve this leave", 403)
            
            leave.action_approve()
            
            return self._json_response(
                data={'id': leave.id, 'state': leave.state},
                message="Leave request approved successfully"
            )
            
        except Exception as e:
            _logger.error(f"Approve leave error: {str(e)}")
            return self._error_response("Failed to approve leave request", 500)
    
    @http.route('/api/leave-types', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_leave_types(self):
        """Get available leave types"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Use sudo() to bypass access rights for public endpoint
            leave_types = request.env['hr.leave.type'].sudo().search([])
            
            leave_type_data = []
            for leave_type in leave_types:
                leave_type_data.append({
                    'id': leave_type.id,
                    'name': leave_type.name,
                })
            
            return self._json_response(
                data=leave_type_data,
                message="Leave types retrieved successfully"
            )
            
        except Exception as e:
            _logger.error(f"Leave types error: {str(e)}")
            return self._error_response("Failed to retrieve leave types", 500)
    
    @http.route('/api/leave-balance/<int:employee_id>', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False)
    def get_leave_balance(self, employee_id):
        """Get employee leave balance"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return self._error_response("Employee not found", 404)
            
            # Get leave allocations
            allocations = request.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee_id),
                ('state', '=', 'validate')
            ])
            
            balance_data = []
            for allocation in allocations:
                balance_data.append({
                    'leave_type': allocation.holiday_status_id.name,
                    'leave_type_id': allocation.holiday_status_id.id,
                    'allocated_days': allocation.number_of_days,
                    'remaining_days': allocation.number_of_days - allocation.leaves_taken,
                    'used_days': allocation.leaves_taken,
                })
            
            return self._json_response(
                data=balance_data,
                message="Leave balance retrieved successfully"
            )
            
        except Exception as e:
            _logger.error(f"Leave balance error: {str(e)}")
            return self._error_response("Failed to retrieve leave balance", 500)
    
    @http.route('/api/leave/history', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_leave_history(self):
        """Get leave history for current user"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session
            from .session_manager import session_manager
            auth_header = request.httprequest.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return self._error_response("Session token required", 401)
            
            session_token = auth_header.replace('Bearer ', '')
            uid = session_manager.get_user_id(session_token)
            
            if not uid:
                return self._error_response("Invalid session", 401)
            
            user = request.env['res.users'].sudo().browse(uid)
            if not user.exists():
                return self._error_response("User not found", 404)
            
            # Get employee
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not employee:
                return self._error_response("Employee record not found", 404)
            
            # Get leave history
            leaves = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id)
            ], order='create_date desc', limit=50)
            
            leave_data = []
            for leave in leaves:
                leave_data.append({
                    'id': leave.id,
                    'type': leave.holiday_status_id.name if leave.holiday_status_id else 'Unknown',
                    'start_date': leave.request_date_from.strftime('%Y-%m-%d') if leave.request_date_from else 'Unknown',
                    'end_date': leave.request_date_to.strftime('%Y-%m-%d') if leave.request_date_to else 'Unknown',
                    'days': leave.number_of_days or 0,
                    'status': dict(leave._fields['state'].selection).get(leave.state, 'Unknown') if hasattr(leave._fields.get('state'), 'selection') else leave.state,
                    'reason': leave.name or 'No reason provided',
                    'applied_date': leave.create_date.strftime('%Y-%m-%d') if leave.create_date else 'Unknown',
                })
            
            return self._json_response(
                data=leave_data,
                message=f"Leave history retrieved successfully. Found {len(leave_data)} records."
            )
            
        except Exception as e:
            _logger.error(f"Get leave history error: {str(e)}")
            return self._error_response("Failed to retrieve leave history", 500)
    
    @http.route('/api/leaves/test', type='http', auth='none', methods=['GET', 'POST', 'OPTIONS'], csrf=False)
    def test_leaves_endpoint(self):
        """Test endpoint untuk debugging"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            method = request.httprequest.method
            return self._json_response(
                data={
                    'method': method,
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Leave API endpoint is working!'
                },
                message=f"Test endpoint success with {method} method"
            )
        except Exception as e:
            _logger.error(f"Test endpoint error: {str(e)}")
            return self._error_response(f"Test endpoint failed: {str(e)}", 500)

    @http.route('/api/sessions/debug', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def debug_sessions(self):
        """Debug endpoint untuk melihat session yang aktif"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            from .session_manager import session_manager
            
            # Get auth header
            auth_header = request.httprequest.headers.get('Authorization', '')
            session_token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
            
            debug_info = {
                'requested_token': session_token,
                'total_active_sessions': len(session_manager._sessions),
                'session_exists': session_token in session_manager._sessions,
                'session_valid': bool(session_manager.get_user_id(session_token)) if session_token else False,
                'active_sessions': list(session_manager._sessions.keys())[:3],  # Only show first 3 for security
            }
            
            return self._json_response(
                data=debug_info,
                message="Session debug info retrieved"
            )
        except Exception as e:
            _logger.error(f"Debug sessions error: {str(e)}")
            return self._error_response(f"Debug failed: {str(e)}", 500)

