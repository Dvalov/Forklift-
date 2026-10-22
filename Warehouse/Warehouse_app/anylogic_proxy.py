import json
import os
import time
import requests
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt


def anylogic_state(request):
    """GET /api/anylogic/state — proxy to AnyLogic /state endpoint."""
    anylogic_url = os.environ.get('ANYLOGIC_URL', 'http://127.0.0.1:8080')
    try:
        resp = requests.get(f'{anylogic_url}/state', timeout=5)
        try:
            return JsonResponse(resp.json(), status=resp.status_code)
        except ValueError as e:
            return JsonResponse({'error': 'invalid_json', 'detail': str(e), 'raw': resp.text[:500]}, status=502)
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'anylogic_unavailable', 'detail': str(e)}, status=503)


def anylogic_stream(request):
    """GET /api/anylogic/stream — SSE stream of AnyLogic state at ~150ms intervals."""
    anylogic_url = os.environ.get('ANYLOGIC_URL', 'http://127.0.0.1:8080')

    def event_stream():
        while True:
            try:
                resp = requests.get(f'{anylogic_url}/state', timeout=2)
                payload = json.dumps(resp.json())
            except Exception:
                payload = 'null'

            yield f'data: {payload}\n\n'
            time.sleep(0.15)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@csrf_exempt
def anylogic_order(request):
    """POST /api/anylogic/order — proxy to AnyLogic /order endpoint."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    anylogic_url = os.environ.get('ANYLOGIC_URL', 'http://127.0.0.1:8080')
    try:
        resp = requests.post(
            f'{anylogic_url}/order',
            data=request.body,
            headers={'Content-Type': 'application/json'},
            timeout=5,
        )
        return JsonResponse(resp.json(), status=resp.status_code)
    except Exception as e:
        import traceback; traceback.print_exc()
        return JsonResponse({'error': 'anylogic_unavailable', 'detail': str(e)}, status=503)
