from .base_controller import BaseController
from odoo import http
from odoo.http import request
import logging

class ElearningCourseController(BaseController):

    @http.route('/api/elearning/slide_ids', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_slide_ids(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ]
            return request.make_response('', headers=headers)
        try:
            slides = request.env['slide.slide'].sudo().search([])
            data = [{'id': s.id, 'title': s.name} for s in slides]
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ]
            return self._json_response(data=data, message='Slide IDs loaded', headers=headers)
        except Exception as e:
            return self._error_response(f'Failed to load slide IDs: {str(e)}', status=500)

    def _error_response(self, message, status=400, headers=None):
        # Pastikan header CORS selalu ada
        cors_headers = [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
        ]
        if headers:
            cors_headers.extend(headers)
        response = request.make_response(
            self._json_response(data=None, message=message, status=status).data,
            headers=cors_headers
        )
        response.status_code = status
        return response

    @http.route('/api/elearning/slide/<int:slide_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_slide_detail(self, slide_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ]
            return request.make_response('', headers=headers)
        try:
            _logger = logging.getLogger(__name__)
            _logger.info(f"[DEBUG] Mencari slide dengan ID: {slide_id}")
            slide = request.env['slide.slide'].sudo().browse(slide_id)
            _logger.info(f"[DEBUG] Hasil browse: slide.id={slide.id}, exists={slide.exists()}")
            if not slide.exists():
                _logger.info(f"[DEBUG] Slide ID {slide_id} tidak ditemukan!")
                return self._error_response('Slide not found', status=404)
            base_url = request.httprequest.host_url.rstrip('/')
            pdf_url = ''
            video_url = ''
            print(f"[DEBUG] slide.slide_type: {slide.slide_type}")
            _logger.info(f"[DEBUG] slide.slide_type: {slide.slide_type}")
            # Cek PDF di field document_binary_content
            if slide.slide_type in ['document', 'pdf'] and getattr(slide, 'document_binary_content', False):
                filename = getattr(slide, 'file_name', None) or getattr(slide, 'name', None) or 'document.pdf'
                pdf_url = f"{base_url}/web/content/slide.slide/{slide.id}/document_binary_content/{filename}?download=true"
            # Fallback ke resource lama jika tidak ada
            elif slide.slide_type in ['document', 'pdf'] and slide.slide_resource_ids:
                resource = slide.slide_resource_ids[0]
                print(f"[DEBUG] Resource: id={resource.id}, name={getattr(resource, 'name', None)}, file_name={getattr(resource, 'file_name', None)}, data_exists={bool(getattr(resource, 'data', False))}")
                _logger.info(f"[DEBUG] Resource: id={resource.id}, name={getattr(resource, 'name', None)}, file_name={getattr(resource, 'file_name', None)}, data_exists={bool(getattr(resource, 'data', False))}")
                if getattr(resource, 'data', False):
                    filename = getattr(resource, 'file_name', None) or getattr(resource, 'name', None) or 'document.pdf'
                    pdf_url = f"{base_url}/web/content/{resource._name}/{resource.id}/data/{filename}?download=true"
            # Video
            if 'video' in (slide.slide_type or ''):
                print(f"[DEBUG] slide.video_url: {getattr(slide, 'video_url', None)}")
                _logger.info(f"[DEBUG] slide.video_url: {getattr(slide, 'video_url', None)}")
                if getattr(slide, 'video_url', False):
                    video_url = slide.video_url
            # Ubah type 'document' menjadi 'pdf' agar konsisten dengan frontend
            slide_type = slide.slide_type
            if slide_type == 'document':
                slide_type = 'pdf'
            data = {
                'id': slide.id,
                'title': slide.name,
                'type': slide_type,
                'pdf_url': pdf_url,
                'video_url': video_url,
                'content': slide.description or '',
            }
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ]
            response = request.make_response(self._json_response(data=data, message='Slide loaded').data, headers=headers)
            return response
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR] Failed to load slide: {e}\n{tb}")
            _logger = logging.getLogger(__name__)
            _logger.error(f"[ERROR] Failed to load slide: {e}\n{tb}")
            return self._error_response(f'Failed to load slide: {str(e)}', status=500)
    @http.route('/api/elearning/course/<int:course_id>/slides', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_course_slides(self, course_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        try:
            course = request.env['slide.channel'].sudo().browse(course_id)
            if not course.exists():
                return self._error_response('Course not found', status=404)
            slides = []
            base_url = request.httprequest.host_url.rstrip('/')
            for slide in course.slide_ids:
                pdf_url = ''
                video_url = ''
                # Debug: print semua field pada slide document
                slide_type = slide.slide_type
                if slide.slide_type == 'document':
                    slide_type = 'pdf'
                    # Cek PDF di field document_binary_content
                    if getattr(slide, 'document_binary_content', False):
                        filename = getattr(slide, 'file_name', None) or getattr(slide, 'name', None) or 'document.pdf'
                        pdf_url = f"{base_url}/web/content/slide.slide/{slide.id}/document_binary_content/{filename}?download=true"
                    # Fallback ke resource lama jika tidak ada
                    elif slide.slide_resource_ids:
                        resource = slide.slide_resource_ids[0]
                        if getattr(resource, 'data', False):
                            filename = getattr(resource, 'file_name', None) or getattr(resource, 'name', None) or 'document.pdf'
                            pdf_url = f"{base_url}/web/content/{resource._name}/{resource.id}/data/{filename}?download=true"
                if slide.slide_type == 'video':
                    if getattr(slide, 'video_url', False):
                        video_url = slide.video_url
                    elif hasattr(slide, 'idi') and getattr(slide, 'idi', False):
                        video_url = slide.idi
                slides.append({
                    'id': slide.id,
                    'title': slide.name,
                    'type': slide_type,
                    'pdf_url': pdf_url,
                    'video_url': video_url,
                })
            return self._json_response(data=slides, message='Slides loaded')
        except Exception as e:
            return self._error_response(f'Failed to load slides: {str(e)}', status=500)