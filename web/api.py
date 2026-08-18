from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import WiehrGlobeModel


@csrf_exempt
@require_http_methods(["GET"])
def release_by_wid(request, wid):
    try:
        release = WiehrGlobeModel.objects.filter(internal_id=wid, is_visible=True).first()
        
        if not release:
            return JsonResponse({
                'success': False,
                'error': 'Release not found or not visible'
            }, status=404)

        data = {
            'success': True,
            'release': {
                'internal_id': release.internal_id,
                'title': release.title,
                'artist': release.artist,
                'date': release.date.isoformat() if release.date else None,
                'image_url': f'/media/{release.image}' if release.image else None,
                'slug': release.slug,
                'url': f'/releases/{release.slug}',
                'background_color': release.background_color,
                'credits': release.credits,
                'geo': release.geo,
            },
            'platforms': [],
            'platform_count': 0
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def releases_list(request):
    try:
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        releases = WiehrGlobeModel.objects.filter(is_visible=True).order_by('-date')[offset:offset+limit]
        
        data = {
            'success': True,
            'count': releases.count(),
            'releases': [
                {
                    'internal_id': r.internal_id,
                    'title': r.title,
                    'artist': r.artist,
                    'date': r.date.isoformat() if r.date else None,
                    'slug': r.slug,
                    'url': f'/releases/{r.slug}',
                    'image_url': f'/media/{r.image}' if r.image else None,
                }
                for r in releases
            ]
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
