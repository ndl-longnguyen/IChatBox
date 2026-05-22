from django.test import TestCase
from django.urls import reverse

from chat.models import ChatMessage, ChatRoom
from users.models import Participant, User


class WidgetHistoryTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create(
            username="user-a",
            first_name="User",
            last_name="A",
        )
        self.key_a = self.user_a.customer_key

        self.user_b = User.objects.create(
            username="user-b",
            first_name="User",
            last_name="B",
        )
        self.key_b = self.user_b.customer_key

        self.participant_a = Participant.objects.create(
            user=self.user_a,
            device="device-1",
            name="Visitor A",
            email="a@example.com",
        )
        self.room_a = ChatRoom.objects.create(
            user=self.user_a,
            participant=self.participant_a,
            customer_key=self.key_a,
        )
        ChatMessage.objects.create(
            chat_room=self.room_a,
            sender_type="PARTICIPANT",
            content="Hello",
        )

    def test_requires_token_and_device(self):
        resp = self.client.get(reverse("widget_history"))
        self.assertEqual(resp.status_code, 400)

    def test_returns_empty_for_unknown_device(self):
        resp = self.client.get(
            reverse("widget_history"),
            {"token": str(self.key_a.key), "device": "unknown-device"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["messages"], [])

    def test_isolated_per_token(self):
        # user_b key should not see user_a chat history even with the same device id.
        resp = self.client.get(
            reverse("widget_history"),
            {"token": str(self.key_b.key), "device": "device-1"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["messages"], [])

        resp = self.client.get(
            reverse("widget_history"),
            {"token": str(self.key_a.key), "device": "device-1"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["message"], "Hello")

    def test_inactive_key_returns_generic_not_found(self):
        self.key_a.is_active = False
        self.key_a.save(update_fields=["is_active"])

        resp = self.client.get(
            reverse("widget_history"),
            {"token": str(self.key_a.key), "device": "device-1"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_history_limit_enforced(self):
        self.key_a.history_limit = 1
        self.key_a.save(update_fields=["history_limit"])
        ChatMessage.objects.create(
            chat_room=self.room_a,
            sender_type="PARTICIPANT",
            content="Second",
        )

        resp = self.client.get(
            reverse("widget_history"),
            {"token": str(self.key_a.key), "device": "device-1", "limit": 50},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["message"], "Second")

    def test_widget_history_supports_cursor_pagination(self):
        second = ChatMessage.objects.create(
            chat_room=self.room_a,
            sender_type="PARTICIPANT",
            content="Second",
        )

        resp = self.client.get(
            reverse("widget_history"),
            {"token": str(self.key_a.key), "device": "device-1", "limit": 1},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["has_more"])
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["message"], "Second")
        self.assertEqual(payload["next_cursor"], payload["messages"][0]["id"])

        cursor = payload["next_cursor"]
        resp2 = self.client.get(
            reverse("widget_history"),
            {
                "token": str(self.key_a.key),
                "device": "device-1",
                "limit": 1,
                "before": cursor,
            },
        )
        self.assertEqual(resp2.status_code, 200)
        payload2 = resp2.json()
        self.assertFalse(payload2["has_more"])
        self.assertEqual(len(payload2["messages"]), 1)
        self.assertEqual(payload2["messages"][0]["message"], "Hello")

    def test_room_history_requires_login(self):
        resp = self.client.get(
            reverse("room_history"),
            {"room": str(self.room_a.id), "limit": 10},
        )
        self.assertEqual(resp.status_code, 302)

    def test_room_history_pagination(self):
        self.client.force_login(self.user_a)
        first = ChatMessage.objects.create(
            chat_room=self.room_a,
            sender_type="PARTICIPANT",
            content="First",
        )
        second = ChatMessage.objects.create(
            chat_room=self.room_a,
            sender_type="USER",
            content="Second",
        )

        resp = self.client.get(
            reverse("room_history"),
            {"room": str(self.room_a.id), "limit": 1},
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["has_more"])
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["message"], "Second")

        cursor = payload["next_cursor"]
        resp2 = self.client.get(
            reverse("room_history"),
            {"room": str(self.room_a.id), "limit": 1, "before": cursor},
        )
        self.assertEqual(resp2.status_code, 200)
        payload2 = resp2.json()
        self.assertTrue(payload2["has_more"])
        self.assertEqual(len(payload2["messages"]), 1)
        self.assertEqual(payload2["messages"][0]["message"], "First")

        cursor2 = payload2["next_cursor"]
        resp3 = self.client.get(
            reverse("room_history"),
            {"room": str(self.room_a.id), "limit": 1, "before": cursor2},
        )
        self.assertEqual(resp3.status_code, 200)
        payload3 = resp3.json()
        self.assertFalse(payload3["has_more"])
        self.assertEqual(len(payload3["messages"]), 1)
        self.assertEqual(payload3["messages"][0]["message"], "Hello")
