import json
from odoo import http
from odoo.http import request, Response

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    return response

class ElearningApiController(http.Controller):
    @http.route('/api/elearning/courses', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def get_courses(self, **kwargs):
        # Always handle OPTIONS for CORS preflight
        if request.httprequest.method == 'OPTIONS':
            response = Response(status=200)
            return add_cors_headers(response)
        try:
            courses = request.env['slide.channel'].sudo().search([])
            data = []
            for course in courses:
                slides = []
                for slide in course.slide_ids:
                    slide_type = (slide.slide_type or '').lower()
                    if slide_type in ['video', 'document', 'quiz']:
                        mapped_type = slide_type
                    elif slide_type in ['infographic', 'presentation', 'webpage']:
                        mapped_type = 'document'
                    else:
                        mapped_type = 'document'
                    content = slide.html_content or ''
                    slides.append({
                        'id': slide.id,
                        'title': slide.name,
                        'type': mapped_type,
                        'content': content or 'No content available',
                        'video_url': slide.video_url or '',
                        'url': slide.url or '',           # gunakan ini untuk link eksternal
                    })
                data.append({
                    'id': course.id,
                    'name': course.name,
                    'description': course.description,
                    'image_url': course.image_1920 and '/web/image/slide.channel/%s/image_1920' % course.id or '',
                    'total_slides': len(course.slide_ids),
                    'slides': slides,
                })
            response = Response(
                response=json.dumps({
                    'success': True,
                    'message': 'Courses fetched successfully',
                    'data': data,
                }),
                status=200,
                mimetype='application/json'
            )
            return add_cors_headers(response)
        except Exception as e:
            response = Response(
                response=json.dumps({
                    'success': False,
                    'message': 'Error: %s' % str(e),
                    'data': [],
                }),
                status=500,
                mimetype='application/json'
            )
            return add_cors_headers(response)