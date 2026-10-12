import os
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def anylogic_state(request):
    """GET /api/anylogic/state — proxy to AnyLogic /state endpoint."""
    anylogic_url = os.environ.get('ANYLOGIC_URL', 'http://localhost:8080')
    try:
        resp = requests.get(f'{anylogic_url}/state', timeout=5)
        return JsonResponse(resp.json(), status=resp.status_code)
    except requests.RequestException:
        return JsonResponse({'error': 'anylogic_unavailable'}, status=503)


@csrf_exempt
def anylogic_order(request):
    """POST /api/anylogic/order — proxy to AnyLogic /order endpoint."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    anylogic_url = os.environ.get('ANYLOGIC_URL', 'http://localhost:8080')
    try:
        resp = requests.post(
            f'{anylogic_url}/order',
            data=request.body,
            headers={'Content-Type': 'application/json'},
            timeout=5,
        )
        return JsonResponse(resp.json(), status=resp.status_code)
    except requests.RequestException:
        return JsonResponse({'error': 'anylogic_unavailable'}, status=503)
