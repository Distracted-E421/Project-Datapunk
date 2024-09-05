import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datapunk.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # If you plan to add WebSocket support later:
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(
    #         your_websocket_urlpatterns
    #     )
    # ),
})
