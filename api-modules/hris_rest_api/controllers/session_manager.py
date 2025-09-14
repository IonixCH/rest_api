import logging
from datetime import datetime, timedelta
from odoo.http import request
import threading

_logger = logging.getLogger(__name__)

class SessionManager:
    """Simple session manager for API authentication"""
    
    def __init__(self):
        self._sessions = {}  # {session_token: {'user_id': int, 'created_at': datetime, 'last_used': datetime}}
        self._lock = threading.Lock()
        self._cleanup_interval = timedelta(hours=24)  # Sessions expire after 24 hours
    
    def store_session(self, session_token, user_id):
        """Store session mapping"""
        try:
            with self._lock:
                self._sessions[session_token] = {
                    'user_id': user_id,
                    'created_at': datetime.now(),
                    'last_used': datetime.now()
                }
                _logger.info(f"Session stored: {session_token} -> user {user_id}")
                self._cleanup_expired_sessions()
        except Exception as e:
            _logger.error(f"Error storing session: {str(e)}")
    
    def get_user_id(self, session_token):
        """Get user ID from session token"""
        try:
            with self._lock:
                session_data = self._sessions.get(session_token)
                if session_data:
                    # Check if session is not expired
                    if datetime.now() - session_data['created_at'] < self._cleanup_interval:
                        # Update last used time
                        session_data['last_used'] = datetime.now()
                        return session_data['user_id']
                    else:
                        # Session expired, remove it
                        del self._sessions[session_token]
                        _logger.info(f"Session expired and removed: {session_token}")
                
                return None
        except Exception as e:
            _logger.error(f"Error getting user from session: {str(e)}")
            return None

    def get_session(self, session_token):
        """Get session data from session token"""
        try:
            with self._lock:
                session_data = self._sessions.get(session_token)
                if session_data:
                    # Check if session is not expired
                    if datetime.now() - session_data['created_at'] < self._cleanup_interval:
                        # Update last used time
                        session_data['last_used'] = datetime.now()
                        return session_data
                    else:
                        # Session expired, remove it
                        del self._sessions[session_token]
                        _logger.info(f"Session expired and removed: {session_token}")
                
                return None
        except Exception as e:
            _logger.error(f"Error getting session: {str(e)}")
            return None
    
    def remove_session(self, session_token):
        """Remove session"""
        try:
            with self._lock:
                if session_token in self._sessions:
                    del self._sessions[session_token]
                    _logger.info(f"Session removed: {session_token}")
        except Exception as e:
            _logger.error(f"Error removing session: {str(e)}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            now = datetime.now()
            expired_tokens = []
            
            for token, data in self._sessions.items():
                if now - data['created_at'] > self._cleanup_interval:
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                del self._sessions[token]
                
            if expired_tokens:
                _logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
                
        except Exception as e:
            _logger.error(f"Error during session cleanup: {str(e)}")
    
    def get_session_count(self):
        """Get current session count (for debugging)"""
        with self._lock:
            return len(self._sessions)

# Global session manager instance
session_manager = SessionManager()

