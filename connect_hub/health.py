from django.http import JsonResponse


def health(request):
    """Simple health check used by host health monitors.

    Returns 200 OK with a small JSON body so load balancers and uptime checks
    can verify the site is up.
    """
    return JsonResponse({"status": "ok"})
