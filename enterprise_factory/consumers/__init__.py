# enterprise_factory/consumers.py
# (File điều hướng chính, cung cấp WarRoomConsumer cho routing.py)

from .chat_handler import ChatHandlerConsumer

# Gán alias WarRoomConsumer để routing.py gọi trực tiếp hoạt động 100%
WarRoomConsumer = ChatHandlerConsumer