from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

def broadcast_dashboard_update(update_type="STOCK_UPDATED", message="Stock updated", data=None):
    """
    Broadcasts a WebSocket message to all connected clients in 'dashboard_updates' group.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'dashboard_updates',
                {
                    'type': 'dashboard_update',
                    'update_type': update_type,
                    'message': message,
                    'data': data or {}
                }
            )
    except Exception as e:
        logger.warning(f"Failed to broadcast WebSocket update: {e}")
