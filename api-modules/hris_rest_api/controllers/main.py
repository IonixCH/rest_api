import json
from odoo import http
from odoo.http import request
from .base_controller import BaseController

class HRISRestAPI(BaseController):
    
    @http.route('/api/health', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def health_check(self):
        """Health check endpoint for connection testing"""
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
            
        response_data = {
            'server': 'Odoo HRIS',
            'version': '1.0.0',
            'timestamp': str(request.env.cr.now())
        }
        
        return self._json_response(
            data=response_data,
            message='HRIS REST API is running'
        )

