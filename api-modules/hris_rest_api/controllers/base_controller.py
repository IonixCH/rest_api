import json
from datetime import datetime
from odoo import http
from odoo.http import request

class BaseController(http.Controller):
    """Base controller with common CORS and response methods"""
    
    def _cors_headers(self):
        """Return CORS headers for API responses with support for dynamic origins"""
        origin = request.httprequest.headers.get('Origin', '*')
        
        # For development, allow common localhost and ngrok patterns
        return {
            'Access-Control-Allow-Origin': origin if origin != 'null' else '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400',
        }

    def _json_response(self, data=None, success=True, message="", status=200):
        """Standard JSON response format with CORS headers"""
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
        """Standard error response with CORS headers"""
        return self._json_response(
            data=None,
            success=False,
            message=message,
            status=status
        )
        
    def _handle_options(self):
        """Handle OPTIONS requests for CORS preflight"""
        return request.make_response('', headers=self._cors_headers())
