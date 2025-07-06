# studentPanel/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.conf import settings
import datetime

class SessionTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        timeout = getattr(settings, 'SESSION_COOKIE_AGE', 1800)
        last_activity = request.session.get('last_activity')

        if last_activity:
            now = datetime.datetime.now().timestamp()
            if now - last_activity > timeout:
                from django.contrib.auth import logout
                logout(request)
                return redirect('student_login')  # replace with your actual login route

        request.session['last_activity'] = datetime.datetime.now().timestamp()


class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get('last_touch'):
            now = datetime.datetime.now()
            last_touch = datetime.datetime.strptime(request.session['last_touch'], '%Y-%m-%d %H:%M:%S')
            if (now - last_touch).seconds > 600:  # 10 minutes timeout
                request.session.flush()

        request.session['last_touch'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.get_response(request)