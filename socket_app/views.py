from django.shortcuts import render

# Create your views here.

def websocket_test_view(request):
    return render(request, "websocket_test.html")

