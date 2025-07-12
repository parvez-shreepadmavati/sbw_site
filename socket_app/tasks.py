from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from geopy.distance import geodesic
from socket_app.models import LocationData, APIConfig
import requests

@shared_task
def run_user_movement_periodically():
    """
    Run the same logic you have in your view — but on a schedule
    Example: process last 1 hour for all users
    """

    print("Running periodic user movement calculation...")

    # Example: For demonstration, just hardcode a user or loop all unique users
    # user_id = "dhaval.chauhan@silverbluewater.com"

    # Time window — last 1 hour
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=1)

    periphery = get_external_periphery_params()
    periphery_radius = periphery['radius']
    periphery_minutes = periphery['minutes']

    user_ids = (
        LocationData.objects
        .filter(timestamp__gte=start_time, timestamp__lte=end_time)
        .values_list('user_id', flat=True)
        .distinct()
    )

    print(f"Found {len(user_ids)} users to process.")
    print(f"Processing users: {user_ids}")

    for user_id in user_ids:
        print(">>> Processing user:", user_id)
        location_points = LocationData.objects.filter(
            user_id=user_id,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).order_by('timestamp')

        if not location_points.exists():
            print(f"No data for user {user_id}")
            return

        # -- LOGIC SAME AS YOUR VIEW --
        total_distance = 0
        previous_point = None
        current_periphery_start = start_time
        current_periphery_end = start_time + timedelta(minutes=periphery_minutes)
        current_center = None
        points_in_window = []

        for point in location_points:
            current_coord = (point.latitude, point.longitude)
            distance_meters = geodesic(previous_point, current_coord).meters if previous_point else 0.0
            total_distance += distance_meters

            if point.timestamp >= current_periphery_end:
                if points_in_window:
                    lat_sum = sum(p.latitude for p in points_in_window)
                    long_sum = sum(p.longitude for p in points_in_window)
                    count = len(points_in_window)
                    current_center = (lat_sum / count, long_sum / count)

                current_periphery_start = current_periphery_end
                current_periphery_end = current_periphery_start + timedelta(minutes=periphery_minutes)
                points_in_window = []

            points_in_window.append(point)

            if current_center is None:
                current_center = current_coord

            dist_to_center = geodesic(current_center, current_coord).meters
            in_periphery = 1 if (point.timestamp <= current_periphery_end and dist_to_center <= periphery_radius) else 0

            if in_periphery == 1:
                # ✅ CALL 2ND DEVELOPER API HERE
                payload = {
                    "id": point.user_id,
                    "lat": point.latitude,
                    "lng": point.longitude,
                    "centerLat": current_center[0],
                    "centerLng": current_center[1]
                }
                print("Calling 2nd Dev API with payload:", payload)
                post_url = APIConfig.get_url("STORE_SALESPERSON_LOCATION_API_URL")
                print("Post URL :", post_url)
                if not post_url:
                    raise ValueError("STORE_SALESPERSON_LOCATION_API_URL not set in SiteConfig")
                try:
                    response = requests.post(
                        # "http://192.168.1.36:8005/api/method/padmavati_crm.api.salesPersonLocationTracking",
                        post_url,
                        json=payload,
                        timeout=10
                    )
                    print("2nd Dev API Response:", response.status_code, response.text)
                except Exception as e:
                    print("2nd Dev API call failed:", e)

            previous_point = current_coord

        print(f"Processed user: {user_id} | Total Distance: {total_distance}")

def get_external_periphery_params():
    try:
        # url = "http://192.168.1.36:8005/api/method/silverblue_otp.py.targetTemplate.locationParams"
        url = APIConfig.get_url("PERIPHERY_PARAMS_API")
        print("External periphery params:", url)
        if not url:
            raise ValueError("PERIPHERY_PARAMS_API not set in SiteConfig")

        headers = {
            'Cookie': 'full_name=Guest; sid=Guest; system_user=no; user_id=Guest; user_image='
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("message")
            if data:
                return {
                    "radius": float(data.get("radius", 20)),
                    "minutes": int(data.get("minutes", 20))
                }
    except Exception as e:
        print("Error getting periphery params:", e)

    return {"radius": 20, "minutes": 20}
