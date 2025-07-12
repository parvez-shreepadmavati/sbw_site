from django.urls import path
from .views import websocket_test_view, user_movement

urlpatterns = [
    path("ws-test/", websocket_test_view, name="websocket_test"),
    path("api/user-movement/<str:user_id>/", user_movement, name="user_movement"),
]
