import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
	"""Week 12 WebSocket 範例：推送新貼文通知。"""

	group_name = "motry_notifications"

	async def connect(self):
		# 檢查用戶是否已認證
		user = self.scope.get("user")
		if not user or user.is_anonymous:
			logger.warning("WebSocket connection rejected: user not authenticated")
			await self.close(code=4001)
			return

		await self.channel_layer.group_add(self.group_name, self.channel_name)
		await self.accept()
		logger.info(f"WebSocket connected for user: {user.id}")

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(self.group_name, self.channel_name)

	async def receive(self, text_data=None, bytes_data=None):
		# 本示範僅單向推播，不處理前端傳來的訊息
		# 驗證接收到的資料格式（防止惡意輸入）
		if text_data:
			try:
				json.loads(text_data)
			except json.JSONDecodeError:
				logger.warning("Invalid JSON received in WebSocket")
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
