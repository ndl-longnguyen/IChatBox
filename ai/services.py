import asyncio
import hashlib
import json
import logging
import re
import socket
import unicodedata
import urllib.error
import urllib.request
from random import Random

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from ai.models import (
    AISettings,
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
    TrainingJob,
)
from chat.models import ChatMessage, ChatRoom

logger = logging.getLogger(__name__)
_rng = Random(0)


SUPPORTED_FILE_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json"}

SEARCH_STOPWORDS = {
    "ban",
    "biet",
    "cho",
    "cua",
    "hay",
    "toi",
    "ve",
    "about",
    "and",
    "for",
    "from",
    "the",
    "your",
}

SEARCH_SYNONYMS = {
    "cong ty": ["company", "business", "organization"],
    "thong tin": ["information", "overview", "profile"],
    "du an": ["project", "projects", "portfolio"],
    "san pham": ["product", "products"],
    "dich vu": ["service", "services", "solution", "solutions"],
    "gia": ["price", "pricing", "cost", "fee"],
    "bang gia": ["pricing", "price list", "plan", "plans"],
}


def get_or_create_ai_settings(user):
    settings_obj, _ = AISettings.objects.get_or_create(user=user)
    return settings_obj


def get_or_create_default_knowledge_base(user):
    knowledge_base = (
        KnowledgeBase.objects.filter(user=user, is_active=True)
        .order_by("id")
        .first()
    )
    if knowledge_base:
        return knowledge_base
    return KnowledgeBase.objects.create(
        user=user,
        name="Default",
        language=getattr(get_or_create_ai_settings(user), "language", "vi"),
        is_active=True,
    )


def _content_hash(content):
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


def _clean_text(content):
    return re.sub(r"\s+", " ", (content or "")).strip()


def _normalize_search_text(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return without_accents.lower()


def _normalize_user_text(value):
    return re.sub(r"\s+", " ", (value or "").strip())


def _tokenize_user_text(value):
    normalized = _normalize_search_text(value)
    return re.findall(r"[a-z0-9]+", normalized)


def _is_greeting_message(message):
    normalized = _normalize_search_text(message)
    return any(
        phrase in normalized
        for phrase in [
            "xin chao",
            "chao",
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
    )


def _is_meaningless_message(message):
    text = _normalize_user_text(message)
    if not text:
        return True
    if len(text) <= 3:
        return True
    if re.fullmatch(r"[\W_]+", text):
        return True
    if re.fullmatch(r"(ha|haha|hihi|kk|lol)+", _normalize_search_text(text)):
        return True
    tokens = _tokenize_user_text(text)
    # Very short with no meaningful tokens.
    return len(tokens) <= 1 and len(text) <= 10


def _is_vague_question(message):
    normalized = _normalize_search_text(message)
    tokens = _tokenize_user_text(message)
    if len(tokens) <= 3:
        return True
    if any(
        phrase in normalized
        for phrase in [
            "giup",
            "tu van",
            "hoi",
            "thong tin",
            "ban co the",
            "co ai",
            "support",
            "help",
        ]
    ):
        return True
    return False


def build_general_assistant_reply(visitor_message, language="vi"):
    message = _normalize_user_text(visitor_message)
    if _is_greeting_message(message):
        if language == "vi":
            return "Xin chào. Mình có thể hỗ trợ bạn vấn đề gì ạ?"
        return "Hello. How can I help you today?"

    if _is_meaningless_message(message) or _is_vague_question(message):
        vi_options = [
            "Mình chưa rõ bạn đang cần hỗ trợ vấn đề gì. Bạn mô tả cụ thể hơn giúp mình được không ạ?",
            "Bạn vui lòng gửi lại câu hỏi rõ hơn (ví dụ: bạn quan tâm sản phẩm nào, nhu cầu gì, hoặc bạn đang gặp lỗi gì) để mình hỗ trợ nhanh hơn nhé.",
            "Mình chưa nắm đủ thông tin. Bạn cho mình biết mục tiêu của bạn là gì và bạn đang ở bước nào được không ạ?",
        ]
        en_options = [
            "I’m not sure what you mean yet. Could you clarify what you need help with?",
            "Could you restate your question with a bit more detail (what you’re trying to do, and what’s not working)?",
            "I don’t have enough context. Tell me your goal and where you’re stuck, and I’ll help.",
        ]
        options = vi_options if language == "vi" else en_options
        return options[_rng.randrange(len(options))]

    if language == "vi":
        return "Bạn cho mình biết thêm chi tiết (bối cảnh và yêu cầu cụ thể) để mình hỗ trợ chính xác nhé."
    return "Please share a bit more detail (context and what you need) so I can help accurately."


def _flatten_json_value(value, prefix=""):
    lines = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            lines.extend(_flatten_json_value(nested_value, label))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value, start=1):
            label = f"{prefix} #{index}" if prefix else f"item #{index}"
            lines.extend(_flatten_json_value(nested_value, label))
    elif value is not None:
        label = prefix.replace("_", " ").replace(".", " / ")
        lines.append(f"{label}: {value}")
    return lines


def normalize_knowledge_content(content):
    raw_content = (content or "").strip()
    if not raw_content:
        return ""

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        return raw_content

    lines = _flatten_json_value(parsed)
    if not lines:
        return raw_content
    return "\n".join(lines)


def split_text_into_chunks(content, chunk_size=None, overlap=None):
    normalized = _clean_text(content)
    if not normalized:
        return []

    chunk_size = chunk_size or getattr(
        settings, "AI_KNOWLEDGE_CHUNK_SIZE", 1200
    )
    overlap = overlap or getattr(settings, "AI_KNOWLEDGE_CHUNK_OVERLAP", 160)
    chunk_size = max(300, int(chunk_size))
    overlap = max(0, min(int(overlap), chunk_size // 2))

    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(
            {
                "content": normalized[start:end].strip(),
                "char_start": start,
                "char_end": end,
            }
        )
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk["content"]]


def train_document(document):
    started_at = timezone.now()
    job = TrainingJob.objects.create(
        knowledge_base=document.knowledge_base,
        status="RUNNING",
        started_at=started_at,
    )
    try:
        index_content = normalize_knowledge_content(document.content)
        chunks = split_text_into_chunks(index_content)
        KnowledgeChunk.objects.filter(document=document).delete()
        KnowledgeChunk.objects.bulk_create(
            [
                KnowledgeChunk(
                    document=document,
                    chunk_index=index,
                    content=chunk["content"],
                    content_hash=_content_hash(chunk["content"]),
                    char_start=chunk["char_start"],
                    char_end=chunk["char_end"],
                )
                for index, chunk in enumerate(chunks)
            ]
        )
        document.content_hash = _content_hash(document.content)
        document.status = "READY" if chunks else "DRAFT"
        document.save(update_fields=["content_hash", "status", "updated_at"])
        job.status = "SUCCEEDED"
    except Exception as exc:
        logger.exception("Failed to train knowledge document %s", document.pk)
        document.status = "DRAFT"
        document.save(update_fields=["status", "updated_at"])
        job.status = "FAILED"
        job.error_message = str(exc)
    finally:
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
    return job


def create_manual_knowledge_document(user, title, content, language="vi"):
    knowledge_base = get_or_create_default_knowledge_base(user)
    document = KnowledgeDocument.objects.create(
        knowledge_base=knowledge_base,
        title=(title or "Manual knowledge").strip(),
        content=content.strip(),
        content_hash=_content_hash(content),
        source="manual",
        language=language or knowledge_base.language,
        status="DRAFT",
    )
    train_document(document)
    return document


def extract_text_from_upload(uploaded_file):
    filename = uploaded_file.name or "knowledge.txt"
    extension = (
        "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    )
    if extension not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError("Supported files: .txt, .md, .markdown, .csv, .json")

    max_bytes = getattr(
        settings, "AI_KNOWLEDGE_UPLOAD_MAX_BYTES", 2 * 1024 * 1024
    )
    content_bytes = uploaded_file.read(max_bytes + 1)
    if len(content_bytes) > max_bytes:
        raise ValueError("Knowledge file is too large.")

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = content_bytes.decode("latin-1")

    if extension == ".json":
        json.loads(content)
    return content


def create_file_knowledge_document(
    user, uploaded_file, title="", language="vi"
):
    content = extract_text_from_upload(uploaded_file)
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)

    knowledge_base = get_or_create_default_knowledge_base(user)
    document = KnowledgeDocument.objects.create(
        knowledge_base=knowledge_base,
        title=(title or uploaded_file.name or "Uploaded knowledge").strip(),
        content=content.strip(),
        content_hash=_content_hash(content),
        source="file",
        source_file=uploaded_file,
        language=language or knowledge_base.language,
        status="DRAFT",
    )
    train_document(document)
    return document


def delete_knowledge_document(user, document_id):
    document = (
        KnowledgeDocument.objects.filter(
            id=document_id,
            knowledge_base__user=user,
        )
        .select_related("knowledge_base")
        .first()
    )
    if not document:
        return False

    source_file = document.source_file
    document.delete()
    if source_file:
        source_file.delete(save=False)
    return True


def _keywords(query):
    normalized_query = _normalize_search_text(query)
    words = re.findall(r"[a-z0-9]+", normalized_query)
    keywords = [
        word
        for word in words
        if len(word) >= 3 and word not in SEARCH_STOPWORDS
    ]
    for phrase, synonyms in SEARCH_SYNONYMS.items():
        if phrase in normalized_query:
            keywords.extend(synonyms)
    return list(dict.fromkeys(keywords))[:16]


def _query_intents(query):
    normalized_query = _normalize_search_text(query)
    intents = set()
    if any(phrase in normalized_query for phrase in ["cong ty", "company"]):
        intents.add("company")
    if any(
        phrase in normalized_query
        for phrase in ["du an", "project", "portfolio"]
    ):
        intents.add("projects")
    if any(
        phrase in normalized_query
        for phrase in ["gia", "price", "pricing", "cost", "fee"]
    ):
        intents.add("pricing")
    return intents


def retrieve_relevant_chunks(user, query, limit=6):
    active_bases = KnowledgeBase.objects.filter(user=user, is_active=True)
    chunks = KnowledgeChunk.objects.filter(
        document__knowledge_base__in=active_bases,
        document__status="READY",
    ).select_related("document", "document__knowledge_base")

    keywords = _keywords(query)
    intents = _query_intents(query)
    if "company" in intents:
        company_chunks = chunks.filter(content__icontains="company /")
        if company_chunks.exists():
            chunks = company_chunks
    elif "projects" in intents:
        project_chunks = chunks.filter(content__icontains="projects #")
        if project_chunks.exists():
            chunks = project_chunks
    elif "pricing" in intents:
        # Prefer explicit pricing-related knowledge; avoid matching "company"/"type" noise.
        pricing_chunks = chunks.filter(
            Q(content__icontains="pricing /")
            | Q(content__icontains="price:")
            | Q(content__icontains="gia:")
            | Q(content__icontains="bang gia")
            | Q(content__icontains="price list")
        )
        if pricing_chunks.exists():
            chunks = pricing_chunks
        else:
            return []

    if keywords:
        condition = Q()
        for keyword in keywords:
            condition |= Q(content__icontains=keyword)
            condition |= Q(document__title__icontains=keyword)
        chunks = chunks.filter(condition)

    candidates = list(
        chunks.order_by("-document__updated_at", "chunk_index")[:100]
    )
    if keywords and not candidates:
        # Fall back to the latest ready chunks from active bases if keyword search is too strict.
        candidates = list(
            KnowledgeChunk.objects.filter(
                document__knowledge_base__in=active_bases,
                document__status="READY",
            )
            .select_related("document", "document__knowledge_base")
            .order_by("-document__updated_at", "chunk_index")[:100]
        )
    if not keywords:
        candidates = list(
            KnowledgeChunk.objects.filter(
                document__knowledge_base__in=active_bases,
                document__status="READY",
            )
            .select_related("document", "document__knowledge_base")
            .order_by("-document__updated_at", "chunk_index")[: max(limit, 1)]
        )

    def score(chunk):
        content = _normalize_search_text(
            f"{chunk.document.title} {chunk.document.source} {chunk.content}"
        )
        return sum(content.count(keyword) for keyword in keywords)

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked[: max(1, int(limit or 6))]


def build_prompt(visitor_message, chunks, ai_settings):
    context = "\n\n".join(
        f"Knowledge [{index + 1}] - {chunk.document.title}:\n{chunk.content}"
        for index, chunk in enumerate(chunks)
    )
    language = ai_settings.language or "vi"
    return f"""{ai_settings.system_prompt}

You are a customer support assistant. Use only the Business knowledge below to answer the visitor's question.
- Do not invent company names, phone numbers, emails, addresses, technologies, or policies.
- If the Business knowledge does not contain the answer, say you do not have enough information and ask the visitor to wait for a human agent.
- Prefer exact names and facts from the Business knowledge.
- Answer in the requested language and keep the tone natural and conversational.
- Do not repeat raw chunk labels, indexes, or internal metadata in your reply.

Language: {language}

Business knowledge:
{context}

Visitor message:
{visitor_message}

Answer directly as a support agent. Keep it concise and practical. Use no more than 4 sentences."""


def _parse_prefixed_fields(content, prefix):
    text = f" {content or ''}"
    next_prefix_pattern = (
        rf" (?:(?:{re.escape(prefix)} / )|(?:projects #\d+ / ))"
    )
    pattern = re.compile(
        rf" {re.escape(prefix)} / ([^:]+): (.*?)(?={next_prefix_pattern}|\Z)",
        flags=re.IGNORECASE,
    )
    fields = {}
    for label, value in pattern.findall(text):
        normalized_label = label.strip().lower()
        fields.setdefault(normalized_label, []).append(value.strip())
    return fields


def _join_values(values):
    return ", ".join(value for value in values if value)


def _as_sentence(text):
    text = (text or "").strip()
    if not text:
        return ""
    return text if text.endswith((".", "!", "?")) else f"{text}."


def build_structured_reply(visitor_message, chunks, ai_settings):
    intents = _query_intents(visitor_message)
    if "pricing" in intents:
        products = []
        for chunk in chunks:
            text = f" {chunk.content or ''}"
            for match in re.finditer(
                r" products #(?P<idx>\d+) / (?P<body>.*?)(?= products #\d+ /|\Z)",
                text,
                flags=re.IGNORECASE,
            ):
                body = match.group("body")
                name_match = (
                    re.search(
                        r"name / vi: (?P<name>.*?)(?= [a-z0-9_ /#]+: |\Z)",
                        body,
                        flags=re.IGNORECASE,
                    )
                    or re.search(
                        r"name / en: (?P<name>.*?)(?= [a-z0-9_ /#]+: |\Z)",
                        body,
                        flags=re.IGNORECASE,
                    )
                    or re.search(
                        r"name: (?P<name>.*?)(?= [a-z0-9_ /#]+: |\Z)",
                        body,
                        flags=re.IGNORECASE,
                    )
                )

                price_match = re.search(
                    r"price(?: / [a-z]{2})?: (?P<price>.*?)(?= [a-z0-9_ /#]+: |\Z)",
                    body,
                    flags=re.IGNORECASE,
                )

                if not price_match:
                    continue

                raw_price = (price_match.group("price") or "").strip()
                digits = re.sub(r"[^\d]", "", raw_price)
                if not digits:
                    continue

                try:
                    price_value = int(digits)
                except ValueError:
                    continue

                products.append(
                    {
                        "name": (
                            name_match.group("name").strip()
                            if name_match
                            else ""
                        ),
                        "price": price_value,
                        "raw_price": raw_price,
                    }
                )

        if not products:
            return None

        most_expensive = max(products, key=lambda item: item["price"])
        language = ai_settings.language or "vi"
        name = most_expensive["name"] or "sản phẩm"
        raw_price = most_expensive["raw_price"] or str(most_expensive["price"])
        if language == "vi":
            return f"Giá cao nhất hiện có là {raw_price} cho {name}."
        return f"The highest listed price is {raw_price} for {name}."

    if "company" not in intents:
        return None

    fields = {}
    for chunk in chunks:
        for label, values in _parse_prefixed_fields(
            chunk.content, "company"
        ).items():
            fields.setdefault(label, []).extend(values)

    if not fields.get("name"):
        return None

    name = fields["name"][0]
    language = ai_settings.language or "vi"
    services = _join_values(
        value
        for label, values in fields.items()
        if label.startswith("services")
        for value in values
    )
    strengths = _join_values(
        value
        for label, values in fields.items()
        if label.startswith("strengths")
        for value in values[:1]
    )
    stats = []
    stat_labels = {
        "projects": "dự án",
        "clients": "khách hàng",
        "countries": "quốc gia",
    }
    for label, values in fields.items():
        if label.startswith("stats"):
            stat_key = label.replace("stats / ", "")
            stats.append(f"{values[0]} {stat_labels.get(stat_key, stat_key)}")
    contacts = []
    contact_labels = {
        "contact / phone": "điện thoại",
        "contact / email": "email",
        "contact / website": "website",
        "contact / address": "địa chỉ",
    }
    for key in contact_labels:
        if fields.get(key):
            contacts.append(f"{contact_labels[key]}: {fields[key][0]}")

    if language == "vi":
        lines = [_as_sentence(f"Công ty là {name}")]
        if fields.get("slogan"):
            lines.append(_as_sentence(f"Định hướng: {fields['slogan'][0]}"))
        if services:
            lines.append(_as_sentence(f"Dịch vụ chính: {services}"))
        if strengths:
            lines.append(_as_sentence(f"Thế mạnh nổi bật: {strengths}"))
        if stats:
            lines.append(_as_sentence(f"Số liệu: {', '.join(stats)}"))
        if contacts:
            lines.append(_as_sentence(f"Liên hệ: {', '.join(contacts)}"))
        return " ".join(lines)

    lines = [_as_sentence(f"The company is {name}")]
    if fields.get("slogan"):
        lines.append(_as_sentence(f"Positioning: {fields['slogan'][0]}"))
    if services:
        lines.append(_as_sentence(f"Main services: {services}"))
    if strengths:
        lines.append(_as_sentence(f"Key strengths: {strengths}"))
    if stats:
        lines.append(_as_sentence(f"Stats: {', '.join(stats)}"))
    if contacts:
        lines.append(_as_sentence(f"Contact: {', '.join(contacts)}"))
    return " ".join(lines)


def call_ollama(prompt, ai_settings):
    base_url = getattr(settings, "AI_LOCAL_BASE_URL", "http://localhost:11434")
    model_name = ai_settings.model_name or getattr(
        settings, "AI_LOCAL_MODEL", "qwen2.5:1.5b"
    )
    timeout = getattr(settings, "AI_LOCAL_TIMEOUT_SECONDS", 30)
    max_tokens = getattr(settings, "AI_LOCAL_MAX_TOKENS", 160)
    num_ctx = getattr(settings, "AI_LOCAL_NUM_CTX", 1024)
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": ai_settings.temperature,
            "num_predict": max(32, int(max_tokens)),
            "num_ctx": max(512, int(num_ctx)),
        },
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    return (response_payload.get("response") or "").strip()


async def call_ollama_async(prompt, ai_settings):
    return await asyncio.to_thread(call_ollama, prompt, ai_settings)


def generate_auto_reply(chat_room_id, visitor_message):
    room = ChatRoom.objects.select_related("user").get(id=chat_room_id)
    ai_settings = get_or_create_ai_settings(room.user)
    if not ai_settings.auto_reply_enabled:
        return None

    language = ai_settings.language or "vi"
    if _is_meaningless_message(visitor_message) or _is_vague_question(
        visitor_message
    ):
        return build_general_assistant_reply(visitor_message, language=language)

    chunks = retrieve_relevant_chunks(
        room.user,
        visitor_message,
        limit=ai_settings.max_context_chunks,
    )
    if not chunks:
        # No relevant knowledge: respond naturally but do not invent business facts.
        intents = _query_intents(visitor_message)
        if "pricing" in intents:
            if language == "vi":
                return (
                    "Mình chưa có đủ dữ liệu bảng giá/sản phẩm để trả lời chính xác. "
                    "Bạn vui lòng cho biết bạn quan tâm sản phẩm nào hoặc chờ nhân viên hỗ trợ."
                )
            return (
                "I don't have enough pricing/product data to answer accurately. "
                "Please tell me which product you mean, or wait for a human agent."
            )
        return build_general_assistant_reply(visitor_message, language=language)

    prompt = build_prompt(visitor_message, chunks, ai_settings)
    try:
        reply = call_ollama(prompt, ai_settings)
    except (
        urllib.error.URLError,
        TimeoutError,
        socket.timeout,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        logger.warning(
            "Local AI auto-reply failed for room %s: %s", room.pk, exc
        )
        return None

    if reply:
        return reply[:4000]
    return build_general_assistant_reply(visitor_message, language=language)


def save_ai_reply(chat_room_id, reply):
    return ChatMessage.objects.create(
        chat_room_id=chat_room_id,
        sender_type="USER",
        content=reply,
    )
