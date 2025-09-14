
from odoo import http
from odoo.http import request

class ElearningApiController(http.Controller):
    @http.route('/api/elearning/courses', type='json', auth='public', methods=['POST'], csrf=False)
    def get_courses(self, **kwargs):
        try:
            courses = request.env['slide.channel'].sudo().search([])
            data = []
            for course in courses:
                data.append({
                    'id': course.id,
                    'name': course.name,
                    'description': course.description,
                    'category': course.category,
                    'image_url': course.image_1920 and '/web/image/slide.channel/%s/image_1920' % course.id or '',
                    'website_url': course.website_url,
                    'total_slides': len(course.slide_ids),
                    # Tambahkan field lain sesuai kebutuhan
                })
            return {
                'success': True,
                'message': 'Courses fetched successfully',
                'data': data,
            }
        except Exception as e:
            return {
                'success': False,
                'message': 'Error: %s' % str(e),
                'data': [],
            }
