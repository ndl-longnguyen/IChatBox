import asyncio

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase, TransactionTestCase, override_settings

from chat.consumers import ChatForUserConsumer, has_required_visitor_info
from chat.models import ChatRoom
from users.models import Participant, User


class VisitorInfoValidationTests(SimpleTestCase):
    def test_allows_guest_when_anonymous_mode_is_enabled(self):
        self.assertTrue(
            has_required_visitor_info(
                allow_anonymous=True,
                username=None,
                phone=None,
                email=None,
            )
        )

    def test_requires_name_and_contact_when_anonymous_mode_is_disabled(self):
        self.assertFalse(
            has_required_visitor_info(
                allow_anonymous=False,
                username="Visitor",
                phone=None,
                email=None,
            )
        )

        self.assertTrue(
            has_required_visitor_info(
                allow_anonymous=False,
                username="Visitor",
                phone="0987654321",
                email=None,
            )
        )

        self.assertTrue(
            has_required_visitor_info(
                allow_anonymous=False,
                username="Visitor",
                phone=None,
                email="visitor@example.com",
            )
        )


@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
)
class ChatForUserConsumerTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="admin-user",
            first_name="Admin",
            last_name="User",
        )
        self.customer_key = self.user.customer_key

    async def connect(self, query_string):
        communicator = WebsocketCommunicator(
            ChatForUserConsumer.as_asgi(),
            f"/ws/user/chat/?token={self.customer_key.key}{query_string}",
        )
        connected, close_code = await communicator.connect()
        return communicator, connected, close_code

    async def disconnect(self, communicator):
        try:
            await communicator.disconnect()
        except asyncio.CancelledError:
            pass

    async def wait_for_close(self, communicator):
        await communicator.wait()

    def test_connect_rejects_missing_contact_info_when_anonymous_is_disabled(
        self,
    ):
        self.customer_key.allow_anonymous = False
        self.customer_key.save(update_fields=["allow_anonymous"])

        communicator, connected, _ = async_to_sync(self.connect)(
            "&username=Visitor"
        )

        self.assertFalse(connected)
        self.assertEqual(Participant.objects.count(), 0)
        self.assertEqual(ChatRoom.objects.count(), 0)
        async_to_sync(self.wait_for_close)(communicator)

    def test_connect_accepts_visitor_info_when_anonymous_is_disabled(self):
        self.customer_key.allow_anonymous = False
        self.customer_key.save(update_fields=["allow_anonymous"])

        communicator, connected, _ = async_to_sync(self.connect)(
            "&username=Visitor&email=visitor%40example.com&device=device-1"
        )

        self.assertTrue(connected)
        participant = Participant.objects.get(user=self.user)
        self.assertEqual(participant.name, "Visitor")
        self.assertEqual(participant.email, "visitor@example.com")
        self.assertEqual(ChatRoom.objects.count(), 1)
        async_to_sync(self.disconnect)(communicator)

    def test_connect_allows_guest_when_anonymous_is_enabled(self):
        communicator, connected, _ = async_to_sync(self.connect)(
            "&device=device-guest"
        )

        self.assertTrue(connected)
        participant = Participant.objects.get(user=self.user)
        self.assertEqual(participant.name, "Guest")
        self.assertEqual(ChatRoom.objects.count(), 1)
        async_to_sync(self.disconnect)(communicator)

    def test_connect_rejects_inactive_key(self):
        self.customer_key.is_active = False
        self.customer_key.save(update_fields=["is_active"])

        communicator, connected, _ = async_to_sync(self.connect)(
            "&device=device-guest"
        )

        self.assertFalse(connected)
        self.assertEqual(Participant.objects.count(), 0)
        self.assertEqual(ChatRoom.objects.count(), 0)
        async_to_sync(self.wait_for_close)(communicator)
