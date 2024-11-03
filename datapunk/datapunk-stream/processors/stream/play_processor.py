from typing import Dict, Any
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor
from core.config import get_settings
from datetime import datetime, timezone

class PlayProcessor(BaseEventProcessor):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.event_types = {
            'install': self._process_install_event,
            'purchase': self._process_purchase_event,
            'subscription': self._process_subscription_event,
            'review': self._process_review_event,
            'redemption': self._process_redemption_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        processor = self.event_types.get(event.data.get('event_type'))
        if not processor:
            raise ValueError(f"Unknown Play Store event type: {event.data.get('event_type')}")
        return await processor(event)

    async def _process_install_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process app installation events"""
        data = event.data
        return {
            'app': {
                'package_name': data.get('package_name'),
                'app_name': data.get('app_name'),
                'version': data.get('version_code'),
                'install_source': data.get('install_source')
            },
            'device': {
                'id': data.get('device_id'),
                'model': data.get('device_model'),
                'os_version': data.get('android_version')
            },
            'timestamp': event.timestamp.isoformat(),
            'status': data.get('status'),  # installed, uninstalled, updated
            'auto_update': data.get('auto_update', False)
        }

    async def _process_purchase_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process purchase events"""
        data = event.data
        return {
            'transaction': {
                'id': data.get('transaction_id'),
                'product_id': data.get('product_id'),
                'product_type': data.get('product_type'),  # app, in-app, movie, book
                'amount': data.get('amount'),
                'currency': data.get('currency'),
                'payment_method': data.get('payment_method')
            },
            'timestamp': event.timestamp.isoformat(),
            'status': data.get('status')  # completed, refunded, pending
        }

    async def _process_subscription_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process subscription events"""
        data = event.data
        return {
            'subscription': {
                'id': data.get('subscription_id'),
                'product_id': data.get('product_id'),
                'plan': data.get('plan_name'),
                'renewal_period': data.get('renewal_period'),
                'price': {
                    'amount': data.get('amount'),
                    'currency': data.get('currency')
                },
                'status': data.get('status'),  # active, cancelled, expired
                'auto_renew': data.get('auto_renew', False),
                'trial_period': data.get('trial_period')
            },
            'timestamp': event.timestamp.isoformat()
        }