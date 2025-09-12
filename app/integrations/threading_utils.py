import threading
import functools
from flask import current_app
from typing import Callable, Any


class ThreadedNotificationService:
    """Service for handling threaded notifications (SMS and Email)"""
    
    def __init__(self):
        self._thread_pool = []
    
    def execute_in_thread(self, func: Callable, *args, **kwargs) -> threading.Thread:
        """Execute a function in a separate thread"""
        # Capture the Flask app instance before starting the thread
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            # If we're not in an application context, try to get the app from the global registry
            from flask import Flask
            app = Flask.get_current_app() if hasattr(Flask, 'get_current_app') else None
            if app is None:
                # Last resort: import the app directly
                from app import create_app
                app = create_app()
        
        def wrapper():
            try:
                # Create a new application context for the thread using the captured app
                with app.app_context():
                    func(*args, **kwargs)
            except Exception as e:
                # Use the app's logger if available, otherwise use print
                if hasattr(app, 'logger'):
                    app.logger.error(f"Error in threaded execution: {str(e)}")
                else:
                    print(f"Error in threaded execution: {str(e)}")
        
        thread = threading.Thread(target=wrapper)
        thread.daemon = True  # Thread will die when main thread dies
        thread.start()
        
        # Keep track of threads for cleanup
        self._thread_pool.append(thread)
        
        # Clean up finished threads
        self._cleanup_finished_threads()
        
        return thread
    
    def _cleanup_finished_threads(self):
        """Remove finished threads from the pool"""
        self._thread_pool = [t for t in self._thread_pool if t.is_alive()]
    
    def wait_for_all_threads(self, timeout: float = None):
        """Wait for all threads to complete (useful for testing)"""
        for thread in self._thread_pool:
            thread.join(timeout=timeout)


# Global instance
threaded_service = ThreadedNotificationService()


def threaded_notification(func: Callable) -> Callable:
    """Decorator to make notification functions run in threads"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return threaded_service.execute_in_thread(func, *args, **kwargs)
    return wrapper


def send_sms_threaded(sms_service, phone_number: str, message: str):
    """Send SMS in a separate thread"""
    try:
        sms_service.send_sms(phone_number, message)
        # Try to use current_app logger, fallback to print if not available
        try:
            current_app.logger.info(f"SMS sent successfully to {phone_number}")
        except RuntimeError:
            print(f"SMS sent successfully to {phone_number}")
    except Exception as e:
        try:
            current_app.logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
        except RuntimeError:
            print(f"Failed to send SMS to {phone_number}: {str(e)}")


def send_email_threaded(mailer_service, recipients: list, subject: str, text: str, sender: str = None, html: bool = False):
    """Send email in a separate thread"""
    try:
        mailer_service.send_email(
            recipients=recipients,
            subject=subject,
            text=text,
            html=html
        )
        # Try to use current_app logger, fallback to print if not available
        try:
            current_app.logger.info(f"Email sent successfully to {recipients}")
        except RuntimeError:
            print(f"Email sent successfully to {recipients}")
    except Exception as e:
        try:
            current_app.logger.error(f"Failed to send email to {recipients}: {str(e)}")
        except RuntimeError:
            print(f"Failed to send email to {recipients}: {str(e)}")
