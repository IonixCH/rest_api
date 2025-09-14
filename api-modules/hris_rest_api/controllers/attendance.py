import json
import logging
from datetime import datetime, date, timedelta, time
import pytz
from odoo import http # type: ignore
from odoo.http import request # type: ignore
import calendar
from geopy.distance import geodesic

_logger = logging.getLogger(__name__)

class AttendanceController(http.Controller):
    
    def _format_time_local(self, dt):
        """Format datetime to local timezone (WIB/Indonesia)"""
        if not dt:
            return ''
        
        # Convert to Indonesia timezone (WIB = UTC+7)
        indonesia_tz = pytz.timezone('Asia/Jakarta')
        
        # If dt is naive (no timezone), assume it's stored in UTC and convert to WIB
        if dt.tzinfo is None:
            # Assume stored time is in UTC, convert to WIB
            utc_dt = pytz.utc.localize(dt)
            local_dt = utc_dt.astimezone(indonesia_tz)
        else:
            local_dt = dt.astimezone(indonesia_tz)
        
        # Format as HH:MM AM/PM
        formatted_time = local_dt.strftime('%I:%M %p')
        _logger.info(f"[TIME FORMAT] Input: {dt} -> UTC assumed -> WIB: {local_dt} -> Formatted: {formatted_time}")
        return formatted_time
    
    def _get_current_datetime_local(self):
        """Get current datetime in local timezone"""
        indonesia_tz = pytz.timezone('Asia/Jakarta')
        return datetime.now(indonesia_tz)
    
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
    
    def _get_user_from_session(self):
        """Get user from session using simplified authentication"""
        try:
            # Check Authorization header first
            auth_header = request.httprequest.headers.get('Authorization', '')
            _logger.info(f"Auth header received: {auth_header[:50]}...")
            
            if auth_header.startswith('Bearer '):
                session_token = auth_header.replace('Bearer ', '')
                _logger.info(f"Attendance request with Bearer token: {session_token[:10]}...")
                
                # Use session manager for lookup
                from .session_manager import session_manager
                uid = session_manager.get_user_id(session_token)
                _logger.info(f"Session manager returned user ID: {uid}")
                
                if uid:
                    user = request.env['res.users'].sudo().browse(uid)
                    if user.exists():
                        _logger.info(f"Found user: {user.name} (ID: {user.id})")
                        return user
                    else:
                        _logger.warning(f"User ID {uid} not found in database")
                else:
                    _logger.warning(f"Session token not found in session manager")
                    # Debug: Print all sessions
                    _logger.warning(f"Available sessions: {list(session_manager._sessions.keys())}")
            else:
                _logger.warning("No valid Authorization header found")
                        
        except Exception as e:
            _logger.error(f"Session lookup error: {str(e)}")
            
        return None

    def _calculate_absent_days(self, employee, month, year):
        """Calculate absent days for an employee in a given month and year"""
        indonesia_tz = pytz.timezone('Asia/Jakarta')
        absent_days = 0
        total_days = calendar.monthrange(year, month)[1]
        for day in range(1, total_days + 1):
            date_obj = datetime(year, month, day, tzinfo=indonesia_tz)
            attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', date_obj.strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<=', date_obj.strftime('%Y-%m-%d 23:59:59')),
            ])
            # If no check-in at all until 5:00 PM
            if not attendances:
                now = datetime.now(indonesia_tz)
                if now.date() > date_obj.date() or (now.date() == date_obj.date() and now.time() >= time(17, 0)):
                    absent_days += 1
        return absent_days

    @http.route('/api/attendance/dashboard', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_dashboard_data(self):
        """Get attendance dashboard data for current user"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            # Get user from session
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get current date info
            today = datetime.now().date()
            current_month_start = today.replace(day=1)
            
            # Check if user has employee record
            employee = request.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            
            if not employee:
                # Create basic employee record if not exists
                company_id = user.company_id.id if hasattr(user, 'company_id') and getattr(user, 'company_id', False) and user.company_id else request.env.company.id
                if not company_id:
                    # Fallback: ambil company pertama yang aktif
                    company = request.env['res.company'].sudo().search([], limit=1)
                    company_id = company.id if company else 1
                employee = request.env['hr.employee'].sudo().create({
                    'name': user.name,
                    'user_id': user.id,
                    'work_email': user.email,
                    'company_id': company_id,
                })
            
            # Get today's attendance
            today_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<', (today + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00'))
            ], order='check_in desc', limit=1)
            
            # Calculate current status
            is_checked_in = bool(today_attendance and not today_attendance.check_out)
            check_in_time = self._format_time_local(today_attendance.check_in) if today_attendance and today_attendance.check_in else ''
            check_out_time = self._format_time_local(today_attendance.check_out) if today_attendance and today_attendance.check_out else ''
            
            # Calculate working hours
            working_hours = '00:00:00'
            if today_attendance and today_attendance.check_in:
                if today_attendance.check_out:
                    # Calculate actual working hours using UTC times (both stored in UTC)
                    check_in_utc = today_attendance.check_in
                    check_out_utc = today_attendance.check_out
                    
                    # Ensure both times are treated as UTC if they are naive
                    if check_in_utc.tzinfo is None:
                        check_in_utc = pytz.utc.localize(check_in_utc)
                    if check_out_utc.tzinfo is None:
                        check_out_utc = pytz.utc.localize(check_out_utc)
                    
                    # Calculate duration using UTC times (no timezone conversion needed for calculation)
                    duration = check_out_utc - check_in_utc
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    seconds = int(duration.total_seconds() % 60)
                    working_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # Debug logging for dashboard working hours
                    _logger.info(f"[DASHBOARD WORKING HOURS] Check-in UTC: {check_in_utc}, Check-out UTC: {check_out_utc}")
                    _logger.info(f"[DASHBOARD WORKING HOURS] Duration: {duration}, Working hours: {working_hours}")
                else:
                    # Calculate current working hours (still checked in)
                    check_in_utc = today_attendance.check_in
                    now = self._get_current_datetime_local()
                    
                    # Convert both times to the same timezone for accurate calculation
                    indonesia_tz = pytz.timezone('Asia/Jakarta')
                    
                    # Convert check_in from UTC to local timezone
                    if check_in_utc.tzinfo is None:
                        # If stored as naive datetime, treat as UTC
                        check_in_utc = pytz.utc.localize(check_in_utc)
                    check_in_local = check_in_utc.astimezone(indonesia_tz)
                    
                    # Calculate duration between local times
                    duration = now - check_in_local
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    seconds = int(duration.total_seconds() % 60)
                    working_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # Debug logging for working hours calculation while checked in
                    _logger.info(f"[DASHBOARD CURRENT WORKING HOURS] Check-in UTC: {check_in_utc}")
                    _logger.info(f"[DASHBOARD CURRENT WORKING HOURS] Check-in Local: {check_in_local}")
                    _logger.info(f"[DASHBOARD CURRENT WORKING HOURS] Now Local: {now}")
                    _logger.info(f"[DASHBOARD CURRENT WORKING HOURS] Duration: {duration}, Working hours: {working_hours}")
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    seconds = int(duration.total_seconds() % 60)
                    working_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Get monthly attendance summary
            monthly_attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', current_month_start.strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<', datetime.now().strftime('%Y-%m-%d 23:59:59'))
            ])
            
            # Calculate attendance statistics
            present_days = len(set(att.check_in.date() for att in monthly_attendances if att.check_in))
            
            # Calculate working days in current month - FIX: Only count days since employee creation
            # Get employee creation date
            employee_creation_date = employee.create_date.date() if employee.create_date else today
            
            # For new employees, start counting from their creation date, not from start of month
            start_counting_date = max(current_month_start, employee_creation_date)
            
            # Only count working days from creation date to today (or end of month)
            working_days = 0
            current_date = start_counting_date
            while current_date <= today:
                if current_date.weekday() < 5:  # Monday to Friday (0-4)
                    working_days += 1
                current_date += timedelta(days=1)
            
            # For new employees with no attendance history, absent days should be 0 initially
            if present_days == 0 and employee_creation_date >= today:
                # Employee created today or in the future - no absences yet
                absent_days = 0
            else:
                absent_days = max(0, working_days - present_days)
                
            # Debug logging
            _logger.info(f"Employee {employee.name} attendance calculation:")
            _logger.info(f"  - Creation date: {employee_creation_date}")
            _logger.info(f"  - Start counting from: {start_counting_date}")
            _logger.info(f"  - Working days: {working_days}")
            _logger.info(f"  - Present days: {present_days}")
            _logger.info(f"  - Absent days: {absent_days}")
            
            # Calculate late arrivals (assuming 10:30 AM is standard time)
            late_days = 0
            standard_time = time(10, 30)  # 10:30 AM
            indonesia_tz = pytz.timezone('Asia/Jakarta')
            for attendance in monthly_attendances:
                if attendance.check_in:
                    # Konversi ke WIB sebelum cek jam
                    check_in = attendance.check_in
                    if check_in.tzinfo is None:
                        check_in = pytz.utc.localize(check_in).astimezone(indonesia_tz)
                    else:
                        check_in = check_in.astimezone(indonesia_tz)
                    if check_in.time() > standard_time:
                        late_days += 1
            
            dashboard_data = {
                'user_info': {
                    'name': user.name,
                    'location': 'Office Location'  # This could be fetched from employee record
                },
                'current_status': {
                    'is_checked_in': is_checked_in,
                    'check_in_time': check_in_time,
                    'check_out_time': check_out_time,
                    'working_hours': working_hours
                },
                'monthly_summary': {
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'late_days': late_days,
                    'working_days': working_days
                }
            }
            
            return self._json_response(dashboard_data, message="Dashboard data retrieved successfully")
            
        except Exception as e:
            _logger.error(f"Error getting dashboard data: {str(e)}")
            return self._error_response(f"Error retrieving dashboard data: {str(e)}", 500)

    @http.route('/api/attendance/toggle', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def toggle_checkin_checkout(self):
        """Toggle check-in/check-out for current user with GPS and camera validation"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            # Get user from session
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get request data for GPS and other info
            try:
                data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            except json.JSONDecodeError:
                data = {}
            
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            location = data.get('location', 'Unknown Location')
            notes = data.get('notes', '')
            camera_image = data.get('camera_image')  # Base64 image from camera
            
            # Validate GPS coordinates are provided
            if not latitude or not longitude:
                return self._error_response("GPS coordinates are required for attendance", 400)
            
            # Validate camera image is provided
            if not camera_image:
                return self._error_response("Camera photo is required for attendance", 400)
            
            # Get employee record
            employee = request.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            
            if not employee:
                # Auto-create employee if needed
                company = request.env.company
                employee = request.env['hr.employee'].sudo().create({
                    'name': user.name,
                    'work_email': user.email,
                    'user_id': user.id,
                    'company_id': company.id,
                })
                _logger.info(f"Auto-created employee: {employee.id} for user {user.name}")
            
            # Validate GPS radius
            company = employee.company_id or request.env.company
            
            # Safe access to latitude/longitude with fallback
            try:
                office_lat = getattr(company, 'latitude', None) or -6.969182
                office_lon = getattr(company, 'longitude', None) or 107.629251
                
                # If no coordinates set, try to set default
                if not office_lat or not office_lon:
                    try:
                        company.sudo().write({
                            'latitude': -6.969182,
                            'longitude': 107.629251
                        })
                        office_lat = -6.969182
                        office_lon = 107.629251
                        _logger.info(f"[TOGGLE] Set default coordinates for company {company.name}")
                    except Exception as set_err:
                        _logger.error(f"[TOGGLE] Failed to set default coordinates: {set_err}")
                        
            except AttributeError:
                # Fallback if fields don't exist
                office_lat = -6.969182
                office_lon = 107.629251
                _logger.warning(f"[TOGGLE] Company latitude/longitude fields not found, using default coordinates")
            
            _logger.info(f"[TOGGLE] GPS Check - office: ({office_lat}, {office_lon}), user: ({latitude}, {longitude})")
            
            try:
                user_lat_f = float(latitude)
                user_lon_f = float(longitude)
                office_lat_f = float(office_lat)
                office_lon_f = float(office_lon)
                distance = geodesic((user_lat_f, user_lon_f), (office_lat_f, office_lon_f)).meters
                within_radius = self._is_within_radius(latitude, longitude, office_lat, office_lon, 100000)
                
                _logger.info(f"[TOGGLE] Distance: {distance} meter, Within radius: {within_radius}")
                
                if not within_radius:
                    return self._error_response(f"Anda di luar area kantor. Jarak: {distance/1000:.2f} km dari kantor (max: 2.0 km)", 400)
                    
            except Exception as e:
                _logger.error(f"[TOGGLE] Error calculating distance: {e}")
                return self._error_response("Error validating location", 500)
            
            # Check attendance for today - enforce one check-in/check-out cycle per day
            today = datetime.now().date()
            today_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<', (today + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00'))
            ], limit=1)
            
            if today_attendance:
                # Already has attendance record for today
                if not today_attendance.check_out:
                    # Has check-in but no check-out, so do check-out
                    try:
                        check_out_time = self._get_current_datetime_local()
                        # Convert WIB to UTC for storage
                        check_out_utc = check_out_time.astimezone(pytz.UTC).replace(tzinfo=None)
                        
                        # Simple direct SQL update to avoid ORM constraints
                        _logger.info(f"Updating checkout for attendance ID: {today_attendance.id}")
                        
                        # Calculate working hours using UTC times
                        check_in_utc = today_attendance.check_in
                        duration = check_out_utc - check_in_utc
                        hours = int(duration.total_seconds() // 3600)
                        minutes = int((duration.total_seconds() % 3600) // 60)
                        seconds = int(duration.total_seconds() % 60)
                        working_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        # Update both check_out and working_hours in single SQL query
                        request.env.cr.execute("""
                            UPDATE hr_attendance 
                            SET check_out = %s, working_hours = %s 
                            WHERE id = %s AND check_out IS NULL
                        """, (check_out_utc, working_hours, today_attendance.id))
                        
                        # Check if update was successful
                        if request.env.cr.rowcount == 0:
                            return self._error_response("Failed to update checkout", 500)
                        
                        # Commit the transaction
                        request.env.cr.commit()
                        _logger.info(f"Checkout committed successfully for attendance ID: {today_attendance.id}")
                        
                        # Debug logging for working hours calculation
                        _logger.info(f"[TOGGLE WORKING HOURS] Check-in UTC: {check_in_utc}")
                        _logger.info(f"[TOGGLE WORKING HOURS] Check-out UTC: {check_out_utc}")
                        _logger.info(f"[TOGGLE WORKING HOURS] Duration: {duration}")
                        _logger.info(f"[TOGGLE WORKING HOURS] Working hours: {working_hours}")
                        _logger.info(f"[TOGGLE WORKING HOURS] Working hours: {working_hours}")
                        
                        check_out_formatted = self._format_time_local(check_out_utc)
                        
                        # Log attendance with GPS and camera info
                        _logger.info(f"[TOGGLE CHECKOUT] Employee: {employee.name}, Location: {location}, GPS: ({latitude}, {longitude}), Distance: {distance/1000:.2f} km")
                        _logger.info(f"[TOGGLE CHECKOUT] WIB time: {check_out_time} -> UTC stored: {check_out_utc} -> formatted: {check_out_formatted}")
                        
                        return self._json_response({
                            'action': 'check_out',
                            'check_out_time': check_out_formatted,
                            'working_hours': working_hours,
                            'is_checked_in': False,
                            'location': location,
                            'distance_from_office': f"{distance/1000:.2f} km",
                            'message': f'Successfully checked out at {check_out_formatted}'
                        }, message="Check out successful")
                        
                    except Exception as checkout_error:
                        _logger.error(f"Error during checkout: {str(checkout_error)}")
                        # Rollback any failed transaction
                        try:
                            request.env.cr.rollback()
                        except:
                            pass
                        return self._error_response(f"Checkout failed: {str(checkout_error)}", 500)
                else:
                    # Already completed check-in and check-out for today
                    return self._error_response("Anda sudah melakukan check-in dan check-out hari ini. Tunggu sampai besok untuk attendance berikutnya.", 400)
            else:
                # No attendance record for today, so do check-in
                try:
                    check_in_time = self._get_current_datetime_local()
                    # Convert WIB to UTC for storage
                    check_in_utc = check_in_time.astimezone(pytz.UTC).replace(tzinfo=None)
                    
                    # Create new attendance record with UTC time
                    attendance = request.env['hr.attendance'].sudo().create({
                        'employee_id': employee.id,
                        'check_in': check_in_utc,
                        'selfie_photo': camera_image,  # base64 string dari frontend
                        'latitude': latitude,          # string dari frontend
                        'longitude': longitude,        # string dari frontend
                    })
                    
                    # Force commit the transaction
                    request.env.cr.commit()
                    
                    check_in_formatted = self._format_time_local(check_in_utc)
                    
                    # Log attendance with GPS and camera info
                    _logger.info(f"[TOGGLE CHECKIN] Employee: {employee.name}, Location: {location}, GPS: ({latitude}, {longitude}), Distance: {distance/1000:.2f} km")
                    _logger.info(f"[TOGGLE CHECKIN] WIB time: {check_in_time} -> UTC stored: {check_in_utc} -> formatted: {check_in_formatted}")
                    
                    return self._json_response({
                        'action': 'check_in',
                        'check_in_time': check_in_formatted,
                        'is_checked_in': True,
                        'location': location,
                        'distance_from_office': f"{distance/1000:.2f} km",
                        'message': f'Successfully checked in at {check_in_formatted}'
                    }, message="Check in successful")
                        
                except Exception as checkin_error:
                    _logger.error(f"Error during checkin: {str(checkin_error)}")
                    # Rollback any failed transaction
                    try:
                        request.env.cr.rollback()
                    except:
                        pass
                    return self._error_response(f"Checkin failed: {str(checkin_error)}", 500)
                
        except Exception as e:
            _logger.error(f"Error during toggle check-in/out: {str(e)}")
            # Rollback any failed transaction
            try:
                request.env.cr.rollback()
            except:
                pass
            return self._error_response(f"Error during check-in/out: {str(e)}", 500)

    def _is_within_radius(self, user_lat, user_lon, office_lat, office_lon, radius_m=10000):
        try:
            user_loc = (float(user_lat), float(user_lon))
            office_loc = (float(office_lat), float(office_lon))
            distance = geodesic(user_loc, office_loc).meters
            _logger.info(f"[RADIUS CHECK] user_loc={user_loc}, office_loc={office_loc}, distance={distance}, radius={radius_m}")
            return distance <= radius_m
        except Exception as e:
            _logger.error(f"Radius check error: {str(e)} | user_lat={user_lat}, user_lon={user_lon}, office_lat={office_lat}, office_lon={office_lon}")
            return False

    @http.route('/api/attendance/checkin', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def check_in(self):
        """Employee check-in"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session using our authentication method
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            

            # Get request data (tanpa employee_id)
            data = json.loads(request.httprequest.data.decode('utf-8'))
            location = data.get('location')
            notes = data.get('notes', '')
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            _logger.info(f"[CHECKIN] user={user.name}, lat={latitude}, lon={longitude}, location={location}, notes={notes}")

            # Pastikan hanya satu employee per user
            employees = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
            if len(employees) > 1:
                # Jika ada lebih dari satu, update user_id employee lain ke None
                for emp in employees[1:]:
                    emp.sudo().write({'user_id': False})
                employee = employees[0]
            elif len(employees) == 1:
                employee = employees[0]
            else:
                # Auto-create employee jika belum ada
                company = request.env.company
                employee = request.env['hr.employee'].sudo().create({
                    'name': user.name,
                    'work_email': user.email,
                    'user_id': user.id,
                    'company_id': company.id,
                })
                _logger.info(f"[CHECKIN] Auto-created employee: {employee.id} for user {user.name}")

            # Validasi radius dan hitung distance
            company = employee.company_id or request.env.company
            office_lat = company.latitude or -6.986682
            office_lon = company.longitude or 107.637303
            distance = 0.0
            within_radius = True
            
            _logger.info(f"[CHECKIN] office_lat={office_lat}, office_lon={office_lon}, user_lat={latitude}, user_lon={longitude}")
            
            try:
                user_lat_f = float(latitude)
                user_lon_f = float(longitude)
                office_lat_f = float(office_lat)
                office_lon_f = float(office_lon)
                distance = geodesic((user_lat_f, user_lon_f), (office_lat_f, office_lon_f)).meters
                within_radius = self._is_within_radius(latitude, longitude, office_lat, office_lon, 100000)
                
                _logger.info(f"[CHECKIN] DISTANCE: {distance} meter, RADIUS: 2000 meter, WITHIN_RADIUS: {within_radius}")
                
                if not within_radius:
                    _logger.warning(f"[CHECKIN] OUTSIDE RADIUS: user=({latitude},{longitude}), office=({office_lat},{office_lon})")
                    return self._error_response(f"Anda di luar area kantor. Jarak: {distance/1000:.2f} km dari kantor (max: 2.0 km)", 400)
                    
            except Exception as e:
                _logger.error(f"[CHECKIN] Error calculating distance: {e}")
                # Continue dengan asumsi dalam radius jika ada error

            # Check if already checked in today
            today = date.today()
            existing_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
                ('check_in', '>=', f'{today} 00:00:00'),
                ('check_in', '<=', f'{today} 23:59:59')
            ], limit=1)
            
            if existing_attendance:
                return self._error_response("Employee is already checked in today", 400)
            
            # Create check-in record using sudo() to bypass permissions
            # --- PATCH: Use WIB (Asia/Jakarta) then convert to UTC ---
            indonesia_tz = pytz.timezone('Asia/Jakarta')
            now_local = datetime.now(indonesia_tz)
            now_utc = now_local.astimezone(pytz.UTC).replace(tzinfo=None)
            attendance_vals = {
                'employee_id': employee.id,
                'check_in': now_utc,
                'selfie_photo': data.get('selfie_photo'),  # base64 string dari frontend
                'latitude': latitude,                      # string dari frontend
                'longitude': longitude,                    # string dari frontend
            }
            attendance = request.env['hr.attendance'].sudo().create(attendance_vals)
            
            # Log additional info yang tidak disimpan di database
            _logger.info(f"[CHECKIN] Additional info - Location: {location}, Lat: {latitude}, Lng: {longitude}, Notes: {notes}")
            
            return self._json_response(
                data={
                    'id': attendance.id,
                    'employee_name': attendance.employee_id.name,
                    'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude,
                    'notes': notes,
                    'distance_from_office': f"{distance:.2f} km" if 'distance' in locals() else "N/A",
                    'within_radius': within_radius if 'within_radius' in locals() else True,
                },
                message="Check-in successful"
            )
        except json.JSONDecodeError as e:
            return self._error_response(f"Invalid JSON data: {str(e)}", 400)
        except Exception as e:
            _logger.error(f"Check-in error: {str(e)}", exc_info=True)
            return self._error_response(f"Check-in failed: {str(e)}", 500)
    
    @http.route('/api/attendance/checkout', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def check_out(self):
        """Employee check-out"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session using our authentication method
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get request data
            data = json.loads(request.httprequest.data.decode('utf-8'))
            employee_id = data.get('employee_id')
            location = data.get('location')
            notes = data.get('notes', '')
            
            # Find employee
            employee = None
            if employee_id:
                employee = request.env['hr.employee'].sudo().browse(employee_id)
                if not employee.exists():
                    employee = None
            
            if not employee:
                employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            
            if not employee:
                return self._error_response("Employee not found", 404)
            
            # Find active check-in for today (broader search to handle timezone issues)
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            
            _logger.info(f"[CHECKOUT] Looking for employee {employee.id}, found attendance: {attendance.id if attendance else 'None'}")
            
            if not attendance:
                return self._error_response("No active check-in found for today", 400)
            
            # Update with check-out time using direct SQL to bypass ORM constraints
            try:
                # --- PATCH: Use WIB (Asia/Jakarta) then convert to UTC ---
                indonesia_tz = pytz.timezone('Asia/Jakarta')
                checkout_time_local = datetime.now(indonesia_tz)
                checkout_time_utc = checkout_time_local.astimezone(pytz.UTC).replace(tzinfo=None)
                
                # Calculate working hours
                check_in_utc = attendance.check_in
                duration = checkout_time_utc - check_in_utc
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                seconds = int(duration.total_seconds() % 60)
                working_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # Update both check_out and working_hours
                request.env.cr.execute(
                    "UPDATE hr_attendance SET check_out = %s, working_hours = %s WHERE id = %s",
                    (checkout_time_utc, working_hours, attendance.id)
                )
                request.env.cr.commit()
                
                # Build response data manually since we updated via SQL
                return self._json_response(
                    data={
                        'id': attendance.id,
                        'employee_name': employee.name,
                        'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                        'check_out': checkout_time_utc.strftime('%Y-%m-%d %H:%M:%S'),
                        'location': location,
                        'notes': notes,
                    },
                    message="Check-out successful"
                )
                
            except Exception as sql_error:
                _logger.error(f"Direct SQL update failed: {str(sql_error)}")
                return self._error_response("Failed to record check-out time", 500)
            
        except json.JSONDecodeError:
            return self._error_response("Invalid JSON data", 400)
        except Exception as e:
            _logger.error(f"Check-out error: {str(e)}")
            return self._error_response("Check-out failed", 500)
    
    @http.route('/api/attendance', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_attendance(self):
        """Get attendance records"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session using our authentication method
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get query parameters
            limit = int(request.httprequest.args.get('limit', 20))
            offset = int(request.httprequest.args.get('offset', 0))
            employee_id = request.httprequest.args.get('employee_id')
            date_from = request.httprequest.args.get('date_from')
            date_to = request.httprequest.args.get('date_to')
            
            # Build domain
            domain = []
            if employee_id:
                domain.append(('employee_id', '=', int(employee_id)))
            if date_from:
                domain.append(('check_in', '>=', f'{date_from} 00:00:00'))
            if date_to:
                domain.append(('check_in', '<=', f'{date_to} 23:59:59'))
            
            # Get attendance records using sudo()
            attendances = request.env['hr.attendance'].sudo().search(domain, limit=limit, offset=offset, order='check_in desc')
            total_count = request.env['hr.attendance'].sudo().search_count(domain)
            
            attendance_data = []
            for attendance in attendances:
                attendance_data.append({
                    'id': attendance.id,
                    'employee_name': attendance.employee_id.name,
                    'employee_id': attendance.employee_id.id,
                    'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else None,
                    'worked_hours': attendance.worked_hours,
                    'date': attendance.check_in.strftime('%Y-%m-%d'),
                })
            
            return self._json_response(
                data={
                    'attendances': attendance_data,
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                },
                message="Attendance records retrieved successfully"
            )
            
        except Exception as e:
            _logger.error(f"Attendance list error: {str(e)}")
            return self._error_response("Failed to retrieve attendance records", 500)
    
    @http.route('/api/attendance/status/<int:employee_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_attendance_status(self, employee_id):
        """Get current attendance status for employee"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            # Get user from session using our authentication method
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return self._error_response("Employee not found", 404)
            
            # Check today's attendance using sudo()
            today = date.today()
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', f'{today} 00:00:00'),
                ('check_in', '<=', f'{today} 23:59:59')
            ], limit=1, order='check_in desc')
            
            if attendance:
                status_data = {
                    'employee_id': employee_id,
                    'employee_name': employee.name,
                    'is_checked_in': not attendance.check_out,
                    'last_attendance_id': attendance.id,
                    'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else None,
                    'worked_hours_today': attendance.worked_hours if attendance.check_out else 0,
                    'status': 'checked_in' if not attendance.check_out else 'checked_out'
                }
            else:
                status_data = {
                    'employee_id': employee_id,
                    'employee_name': employee.name,
                    'is_checked_in': False,
                    'last_attendance_id': None,
                    'check_in': None,
                    'check_out': None,
                    'worked_hours_today': 0,
                    'status': 'not_checked_in'
                }
            
            return self._json_response(
                data=status_data,
                message="Attendance status retrieved successfully"
            )
            
        except Exception as e:
            _logger.error(f"Attendance status error: {str(e)}")
            return self._error_response("Failed to retrieve attendance status", 500)

    @http.route('/api/health', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def health_check(self):
        """Simple health check endpoint"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            return self._json_response(
                data={
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'service': 'HRIS Backend API'
                },
                message="Service is running normally"
            )
        except Exception as e:
            _logger.error(f"Health check error: {str(e)}")
            return self._error_response("Service unhealthy", 500)

    @http.route('/api/attendance/office-location', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def update_office_location(self):
        """Update office location coordinates in Odoo company settings"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            # Get user from session
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Parse request data
            data = json.loads(request.httprequest.data.decode('utf-8'))
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not latitude or not longitude:
                return self._error_response("Latitude and longitude are required", 400)
            
            # Validate coordinates
            try:
                lat_float = float(latitude)
                lng_float = float(longitude)
                
                if not (-90 <= lat_float <= 90):
                    return self._error_response("Invalid latitude range (-90 to 90)", 400)
                if not (-180 <= lng_float <= 180):
                    return self._error_response("Invalid longitude range (-180 to 180)", 400)
                    
            except (ValueError, TypeError):
                return self._error_response("Invalid coordinate format", 400)
            
            # Update company's office location
            company = user.company_id or request.env.company
            company.sudo().write({
                'latitude': lat_float,
                'longitude': lng_float,
            })
            
            _logger.info(f"Office location updated by user {user.login}: {lat_float}, {lng_float}")
            
            return self._json_response(
                data={
                    'latitude': lat_float,
                    'longitude': lng_float,
                    'company_id': company.id,
                    'company_name': company.name
                },
                message="Office location updated successfully in Odoo"
            )
            
        except Exception as e:
            _logger.error(f"Update office location error: {str(e)}")
            return self._error_response("Failed to update office location", 500)

    @http.route('/api/attendance/office-location', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_office_location(self):
        """Get current office location coordinates from Odoo company settings"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
            
        try:
            # Get user from session
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get company's office location
            company = user.company_id or request.env.company
            
            # Fallback coordinates if not set
            latitude = getattr(company, 'latitude', None) or -6.9866798
            longitude = getattr(company, 'longitude', None) or 107.629251
            
            return self._json_response(
                data={
                    'latitude': latitude,
                    'longitude': longitude,
                    'company_id': company.id,
                    'company_name': company.name
                },
                message="Office location retrieved successfully from Odoo"
            )
            
        except Exception as e:
            _logger.error(f"Get office location error: {str(e)}")
            return self._error_response("Failed to retrieve office location", 500)

    @http.route('/api/attendance/history', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_attendance_history(self):
        """Get attendance history for current user"""
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())
        
        try:
            user = self._get_user_from_session()
            if not user:
                return self._error_response("Authentication required", 401)
            
            # Get employee
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not employee:
                return self._error_response("Employee record not found", 404)
            
            # Get query parameters
            start_date = request.httprequest.args.get('start_date')
            end_date = request.httprequest.args.get('end_date')
            
            # Default to last 30 days if not specified
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Parse dates
            try:
                start_datetime = datetime.strptime(start_date[:10], '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date[:10], '%Y-%m-%d')
            except ValueError:
                return self._error_response("Invalid date format. Use YYYY-MM-DD", 400)
            
            # Get attendance records
            attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_datetime),
                ('check_in', '<=', end_datetime + timedelta(days=1))
            ], order='check_in desc')
            
            # Group by date and format response
            attendance_data = []
            attendance_by_date = {}
            
            indonesia_tz = pytz.timezone('Asia/Jakarta')
            
            for attendance in attendances:
                check_in_date = attendance.check_in.date() if attendance.check_in else None
                if check_in_date:
                    date_str = check_in_date.strftime('%Y-%m-%d')
                    
                    if date_str not in attendance_by_date:
                        attendance_by_date[date_str] = {
                            'date': date_str,
                            'check_in': None,
                            'check_out': None,
                            'working_hours': '00:00:00',
                            'status': 'Present'
                        }
                    
                    # Check-in time
                    if attendance.check_in and not attendance_by_date[date_str]['check_in']:
                        attendance_by_date[date_str]['check_in'] = self._format_time_local(attendance.check_in)
                    
                    # Check-out time
                    if attendance.check_out:
                        attendance_by_date[date_str]['check_out'] = self._format_time_local(attendance.check_out)
                        
                        # Calculate working hours in HH:MM:SS format
                        if attendance.check_in:
                            working_duration = attendance.check_out - attendance.check_in
                            hours = int(working_duration.total_seconds() // 3600)
                            minutes = int((working_duration.total_seconds() % 3600) // 60)
                            seconds = int(working_duration.total_seconds() % 60)
                            attendance_by_date[date_str]['working_hours'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            attendance_by_date[date_str]['working_hours'] = '00:00:00'
                    
                    # Determine status (late if check-in after 10:30 AM)
                    if attendance.check_in:
                        check_in = attendance.check_in
                        if check_in.tzinfo is None:
                            check_in = pytz.utc.localize(check_in).astimezone(indonesia_tz)
                        else:
                            check_in = check_in.astimezone(indonesia_tz)
                        check_in_time = check_in.time()
                        if check_in_time > time(10, 30):  # Late if after 10:30 AM
                            attendance_by_date[date_str]['status'] = 'Late'
            
            # Convert to list and sort by date
            attendance_data = list(attendance_by_date.values())
            attendance_data.sort(key=lambda x: x['date'], reverse=True)
            
            return self._json_response(
                data=attendance_data,
                message=f"Attendance history retrieved successfully. Found {len(attendance_data)} records."
            )
            
        except Exception as e:
            _logger.error(f"Get attendance history error: {str(e)}")
            return self._error_response("Failed to retrieve attendance history", 500)
