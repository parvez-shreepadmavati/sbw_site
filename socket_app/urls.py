from django.urls import path
from .views import websocket_test_view

urlpatterns = [
    path("ws-test/", websocket_test_view, name="websocket_test"),
]
