import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
	"""Week 12 WebSocket 範例：推送新貼文通知。"""

	group_name = "motry_notifications"

	async def connect(self):
		await self.channel_layer.group_add(self.group_name, self.channel_name)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(self.group_name, self.channel_name)

	async def receive(self, text_data=None, bytes_data=None):
		# 本示範僅單向推播，不處理前端傳來的訊息
		return

	async def motry_notification(self, event):
		await self.send(
			text_data=json.dumps(
				{
					"type": "new_post",
					"post_id": event.get("post_id"),
					"title": event.get("title"),
					"vehicle": event.get("vehicle"),
				}
			)
		)
