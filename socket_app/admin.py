from django.contrib import admin
from .models import SocketSettings, LocationData, APIConfig
import urllib.parse
import urllib.request
import json
# Register your models here.
# admin.site.register(SocketSettings)
# admin.site.register(LocationData)
admin.site.site_header = 'Silver Blue Water Admin'
admin.site.index_title = 'SBW administration'
# admin.site.site_title = 'HTML title from adminsitration'

from django.contrib import admin
from .models import LocationData
from django.utils.html import format_html

admin.site.register(APIConfig)

@admin.register(LocationData)
class LocationDataAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'socket_id', 'latitude', 'longitude', 'date', 'time', 'timestamp', 'map_link')
    search_fields = ('user_id', 'date', 'socket_id', 'latitude', 'longitude')
    list_filter = ('date', 'user_id')

    fieldsets = (
        ("User Information", {"fields": ("user_id",)}),
        ("Location Details", {"fields": ("latitude", "longitude", "map_preview", "address_preview")}),
        ("Timestamps", {"fields": ("date", "time", "timestamp")}),
    )

    # readonly_fields = ('map_preview', 'address_preview', 'user_id', 'socket_id', 'latitude', 'longitude', 'date', 'time', 'timestamp')
    readonly_fields = ('map_preview', 'address_preview', )

    def map_preview(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" '
                'src="https://www.openstreetmap.org/export/embed.html?bbox={lon}%2C{lat}%2C{lon}%2C{lat}&amp;layer=mapnik&amp;marker={lat}%2C{lon}" '
                'style="border: 1px solid black"></iframe>',
                lat=obj.latitude,
                lon=obj.longitude
            )
        return "No coordinates available"
    map_preview.short_description = "Map Preview"

    def map_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}" target="_blank">View Map</a>',
                lat=obj.latitude,
                lon=obj.longitude
            )
        return "-"
    map_link.short_description = "Map Link"

    def address_preview(self, obj):
        if obj.latitude and obj.longitude:
            try:
                params = urllib.parse.urlencode({
                    'format': 'json',
                    'lat': obj.latitude,
                    'lon': obj.longitude,
                    'zoom': 18,
                    'addressdetails': 1
                })
                url = f"https://nominatim.openstreetmap.org/reverse?{params}"
                headers = {'User-Agent': 'Mozilla/5.0 (DjangoAdminApp)'}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if 'display_name' in data:
                        return format_html('<p>{}</p>', data['display_name'])
                    else:
                        return "Address not found"
            except Exception as e:
                return f"Error fetching address: {e}"
        return "No coordinates available"
    address_preview.short_description = "Address (Reverse Geocoded)"

    # # This removes the "Add" button
    # def has_add_permission(self, request, obj=None):
    #     return False
    #
    # # Optional: Also remove delete permissions
    # def has_delete_permission(self, request, obj=None):
    #     return False


@admin.register(SocketSettings)
class SocketSettingsAdmin(admin.ModelAdmin):
    # This removes the "Add" button
    def has_add_permission(self, request, obj=None):
        return False

    # Optional: Also remove delete permissions
    def has_delete_permission(self, request, obj=None):
        return False


