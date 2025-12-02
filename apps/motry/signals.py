from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_keys import BRAND_MAP_CACHE_KEY
from .models import Post, Vehicle


@receiver([post_save, post_delete], sender=Vehicle)
def clear_brand_map_cache(**kwargs):
	cache.delete(BRAND_MAP_CACHE_KEY)


@receiver(post_save, sender=Post)
def notify_new_post(sender, instance: Post, created: bool, **kwargs):
	"""Week 12 WebSocket 範例：新增貼文時透過 Channels 推播通知。"""
	if not created:
		return

	channel_layer = get_channel_layer()
	if not channel_layer:
		return

	async_to_sync(channel_layer.group_send)(
		"motry_notifications",
		{
			"type": "motry_notification",
			"post_id": instance.id,
			"title": str(instance),
			"vehicle": {
				"id": instance.vehicle_id,
				"name": str(instance.vehicle),
			},
		},
	)
