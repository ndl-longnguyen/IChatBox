from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from ai.models import KnowledgeChunk, KnowledgeDocument
from ai.services import (
    build_structured_reply,
    create_manual_knowledge_document,
    delete_knowledge_document,
    normalize_knowledge_content,
)
from users.models import User


class KnowledgeParsingTests(SimpleTestCase):
    def test_normalize_json_knowledge_content_flattens_nested_values(self):
        content = """
        {
          "company": {
            "name": "SOARIG VIETNAM Co., Ltd.",
            "contact": {"email": "info@soarig.vn"}
          }
        }
        """

        normalized = normalize_knowledge_content(content)

        self.assertIn("company / name: SOARIG VIETNAM Co., Ltd.", normalized)
        self.assertIn("company / contact / email: info@soarig.vn", normalized)

    def test_structured_company_reply_uses_context_values(self):
        chunk = SimpleNamespace(
            content=(
                "company / name: SOARIG VIETNAM Co., Ltd. "
                "company / services #1: Mobile App Development "
                "company / contact / email: info@soarig.vn"
            )
        )
        ai_settings = SimpleNamespace(language="vi")

        reply = build_structured_reply(
            "cho tôi biết thông tin công ty của bạn",
            [chunk],
            ai_settings,
        )

        self.assertIn("SOARIG VIETNAM Co., Ltd.", reply)
        self.assertIn("Mobile App Development", reply)
        self.assertIn("info@soarig.vn", reply)
        self.assertNotIn("support@companyname.com", reply)


class KnowledgeDeletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="tenant-a",
            first_name="Tenant",
            last_name="A",
        )
        self.other_user = User.objects.create(
            username="tenant-b",
            first_name="Tenant",
            last_name="B",
        )

    def test_delete_knowledge_document_cascades_chunks_for_owner(self):
        document = create_manual_knowledge_document(
            self.user,
            "Company info",
            "SOARIG VIETNAM Co., Ltd. provides IT/DX solutions.",
        )

        self.assertTrue(
            KnowledgeChunk.objects.filter(document=document).exists()
        )

        deleted = delete_knowledge_document(self.user, document.id)

        self.assertTrue(deleted)
        self.assertFalse(
            KnowledgeDocument.objects.filter(id=document.id).exists()
        )
        self.assertFalse(
            KnowledgeChunk.objects.filter(document_id=document.id).exists()
        )

    def test_delete_knowledge_document_does_not_cross_tenants(self):
        document = create_manual_knowledge_document(
            self.user,
            "Company info",
            "Tenant A private knowledge.",
        )

        deleted = delete_knowledge_document(self.other_user, document.id)

        self.assertFalse(deleted)
        self.assertTrue(
            KnowledgeDocument.objects.filter(id=document.id).exists()
        )
