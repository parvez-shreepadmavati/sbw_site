from django.shortcuts import render

# Create your views here.

def websocket_test_view(request):
    return render(request, "websocket_test.html")

from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import geodesic
from socket_app.models import LocationData
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.utils import timezone
import re

import requests

def get_external_periphery_params():
    try:
        url = "http://192.168.1.36:8005/api/method/silverblue_otp.py.targetTemplate.locationParams"
        headers = {
            'Cookie': 'full_name=Guest; sid=Guest; system_user=no; user_id=Guest; user_image='
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("message")  # Depends on your API's actual response shape
            if data:
                return {
                    "radius": float(data.get("radius", 20)),
                    "minutes": int(data.get("minutes", 20))
                }
    except Exception as e:
        print(f"Error fetching external periphery params: {e}")

    return {"radius": 20, "minutes": 20}


def normalize_datetime_string(dt_str):
    if dt_str and re.match(r"^\d{4}-\d{2}-\d{2}\d{2}:\d{2}:\d{2}$", dt_str):
        return dt_str[:10] + 'T' + dt_str[10:]
    return dt_str

@csrf_exempt
def user_movement(request, user_id):
    try:
        # Read request params
        raw_start = request.GET.get("start_time")
        raw_end = request.GET.get("end_time")
        # periphery_minutes = int(request.GET.get("periphery_duration", 20))
        # periphery_radius = float(request.GET.get("periphery_radius", 20))
        # Try getting from query params
        periphery_minutes = request.GET.get("periphery_duration")
        periphery_radius = request.GET.get("periphery_radius")

        # If not provided, fallback to external API
        if periphery_minutes is None or periphery_radius is None:
            external = get_external_periphery_params()
            print("External periphery params:", external)
            periphery_minutes = periphery_minutes or external["minutes"]
            periphery_radius = periphery_radius or external["radius"]
            print("Using external periphery params:", periphery_minutes, periphery_radius)

        # Cast safely
        periphery_minutes = int(periphery_minutes)
        periphery_radius = float(periphery_radius)
        print("Using internal periphery params:", periphery_minutes, periphery_radius)

        start_param = normalize_datetime_string(raw_start)
        end_param = normalize_datetime_string(raw_end)

        current_time = timezone.now()

        start_time = parse_datetime(start_param) if start_param else current_time - timedelta(hours=1)
        end_time = parse_datetime(end_param) if end_param else current_time

        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)

        if not start_time or not end_time:
            return JsonResponse({
                "status": "error",
                "message": "Invalid datetime format"
            }, status=400)

        if start_time >= end_time:
            return JsonResponse({
                "status": "error",
                "message": "Start time must be earlier than end time"
            }, status=400)

        # Get points
        location_points = LocationData.objects.filter(
            user_id=user_id,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).order_by('timestamp')

        if not location_points.exists():
            return JsonResponse({
                "status": "success",
                "user": user_id,
                "message": "No data",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_distance_meters": 0,
                "periphery_radius_meters": periphery_radius,
                "periphery_duration_minutes": periphery_minutes,
                "periphery_valid_until": (start_time + timedelta(minutes=periphery_minutes)).isoformat(),
                "points_count": 0,
                "points": []
            })

        # Initialize variables
        total_distance = 0
        previous_point = None
        points_data = []
        current_periphery_start = start_time
        current_periphery_end = start_time + timedelta(minutes=periphery_minutes)
        current_center = None
        points_in_window = []

        for point in location_points:
            current_coord = (point.latitude, point.longitude)
            print("Processing point:", point.id, current_coord, "at", point.timestamp)

            # Distance from previous point (for total distance)
            distance_meters = geodesic(previous_point, current_coord).meters if previous_point else 0.0
            print("distance_meters:", distance_meters)
            total_distance += distance_meters

            # Check if we need to move to the next periphery window
            if point.timestamp >= current_periphery_end:
                # Compute new center based on points in the last window
                if points_in_window:
                    lat_sum = sum(p.latitude for p in points_in_window)
                    long_sum = sum(p.longitude for p in points_in_window)
                    count = len(points_in_window)
                    current_center = (lat_sum / count, long_sum / count)

                # Reset for next window
                current_periphery_start = current_periphery_end
                current_periphery_end = current_periphery_start + timedelta(minutes=periphery_minutes)
                points_in_window = []

            # Add point to current window
            points_in_window.append(point)

            # If no center yet, use the first point as center
            if current_center is None:
                current_center = current_coord

            # Distance from current center
            dist_to_center = geodesic(current_center, current_coord).meters

            # Check if in periphery
            in_periphery = 1 if (point.timestamp <= current_periphery_end and dist_to_center <= periphery_radius) else 0
            print("Current center:", current_center, "Distance to center:", dist_to_center, "In periphery:", in_periphery)

            points_data.append({
                "id": point.id,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "timestamp": point.timestamp.isoformat(),
                "distance_meters": round(distance_meters, 2),
                "distance_to_center": round(dist_to_center, 2),
                "in_periphery_flag": in_periphery,
                "current_center_lat": current_center[0],
                "current_center_long": current_center[1],
                "periphery_window_end": current_periphery_end.isoformat()
            })

            previous_point = current_coord

        # Final center (average of all points if needed)
        lat_sum = sum(p.latitude for p in location_points)
        long_sum = sum(p.longitude for p in location_points)
        count = location_points.count()
        overall_center = (lat_sum / count, long_sum / count)

        return JsonResponse({
            "status": "success",
            "user": user_id,
            "center_point": {
                "latitude": overall_center[0],
                "longitude": overall_center[1]
            },
            "total_distance_meters": round(total_distance, 2),
            "periphery_radius_meters": periphery_radius,
            "periphery_duration_minutes": periphery_minutes,
            "periphery_valid_until": current_periphery_end.isoformat(),  # Last computed window
            "points_count": len(points_data),
            "points": points_data
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
'''
def normalize_datetime_string(dt_str):
    if dt_str and re.match(r"^\d{4}-\d{2}-\d{2}\d{2}:\d{2}:\d{2}$", dt_str):
        return dt_str[:10] + 'T' + dt_str[10:]
    return dt_str

@csrf_exempt
def user_movement(request, user_id):
    try:
        # ✅ Read request params
        raw_start = request.GET.get("start_time")
        raw_end = request.GET.get("end_time")
        periphery_minutes = int(request.GET.get("periphery_duration", 20))
        periphery_radius = float(request.GET.get("periphery_radius", 20))


        start_param = normalize_datetime_string(raw_start)
        end_param = normalize_datetime_string(raw_end)

        current_time = timezone.now()

        start_time = parse_datetime(start_param) if start_param else current_time - timedelta(hours=1)
        end_time = parse_datetime(end_param) if end_param else current_time
        print("End time:", end_time)

        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
            print("End time after make_aware:", end_time)



        if not start_time or not end_time:
            return JsonResponse({
                "status": "error",
                "message": "Invalid datetime format"
            }, status=400)

        if start_time >= end_time:
            return JsonResponse({
                "status": "error",
                "message": "Start time must be earlier than end time"
            }, status=400)

        # ✅ Get points
        location_points = LocationData.objects.filter(
            user_id=user_id,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).order_by('timestamp')

        if not location_points.exists():
            return JsonResponse({
                "status": "success",
                "user": user_id,
                "message": "No data",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_distance_meters": 0,
                "periphery_radius_meters": periphery_radius,
                "periphery_duration_minutes": periphery_minutes,
                "periphery_valid_until": (start_time + timedelta(minutes=periphery_minutes)).isoformat(),
                "points_count": 0,
                "points": []
            })

        # ✅ Calculate center point (mean lat/long)
        lat_sum = sum(p.latitude for p in location_points)
        long_sum = sum(p.longitude for p in location_points)
        count = location_points.count()
        center_lat = lat_sum / count
        center_long = long_sum / count
        center_coord = (center_lat, center_long)

        total_distance = 0
        previous_point = None
        points_data = []
        periphery_end_time = start_time + timedelta(minutes=periphery_minutes)

        for point in location_points:
            current_coord = (point.latitude, point.longitude)

            # Distance from previous point
            distance_meters = geodesic(previous_point, current_coord).meters if previous_point else 0.0
            total_distance += distance_meters

            # Distance from center point
            dist_to_center = geodesic(center_coord, current_coord).meters

            # Check periphery flag:
            in_periphery = 0
            if point.timestamp <= periphery_end_time and dist_to_center <= periphery_radius:
                in_periphery = 1

            points_data.append({
                "latitude": point.latitude,
                "longitude": point.longitude,
                "timestamp": point.timestamp.isoformat(),
                "distance_meters": round(distance_meters, 2),
                "distance_to_center": round(dist_to_center, 2),
                "in_periphery_flag": in_periphery
            })

            previous_point = current_coord

        return JsonResponse({
            "status": "success",
            "user": user_id,
            "center_point": {
                "latitude": center_lat,
                "longitude": center_long
            },
            "total_distance_meters": round(total_distance, 2),
            "periphery_radius_meters": periphery_radius,
            "periphery_duration_minutes": periphery_minutes,
            "periphery_valid_until": periphery_end_time.isoformat(),
            "points_count": len(points_data),
            "points": points_data
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
'''

'''
@csrf_exempt
def user_movement(request, user_id):
    """
    API: Get user location data in a time range and return distance between each consecutive point
    """
    try:
        # Query parameters
        start_param = request.GET.get("start_time")
        end_param = request.GET.get("end_time")

        current_time = now()
        start_time = parse_datetime(start_param) if start_param else current_time - timedelta(hours=1)
        end_time = parse_datetime(end_param) if end_param else current_time

        if not start_time or not end_time:
            return JsonResponse({
                "status": "error",
                "message": "Invalid datetime format. Use ISO format like 2025-06-26T08:00:00"
            }, status=400)

        if start_time >= end_time:
            return JsonResponse({
                "status": "error",
                "message": "Start time must be earlier than end time"
            }, status=400)

        # Fetch records
        location_points = LocationData.objects.filter(
            user_id=user_id,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).order_by('timestamp')

        if not location_points.exists():
            return JsonResponse({
                "status": "success",
                "user": user_id,
                "total_distance_meters": 0,
                "points_count": 0,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "points": [],
                "message": "No data found in the specified time range"
            })

        total_distance = 0
        previous_point = None
        points_data = []

        for point in location_points:
            current_coord = (point.latitude, point.longitude)

            # Calculate distance from previous point
            if previous_point:
                distance = geodesic(previous_point, current_coord).meters
            else:
                distance = 0.0  # First point

            points_data.append({
                "latitude": point.latitude,
                "longitude": point.longitude,
                "timestamp": point.timestamp.isoformat(),
                "distance_meters": round(distance, 2)
            })

            total_distance += distance
            previous_point = current_coord

        return JsonResponse({
            "status": "success",
            "user": user_id,
            "total_distance_meters": round(total_distance, 2),
            "points_count": len(points_data),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "points": points_data
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
'''