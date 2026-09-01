from django.conf import settings

CACHEABLE_EXTENSIONS = (
    '.woff2', '.woff', '.ttf', '.eot',
    '.svg', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.ico',
    '.css', '.js',
    '.ogg', '.mp3', '.wav',
    '.pdf', '.zip',
)


class StaticFilesCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            if any(request.path.endswith(ext) for ext in CACHEABLE_EXTENSIONS):
                if getattr(settings, 'ENV', 'DEV') == 'PROD':
                    response['Cache-Control'] = 'public, max-age=31536000, immutable'
                else:
                    response['Cache-Control'] = 'no-cache, must-revalidate'
        
        if request.path == '/':
            links = [
                '</robots.txt>; rel="robots"',
                '</sitemap.xml>; rel="sitemap"; type="application/xml"',
                '</llms.txt>; rel="ai-agent"; type="text/plain"',
            ]
            response['Link'] = ', '.join(links)

        if hasattr(settings, 'ENV') and settings.ENV == 'PROD':
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'
        
        return response
