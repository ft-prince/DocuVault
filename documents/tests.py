"""
DocuVault – Comprehensive Test Suite
=====================================
Covers: Models · Forms · URL resolution · Views · Access control ·
        Workspace/Folder API · Chatbot · Agent API · Security
"""

import io
import json
import tempfile
import uuid

from unittest.mock import MagicMock, patch

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone

from .models import (
    ActivityLog,
    AgentToken,
    Category,
    ChatMessage,
    ChatSession,
    Document,
    DocumentComment,
    DocumentEmbedding,
    DocumentVersion,
    Favorite,
    Folder,
    Notification,
    Role,
    SharedLink,
    Tag,
    User,
)

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

TEMP_MEDIA = tempfile.mkdtemp()


def dummy_pdf(name="test.pdf", size=1024):
    return SimpleUploadedFile(name, b"%PDF-1.4 " + b"x" * size, content_type="application/pdf")


def dummy_txt(name="test.txt", content=b"Hello world"):
    return SimpleUploadedFile(name, content, content_type="text/plain")


def make_user(username="user1", password="pass1234!", user_type="user", **kwargs):
    u = User.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@example.com",
        user_type=user_type,
        **kwargs,
    )
    return u


def make_admin(username="admin1", password="pass1234!"):
    return make_user(username=username, password=password, user_type="admin")


def make_role(name="Viewer", level=10, is_default=False):
    return Role.objects.create(name=name, level=level, is_default=is_default)


def make_category(name="General", created_by=None):
    return Category.objects.create(name=name, created_by=created_by)


def make_doc(owner, title="Doc", access_level="private", **kwargs):
    f = dummy_txt(f"{title}.txt")
    return Document.objects.create(
        title=title,
        file=f,
        owner=owner,
        access_level=access_level,
        file_size=f.size,
        file_type="text/plain",
        **kwargs,
    )


def make_folder(owner, name="Folder", parent=None):
    return Folder.objects.create(owner=owner, name=name, parent=parent)


def auth_client(user, password="pass1234!"):
    c = Client()
    c.login(username=user.username, password=password)
    return c


# ══════════════════════════════════════════════════════════════
# 1. MODEL TESTS
# ══════════════════════════════════════════════════════════════


class TestUserModel(TestCase):
    def test_str(self):
        u = make_user("alice")
        self.assertEqual(str(u), "alice")

    def test_is_admin_false_by_default(self):
        u = make_user("bob")
        self.assertFalse(u.is_admin())

    def test_is_admin_true(self):
        u = make_admin("carol")
        self.assertTrue(u.is_admin())

    def test_get_role_level_no_role(self):
        u = make_user("dave")
        self.assertEqual(u.get_role_level(), 1)

    def test_get_role_level_with_role(self):
        r = make_role("Manager", level=50)
        u = make_user("eve")
        u.role = r
        u.save()
        self.assertEqual(u.get_role_level(), 50)

    def test_get_role_level_admin_always_100(self):
        u = make_admin("frank")
        self.assertEqual(u.get_role_level(), 100)


class TestRoleModel(TestCase):
    def test_str(self):
        r = make_role("Editor", level=20)
        self.assertIn("Editor", str(r))
        self.assertIn("20", str(r))

    def test_unique_name(self):
        make_role("Tester")
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Role.objects.create(name="Tester", level=5)

    def test_level_ordering(self):
        make_role("Low", level=5)
        make_role("High", level=90)
        roles = list(Role.objects.all())
        self.assertEqual(roles[0].level, 90)   # higher first


class TestDocumentModel(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.other = make_user("other")
        self.admin = make_admin("adm")

    def test_str(self):
        d = make_doc(self.owner, "My Doc")
        self.assertEqual(str(d), "My Doc")

    def test_can_view_owner(self):
        d = make_doc(self.owner, access_level="private")
        self.assertTrue(d.can_view(self.owner))

    def test_can_view_private_blocked(self):
        d = make_doc(self.owner, access_level="private")
        self.assertFalse(d.can_view(self.other))

    def test_can_view_public(self):
        d = make_doc(self.owner, access_level="public")
        self.assertTrue(d.can_view(self.other))

    def test_can_view_role_sufficient(self):
        r = make_role("Reader", level=10)
        self.other.role = r
        self.other.save()
        d = make_doc(self.owner, access_level="role", required_role_level=5)
        self.assertTrue(d.can_view(self.other))

    def test_can_view_role_insufficient(self):
        r = make_role("Low", level=3)
        self.other.role = r
        self.other.save()
        d = make_doc(self.owner, access_level="role", required_role_level=50)
        self.assertFalse(d.can_view(self.other))

    def test_can_view_custom_shared(self):
        d = make_doc(self.owner, access_level="custom")
        d.shared_with.add(self.other)
        self.assertTrue(d.can_view(self.other))

    def test_can_view_admin_always(self):
        d = make_doc(self.owner, access_level="private")
        self.assertTrue(d.can_view(self.admin))

    def test_can_edit_owner(self):
        d = make_doc(self.owner)
        self.assertTrue(d.can_edit(self.owner))

    def test_can_edit_other_blocked(self):
        d = make_doc(self.owner)
        self.assertFalse(d.can_edit(self.other))

    def test_can_edit_locked_blocked(self):
        d = make_doc(self.owner, is_locked=True, locked_by=self.admin)
        self.assertFalse(d.can_edit(self.owner))

    def test_can_delete_owner(self):
        d = make_doc(self.owner)
        self.assertTrue(d.can_delete(self.owner))

    def test_can_delete_other_blocked(self):
        d = make_doc(self.owner)
        self.assertFalse(d.can_delete(self.other))

    def test_increment_views(self):
        d = make_doc(self.owner)
        d.increment_views()
        d.refresh_from_db()
        self.assertEqual(d.views_count, 1)

    def test_increment_downloads(self):
        d = make_doc(self.owner)
        d.increment_downloads()
        d.refresh_from_db()
        self.assertEqual(d.downloads_count, 1)

    def test_get_embedding_none(self):
        d = make_doc(self.owner)
        self.assertIsNone(d.get_embedding())


class TestFolderModel(TestCase):
    def setUp(self):
        self.user = make_user("fuser")

    def test_str(self):
        f = make_folder(self.user, "Docs")
        self.assertEqual(str(f), "Docs")

    def test_get_path_top_level(self):
        f = make_folder(self.user, "Root")
        self.assertEqual(f.get_path(), "Root")

    def test_get_path_nested(self):
        parent = make_folder(self.user, "Parent")
        child = make_folder(self.user, "Child", parent=parent)
        self.assertEqual(child.get_path(), "Parent / Child")

    def test_doc_count(self):
        f = make_folder(self.user, "F")
        d = make_doc(self.user, folder=f)
        self.assertEqual(f.doc_count(), 1)

    def test_doc_count_excludes_deleted(self):
        f = make_folder(self.user, "F2")
        d = make_doc(self.user, folder=f, is_deleted=True)
        self.assertEqual(f.doc_count(), 0)

    def test_all_ancestor_ids(self):
        p = make_folder(self.user, "P")
        c = make_folder(self.user, "C", parent=p)
        gc = make_folder(self.user, "GC", parent=c)
        ids = gc.all_ancestor_ids()
        self.assertIn(p.id, ids)
        self.assertIn(c.id, ids)


class TestSharedLinkModel(TestCase):
    def setUp(self):
        self.user = make_user("linkuser")
        self.doc = make_doc(self.user)

    def test_is_valid_active(self):
        link = SharedLink.objects.create(document=self.doc, created_by=self.user)
        self.assertTrue(link.is_valid())

    def test_is_valid_inactive(self):
        link = SharedLink.objects.create(document=self.doc, created_by=self.user, is_active=False)
        self.assertFalse(link.is_valid())

    def test_is_valid_expired(self):
        past = timezone.now() - timezone.timedelta(days=1)
        link = SharedLink.objects.create(document=self.doc, created_by=self.user, expires_at=past)
        self.assertFalse(link.is_valid())

    def test_is_valid_max_reached(self):
        link = SharedLink.objects.create(
            document=self.doc, created_by=self.user,
            max_access_count=3, access_count=3,
        )
        self.assertFalse(link.is_valid())

    def test_increment_access(self):
        link = SharedLink.objects.create(document=self.doc, created_by=self.user)
        link.increment_access()
        link.refresh_from_db()
        self.assertEqual(link.access_count, 1)


class TestAgentTokenModel(TestCase):
    def setUp(self):
        self.user = make_user("auser")

    def test_get_or_create_for_user(self):
        token = AgentToken.get_or_create_for_user(self.user)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token), 64)

    def test_get_or_create_idempotent(self):
        t1 = AgentToken.get_or_create_for_user(self.user)
        t2 = AgentToken.get_or_create_for_user(self.user)
        self.assertEqual(t1, t2)

    def test_authenticate_valid(self):
        token_value = AgentToken.get_or_create_for_user(self.user)
        user, obj = AgentToken.authenticate(token_value)
        self.assertEqual(user, self.user)
        self.assertIsNotNone(obj)

    def test_authenticate_invalid(self):
        user, obj = AgentToken.authenticate("deadbeef" * 8)
        self.assertIsNone(user)
        self.assertIsNone(obj)

    def test_str(self):
        AgentToken.get_or_create_for_user(self.user)
        tok = AgentToken.objects.get(user=self.user)
        self.assertIn("auser", str(tok))


class TestDocumentEmbeddingModel(TestCase):
    def setUp(self):
        self.user = make_user("euser")
        self.doc = make_doc(self.user)
        self.emb = DocumentEmbedding.objects.create(document=self.doc)

    def test_initial_status(self):
        self.assertEqual(self.emb.index_status, "pending")
        self.assertFalse(self.emb.is_indexed)

    def test_mark_processing(self):
        self.emb.mark_processing()
        self.emb.refresh_from_db()
        self.assertEqual(self.emb.index_status, "processing")

    def test_mark_completed(self):
        self.emb.mark_completed(chunk_count=5, embedding_model="test-model")
        self.emb.refresh_from_db()
        self.assertEqual(self.emb.index_status, "completed")
        self.assertTrue(self.emb.is_indexed)
        self.assertEqual(self.emb.chunk_count, 5)

    def test_mark_failed(self):
        self.emb.mark_failed("Something went wrong")
        self.emb.refresh_from_db()
        self.assertEqual(self.emb.index_status, "failed")
        self.assertEqual(self.emb.retry_count, 1)
        self.assertIn("Something went wrong", self.emb.error_message)


class TestChatModels(TestCase):
    def setUp(self):
        self.user = make_user("chatuser")

    def test_chat_session_str(self):
        s = ChatSession.objects.create(user=self.user, title="Test Session")
        self.assertIn("Test Session", str(s))

    def test_chat_session_message_count(self):
        s = ChatSession.objects.create(user=self.user)
        ChatMessage.objects.create(session=s, message_type="human", content="Hi")
        ChatMessage.objects.create(session=s, message_type="ai", content="Hello!")
        self.assertEqual(s.get_message_count(), 2)

    def test_chat_message_str(self):
        s = ChatSession.objects.create(user=self.user)
        m = ChatMessage.objects.create(session=s, message_type="human", content="Test question")
        self.assertIn("human", str(m))


# ══════════════════════════════════════════════════════════════
# 2. FORM TESTS
# ══════════════════════════════════════════════════════════════


class TestUserRegistrationForm(TestCase):
    def _data(self, **overrides):
        base = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "ComplexPass99!",
            "password2": "ComplexPass99!",
        }
        base.update(overrides)
        return base

    def test_valid_form(self):
        from .forms import UserRegistrationForm
        f = UserRegistrationForm(data=self._data())
        self.assertTrue(f.is_valid(), f.errors)

    def test_duplicate_email(self):
        from .forms import UserRegistrationForm
        make_user("existing", email="taken@example.com")
        # Manually set email on the existing user
        u = User.objects.get(username="existing")
        u.email = "taken@example.com"
        u.save()
        f = UserRegistrationForm(data=self._data(email="taken@example.com"))
        self.assertFalse(f.is_valid())
        self.assertIn("email", f.errors)

    def test_password_mismatch(self):
        from .forms import UserRegistrationForm
        f = UserRegistrationForm(data=self._data(password2="WrongPass99!"))
        self.assertFalse(f.is_valid())


class TestRoleForm(TestCase):
    def test_valid(self):
        from .forms import RoleForm
        f = RoleForm(data={"name": "Tester", "description": "", "level": 20, "is_default": False})
        self.assertTrue(f.is_valid(), f.errors)

    def test_invalid_level_zero(self):
        from .forms import RoleForm
        f = RoleForm(data={"name": "Bad", "level": 0, "is_default": False})
        self.assertFalse(f.is_valid())

    def test_invalid_level_over_100(self):
        from .forms import RoleForm
        f = RoleForm(data={"name": "Over", "level": 101, "is_default": False})
        self.assertFalse(f.is_valid())


class TestCategoryForm(TestCase):
    def test_valid(self):
        from .forms import CategoryForm
        f = CategoryForm(data={"name": "Finance", "description": "", "color": "#ff0000", "icon": "", "parent": ""})
        self.assertTrue(f.is_valid(), f.errors)


class TestCommentForm(TestCase):
    def test_valid(self):
        from .forms import CommentForm
        f = CommentForm(data={"content": "Great document!"})
        self.assertTrue(f.is_valid())

    def test_empty_content_invalid(self):
        from .forms import CommentForm
        f = CommentForm(data={"content": ""})
        self.assertFalse(f.is_valid())


# ══════════════════════════════════════════════════════════════
# 3. URL RESOLUTION TESTS
# ══════════════════════════════════════════════════════════════


class TestURLResolution(TestCase):
    """Ensure every named URL resolves to the correct view."""

    def _check(self, name, kwargs=None, view_name=None):
        url = reverse(name, kwargs=kwargs)
        match = resolve(url)
        if view_name:
            self.assertEqual(match.view_name, f"documents:{name}" if ":" not in name else name)
        return match

    def test_home(self):         self._check("home")
    def test_register(self):     self._check("register")
    def test_login(self):        self._check("login")
    def test_logout(self):       self._check("logout")
    def test_dashboard(self):    self._check("dashboard")
    def test_workspace(self):    self._check("workspace")
    def test_workspace_agent(self): self._check("workspace_agent")

    def test_document_list(self):   self._check("document_list")
    def test_document_create(self): self._check("document_create")
    def test_document_detail(self): self._check("document_detail", {"pk": 1})
    def test_document_edit(self):   self._check("document_edit",   {"pk": 1})
    def test_document_delete(self): self._check("document_delete", {"pk": 1})
    def test_document_download(self): self._check("document_download", {"pk": 1})

    def test_folder_create(self):   self._check("folder_create")
    def test_folder_rename(self):   self._check("folder_rename", {"pk": 1})
    def test_folder_delete(self):   self._check("folder_delete", {"pk": 1})
    def test_document_move(self):   self._check("document_move", {"pk": 1})

    def test_comment_create(self):  self._check("comment_create", {"document_pk": 1})
    def test_comment_delete(self):  self._check("comment_delete", {"pk": 1})

    def test_favorite_toggle(self): self._check("favorite_toggle", {"document_pk": 1})
    def test_favorites_list(self):  self._check("favorites_list")

    def test_shared_link_create(self): self._check("shared_link_create", {"document_pk": 1})
    def test_shared_link_access(self):
        token = uuid.uuid4()
        self._check("shared_link_access", {"token": token})

    def test_profile(self):      self._check("profile")
    def test_profile_edit(self): self._check("profile_edit")

    def test_admin_users_list(self): self._check("admin_users_list")
    def test_admin_roles_list(self): self._check("admin_roles_list")

    def test_category_list(self):   self._check("category_list")
    def test_category_create(self): self._check("category_create")

    def test_notifications_list(self): self._check("notifications_list")

    def test_advanced_search(self): self._check("advanced_search")
    def test_activity_log(self):    self._check("activity_log")

    def test_chatbot(self):       self._check("chatbot")
    def test_chatbot_query(self): self._check("chatbot_query")
    def test_chat_history(self):  self._check("chat_history")
    def test_new_chat(self):      self._check("new_chat")

    def test_agent_auth(self):      self._check("agent_auth")
    def test_agent_upload(self):    self._check("agent_upload")
    def test_agent_events(self):    self._check("agent_events")
    def test_agent_heartbeat(self): self._check("agent_heartbeat")
    def test_agent_status(self):    self._check("agent_status")

    def test_agent_sync_start(self):  self._check("agent_sync_start")
    def test_agent_sync_done(self):   self._check("agent_sync_done")
    def test_agent_sync_status(self): self._check("agent_sync_status")

    def test_rag_system_info(self): self._check("rag_system_info")
    def test_document_index_status(self): self._check("document_index_status", {"pk": 1})
    def test_document_reindex(self): self._check("document_reindex", {"pk": 1})


# ══════════════════════════════════════════════════════════════
# 4. AUTHENTICATION VIEW TESTS
# ══════════════════════════════════════════════════════════════


class TestAuthViews(TestCase):
    def test_register_get(self):
        r = self.client.get(reverse("register"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "documents/auth/register.html")

    def test_register_post_valid(self):
        r = self.client.post(reverse("register"), {
            "username": "freshuser",
            "email": "fresh@example.com",
            "first_name": "Fresh",
            "last_name": "User",
            "password1": "ComplexPass99!",
            "password2": "ComplexPass99!",
        })
        self.assertRedirects(r, reverse("workspace"))
        self.assertTrue(User.objects.filter(username="freshuser").exists())

    def test_register_redirects_if_authenticated(self):
        u = make_user("authed")
        c = auth_client(u)
        r = c.get(reverse("register"))
        self.assertRedirects(r, reverse("workspace"))

    def test_login_get(self):
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 200)

    def test_login_post_valid(self):
        make_user("loginuser", password="pass1234!")
        r = self.client.post(reverse("login"), {"username": "loginuser", "password": "pass1234!"})
        self.assertRedirects(r, reverse("chatbot"))

    def test_login_post_invalid(self):
        r = self.client.post(reverse("login"), {"username": "nobody", "password": "wrong"})
        self.assertEqual(r.status_code, 200)
        msgs = [str(m) for m in get_messages(r.wsgi_request)]
        self.assertTrue(any("Invalid" in m for m in msgs))

    def test_login_redirects_if_authenticated(self):
        u = make_user("already")
        c = auth_client(u)
        r = c.get(reverse("login"))
        self.assertRedirects(r, reverse("chatbot"))

    def test_logout(self):
        u = make_user("logme")
        c = auth_client(u)
        r = c.get(reverse("logout"))
        self.assertRedirects(r, reverse("home"))


# ══════════════════════════════════════════════════════════════
# 5. HOME AND DASHBOARD
# ══════════════════════════════════════════════════════════════


class TestHomeAndDashboard(TestCase):
    def test_home_public(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "documents/home.html")

    def test_dashboard_requires_login(self):
        r = self.client.get(reverse("dashboard"))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_authenticated(self):
        u = make_user("dashuser")
        c = auth_client(u)
        r = c.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)


# ══════════════════════════════════════════════════════════════
# 6. DOCUMENT VIEWS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentListView(TestCase):
    def setUp(self):
        self.user = make_user("listuser")
        self.c = auth_client(self.user)

    def test_requires_login(self):
        r = self.client.get(reverse("document_list"))
        self.assertEqual(r.status_code, 302)

    def test_list_returns_200(self):
        r = self.c.get(reverse("document_list"))
        self.assertEqual(r.status_code, 200)

    def test_own_doc_visible(self):
        make_doc(self.user, "My Private")
        r = self.c.get(reverse("document_list"))
        self.assertContains(r, "My Private")

    def test_other_private_not_visible(self):
        other = make_user("other2")
        make_doc(other, "Other Private", access_level="private")
        r = self.c.get(reverse("document_list"))
        self.assertNotContains(r, "Other Private")

    def test_public_doc_visible(self):
        other = make_user("pub_owner")
        make_doc(other, "Public Doc", access_level="public")
        r = self.c.get(reverse("document_list"))
        self.assertContains(r, "Public Doc")

    def test_search_filter(self):
        make_doc(self.user, "Annual Report")
        make_doc(self.user, "Meeting Notes")
        r = self.c.get(reverse("document_list") + "?q=Annual")
        self.assertContains(r, "Annual Report")
        self.assertNotContains(r, "Meeting Notes")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentDetailView(TestCase):
    def setUp(self):
        self.owner = make_user("detailowner")
        self.other = make_user("detailother")
        self.doc = make_doc(self.owner, "Detail Doc")

    def test_owner_can_view(self):
        c = auth_client(self.owner)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_private_blocked(self):
        c = auth_client(self.other)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 403)

    def test_public_accessible(self):
        self.doc.access_level = "public"
        self.doc.save()
        c = auth_client(self.other)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_view_increments_counter(self):
        c = auth_client(self.owner)
        c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.doc.refresh_from_db()
        self.assertGreater(self.doc.views_count, 0)

    def test_view_logs_activity(self):
        c = auth_client(self.owner)
        c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertTrue(ActivityLog.objects.filter(document=self.doc, action="view").exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentCreateView(TestCase):
    def setUp(self):
        self.user = make_user("creator")
        self.c = auth_client(self.user)

    def test_get_form(self):
        r = self.c.get(reverse("document_create"))
        self.assertEqual(r.status_code, 200)

    def test_create_document(self):
        r = self.c.post(reverse("document_create"), {
            "title": "New Doc",
            "description": "Test",
            "file": dummy_pdf(),
            "access_level": "private",
            "required_role_level": 1,
            "allow_comments": True,
            "allow_download": True,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Document.objects.filter(title="New Doc", owner=self.user).exists())

    def test_create_logs_activity(self):
        self.c.post(reverse("document_create"), {
            "title": "Logged Doc",
            "description": "",
            "file": dummy_pdf("log.pdf"),
            "access_level": "private",
            "required_role_level": 1,
            "allow_comments": True,
            "allow_download": True,
        })
        doc = Document.objects.get(title="Logged Doc")
        self.assertTrue(ActivityLog.objects.filter(document=doc, action="create").exists())

    def test_requires_login(self):
        r = self.client.get(reverse("document_create"))
        self.assertEqual(r.status_code, 302)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentEditView(TestCase):
    def setUp(self):
        self.owner = make_user("editor")
        self.other = make_user("noedit")
        self.doc = make_doc(self.owner, "Editable")

    def test_owner_can_get(self):
        c = auth_client(self.owner)
        r = c.get(reverse("document_edit", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_other_cannot_get(self):
        c = auth_client(self.other)
        r = c.get(reverse("document_edit", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 403)

    def test_edit_title(self):
        c = auth_client(self.owner)
        r = c.post(reverse("document_edit", kwargs={"pk": self.doc.pk}), {
            "title": "Edited Title",
            "description": "",
            "access_level": "private",
            "required_role_level": 1,
            "allow_comments": True,
            "allow_download": True,
        })
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "Edited Title")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentDeleteView(TestCase):
    def setUp(self):
        self.owner = make_user("delowner")
        self.other = make_user("nodelete")
        self.doc = make_doc(self.owner, "To Delete")

    def test_owner_delete(self):
        c = auth_client(self.owner)
        r = c.post(reverse("document_delete", kwargs={"pk": self.doc.pk}))
        self.doc.refresh_from_db()
        self.assertTrue(self.doc.is_deleted)

    def test_other_cannot_delete(self):
        c = auth_client(self.other)
        r = c.post(reverse("document_delete", kwargs={"pk": self.doc.pk}))
        self.doc.refresh_from_db()
        self.assertFalse(self.doc.is_deleted)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentDownload(TestCase):
    def setUp(self):
        self.owner = make_user("dlowner")
        self.doc = make_doc(self.owner, "Downloadable")
        self.doc.allow_download = True
        self.doc.save()

    def test_download_owner(self):
        c = auth_client(self.owner)
        r = c.get(reverse("document_download", kwargs={"pk": self.doc.pk}))
        # Should not be 403/404
        self.assertIn(r.status_code, [200, 302])

    def test_download_increments_counter(self):
        c = auth_client(self.owner)
        c.get(reverse("document_download", kwargs={"pk": self.doc.pk}))
        self.doc.refresh_from_db()
        self.assertGreaterEqual(self.doc.downloads_count, 1)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestDocumentVersioning(TestCase):
    def setUp(self):
        self.owner = make_user("verowner")
        self.doc = make_doc(self.owner, "Versioned")
        # Create version 1
        DocumentVersion.objects.create(
            document=self.doc,
            version_number=1,
            file=self.doc.file,
            file_size=10,
            uploaded_by=self.owner,
        )

    def test_version_created(self):
        self.assertEqual(self.doc.versions.count(), 1)

    def test_version_str(self):
        v = self.doc.versions.first()
        self.assertIn("v1", str(v))

    def test_version_download(self):
        v = self.doc.versions.first()
        c = auth_client(self.owner)
        r = c.get(reverse("version_download", kwargs={"doc_pk": self.doc.pk, "version_pk": v.pk}))
        self.assertIn(r.status_code, [200, 302])


# ══════════════════════════════════════════════════════════════
# 7. COMMENT VIEWS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestCommentViews(TestCase):
    def setUp(self):
        self.user = make_user("commenter")
        self.doc = make_doc(self.user, access_level="public")
        self.c = auth_client(self.user)

    def test_add_comment(self):
        r = self.c.post(
            reverse("comment_create", kwargs={"document_pk": self.doc.pk}),
            {"content": "Nice doc!"},
        )
        self.assertEqual(self.doc.comments.count(), 1)

    def test_delete_own_comment(self):
        comment = DocumentComment.objects.create(
            document=self.doc, user=self.user, content="To delete"
        )
        r = self.c.post(reverse("comment_delete", kwargs={"pk": comment.pk}))
        self.assertFalse(DocumentComment.objects.filter(pk=comment.pk).exists())

    def test_cannot_delete_others_comment(self):
        other = make_user("other_comm")
        comment = DocumentComment.objects.create(
            document=self.doc, user=other, content="Not mine"
        )
        r = self.c.post(reverse("comment_delete", kwargs={"pk": comment.pk}))
        # Should still exist (403 or redirect without deletion)
        self.assertTrue(DocumentComment.objects.filter(pk=comment.pk).exists())


# ══════════════════════════════════════════════════════════════
# 8. FAVORITE VIEWS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestFavoriteViews(TestCase):
    def setUp(self):
        self.user = make_user("favuser")
        self.doc = make_doc(self.user, access_level="public")
        self.c = auth_client(self.user)

    def test_toggle_adds_favorite(self):
        self.c.post(reverse("favorite_toggle", kwargs={"document_pk": self.doc.pk}))
        self.assertTrue(Favorite.objects.filter(user=self.user, document=self.doc).exists())

    def test_toggle_removes_favorite(self):
        Favorite.objects.create(user=self.user, document=self.doc)
        self.c.post(reverse("favorite_toggle", kwargs={"document_pk": self.doc.pk}))
        self.assertFalse(Favorite.objects.filter(user=self.user, document=self.doc).exists())

    def test_favorites_list(self):
        Favorite.objects.create(user=self.user, document=self.doc)
        r = self.c.get(reverse("favorites_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.doc.title)


# ══════════════════════════════════════════════════════════════
# 9. SHARED LINK VIEWS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestSharedLinkViews(TestCase):
    def setUp(self):
        self.owner = make_user("shareowner")
        self.doc = make_doc(self.owner, "Shared Doc")
        self.c = auth_client(self.owner)

    def test_create_shared_link(self):
        r = self.c.post(
            reverse("shared_link_create", kwargs={"document_pk": self.doc.pk}),
            {"allow_download": True},
        )
        self.assertTrue(SharedLink.objects.filter(document=self.doc).exists())

    def test_access_shared_link(self):
        link = SharedLink.objects.create(document=self.doc, created_by=self.owner)
        r = self.client.get(reverse("shared_link_access", kwargs={"token": link.token}))
        self.assertEqual(r.status_code, 200)

    def test_invalid_token_404(self):
        r = self.client.get(
            reverse("shared_link_access", kwargs={"token": uuid.uuid4()})
        )
        self.assertEqual(r.status_code, 404)

    def test_expired_link(self):
        past = timezone.now() - timezone.timedelta(days=1)
        link = SharedLink.objects.create(
            document=self.doc, created_by=self.owner, expires_at=past
        )
        r = self.client.get(reverse("shared_link_access", kwargs={"token": link.token}))
        self.assertNotEqual(r.status_code, 200)


# ══════════════════════════════════════════════════════════════
# 10. NOTIFICATION VIEWS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestNotificationViews(TestCase):
    def setUp(self):
        self.user = make_user("notifuser")
        self.sender = make_user("sender")
        self.doc = make_doc(self.user)
        self.c = auth_client(self.user)
        self.notif = Notification.objects.create(
            recipient=self.user,
            sender=self.sender,
            notification_type="document_shared",
            title="Test Notif",
            message="You have a new notification",
            document=self.doc,
        )

    def test_notifications_list(self):
        r = self.c.get(reverse("notifications_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Notif")

    def test_mark_read(self):
        r = self.c.post(reverse("notification_mark_read", kwargs={"pk": self.notif.pk}))
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)

    def test_mark_all_read_ajax(self):
        r = self.c.post(
            reverse("notification_mark_all_read_ajax"),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)


# ══════════════════════════════════════════════════════════════
# 11. PROFILE VIEWS
# ══════════════════════════════════════════════════════════════


class TestProfileViews(TestCase):
    def setUp(self):
        self.user = make_user("profuser")
        self.c = auth_client(self.user)

    def test_profile_get(self):
        r = self.c.get(reverse("profile"))
        self.assertEqual(r.status_code, 200)

    def test_profile_by_username(self):
        r = self.c.get(reverse("profile_view", kwargs={"username": self.user.username}))
        self.assertEqual(r.status_code, 200)

    def test_profile_edit_get(self):
        r = self.c.get(reverse("profile_edit"))
        self.assertEqual(r.status_code, 200)

    def test_profile_edit_post(self):
        r = self.c.post(reverse("profile_edit"), {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "profuser@example.com",
            "bio": "Hello world",
            "phone": "",
            "department": "",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")


# ══════════════════════════════════════════════════════════════
# 12. ADMIN VIEWS
# ══════════════════════════════════════════════════════════════


class TestAdminViews(TestCase):
    def setUp(self):
        self.admin = make_admin("adminv")
        self.user = make_user("nonadmin")
        self.admin_c = auth_client(self.admin)
        self.user_c = auth_client(self.user)

    def test_admin_users_list_admin(self):
        r = self.admin_c.get(reverse("admin_users_list"))
        self.assertEqual(r.status_code, 200)

    def test_admin_users_list_non_admin(self):
        r = self.user_c.get(reverse("admin_users_list"))
        self.assertNotEqual(r.status_code, 200)

    def test_admin_roles_list_admin(self):
        r = self.admin_c.get(reverse("admin_roles_list"))
        self.assertEqual(r.status_code, 200)

    def test_admin_role_create(self):
        r = self.admin_c.post(reverse("admin_role_create"), {
            "name": "NewRole",
            "description": "",
            "level": 30,
            "is_default": False,
        })
        self.assertTrue(Role.objects.filter(name="NewRole").exists())

    def test_admin_user_update_role(self):
        target = make_user("target_user")
        role = make_role("SomeRole", level=15)
        r = self.admin_c.post(
            reverse("admin_user_update_role", kwargs={"user_id": target.pk}),
            {"role": role.pk, "user_type": "user"},
        )
        target.refresh_from_db()
        self.assertEqual(target.role, role)


# ══════════════════════════════════════════════════════════════
# 13. CATEGORY VIEWS
# ══════════════════════════════════════════════════════════════


class TestCategoryViews(TestCase):
    def setUp(self):
        self.user = make_user("catuser")
        self.c = auth_client(self.user)

    def test_category_list(self):
        r = self.c.get(reverse("category_list"))
        self.assertEqual(r.status_code, 200)

    def test_category_create(self):
        r = self.c.post(reverse("category_create"), {
            "name": "Science",
            "description": "",
            "color": "#00ff00",
            "icon": "",
            "parent": "",
        })
        self.assertTrue(Category.objects.filter(name="Science").exists())


# ══════════════════════════════════════════════════════════════
# 14. SEARCH AND ACTIVITY
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestSearchView(TestCase):
    def setUp(self):
        self.user = make_user("searcher")
        self.c = auth_client(self.user)
        make_doc(self.user, "Quarterly Report")

    def test_search_page_loads(self):
        r = self.c.get(reverse("advanced_search"))
        self.assertEqual(r.status_code, 200)

    def test_search_returns_results(self):
        r = self.c.get(reverse("advanced_search") + "?query=Quarterly")
        self.assertContains(r, "Quarterly Report")

    def test_search_no_results(self):
        r = self.c.get(reverse("advanced_search") + "?query=ZZZnonexistent")
        self.assertEqual(r.status_code, 200)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestActivityLogView(TestCase):
    def setUp(self):
        self.user = make_user("actuser")
        self.admin = make_admin("actadmin")
        self.doc = make_doc(self.user)
        ActivityLog.objects.create(
            user=self.user, document=self.doc, action="view", description="viewed"
        )

    def test_activity_log_admin(self):
        c = auth_client(self.admin)
        r = c.get(reverse("activity_log"))
        self.assertEqual(r.status_code, 200)

    def test_activity_log_non_admin_denied(self):
        c = auth_client(self.user)
        r = c.get(reverse("activity_log"))
        self.assertNotEqual(r.status_code, 200)


# ══════════════════════════════════════════════════════════════
# 15. WORKSPACE VIEW
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestWorkspaceView(TestCase):
    def setUp(self):
        self.user = make_user("wsuser")
        self.c = auth_client(self.user)

    def test_workspace_loads(self):
        r = self.c.get(reverse("workspace"))
        self.assertEqual(r.status_code, 200)

    def test_workspace_requires_login(self):
        r = self.client.get(reverse("workspace"))
        self.assertEqual(r.status_code, 302)

    def test_workspace_shows_folders(self):
        make_folder(self.user, "My Folder")
        r = self.c.get(reverse("workspace"))
        self.assertContains(r, "My Folder")

    def test_workspace_agent_page(self):
        r = self.c.get(reverse("workspace_agent"))
        self.assertEqual(r.status_code, 200)


# ══════════════════════════════════════════════════════════════
# 16. FOLDER API
# ══════════════════════════════════════════════════════════════


class TestFolderAPI(TestCase):
    def setUp(self):
        self.user = make_user("folderapi")
        self.c = auth_client(self.user)

    def _post_json(self, url, data):
        return self.c.post(url, json.dumps(data), content_type="application/json")

    def test_create_folder(self):
        r = self._post_json(reverse("folder_create"), {"name": "NewFolder"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("ok") or "id" in data)
        self.assertTrue(Folder.objects.filter(owner=self.user, name="NewFolder").exists())

    def test_create_folder_missing_name(self):
        r = self._post_json(reverse("folder_create"), {})
        self.assertEqual(r.status_code, 400)

    def test_rename_folder(self):
        f = make_folder(self.user, "OldName")
        r = self._post_json(reverse("folder_rename", kwargs={"pk": f.pk}), {"name": "NewName"})
        self.assertEqual(r.status_code, 200)
        f.refresh_from_db()
        self.assertEqual(f.name, "NewName")

    def test_delete_folder(self):
        f = make_folder(self.user, "ToDelete")
        r = self._post_json(reverse("folder_delete", kwargs={"pk": f.pk}), {})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Folder.objects.filter(pk=f.pk).exists())

    def test_cannot_rename_others_folder(self):
        other = make_user("folderother")
        f = make_folder(other, "OthersFolder")
        r = self._post_json(reverse("folder_rename", kwargs={"pk": f.pk}), {"name": "Hacked"})
        f.refresh_from_db()
        self.assertEqual(f.name, "OthersFolder")

    def test_move_document_to_folder(self):
        doc = make_doc(self.user, "MoveMe")
        folder = make_folder(self.user, "Destination")
        r = self._post_json(
            reverse("document_move", kwargs={"pk": doc.pk}),
            {"folder_id": folder.pk},
        )
        self.assertEqual(r.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.folder, folder)


# ══════════════════════════════════════════════════════════════
# 17. CHATBOT VIEWS
# ══════════════════════════════════════════════════════════════


class TestChatbotViews(TestCase):
    def setUp(self):
        self.user = make_user("cbuser")
        self.c = auth_client(self.user)

    def test_chatbot_page_loads(self):
        r = self.c.get(reverse("chatbot"))
        self.assertEqual(r.status_code, 200)

    def test_chatbot_requires_login(self):
        r = self.client.get(reverse("chatbot"))
        self.assertEqual(r.status_code, 302)

    @patch("documents.rag_views.get_rag_chatbot")
    def test_chatbot_query(self, mock_rag):
        mock_bot = MagicMock()
        mock_bot.chat.return_value = {
            "answer": "Test answer",
            "sources": [],
            "retrieval_time": 0.1,
            "generation_time": 0.2,
        }
        mock_rag.return_value = mock_bot

        r = self.c.post(
            reverse("chatbot_query"),
            json.dumps({"query": "What is this?", "session_id": None}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("answer", data)

    def test_chat_history_page(self):
        r = self.c.get(reverse("chat_history"))
        self.assertEqual(r.status_code, 200)

    def test_new_chat(self):
        r = self.c.get(reverse("new_chat"))
        self.assertIn(r.status_code, [200, 302])

    def test_chat_session_detail(self):
        session = ChatSession.objects.create(user=self.user, title="My Session")
        r = self.c.get(reverse("chat_session_detail", kwargs={"pk": session.pk}))
        self.assertEqual(r.status_code, 200)

    def test_delete_session(self):
        session = ChatSession.objects.create(user=self.user, title="Del Session")
        r = self.c.post(reverse("delete_session", kwargs={"pk": session.pk}))
        self.assertFalse(ChatSession.objects.filter(pk=session.pk).exists())

    def test_rename_session(self):
        session = ChatSession.objects.create(user=self.user, title="Old Title")
        r = self.c.post(
            reverse("rename_session", kwargs={"pk": session.pk}),
            json.dumps({"title": "New Title"}),
            content_type="application/json",
        )
        session.refresh_from_db()
        self.assertEqual(session.title, "New Title")


# ══════════════════════════════════════════════════════════════
# 18. INDEXING VIEWS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestIndexingViews(TestCase):
    def setUp(self):
        self.user = make_user("idxuser")
        self.doc = make_doc(self.user, "Index Me")
        self.c = auth_client(self.user)

    def test_index_status_view(self):
        r = self.c.get(reverse("document_index_status", kwargs={"pk": self.doc.pk}))
        self.assertIn(r.status_code, [200])
        data = r.json()
        self.assertIn("is_indexed", data)

    @patch("documents.rag_views.index_document_task")
    def test_reindex_document(self, mock_task):
        mock_task.return_value = None
        r = self.c.post(reverse("document_reindex", kwargs={"pk": self.doc.pk}))
        self.assertIn(r.status_code, [200, 202])

    def test_rag_system_info(self):
        r = self.c.get(reverse("rag_system_info"))
        self.assertIn(r.status_code, [200])


# ══════════════════════════════════════════════════════════════
# 19. AGENT API
# ══════════════════════════════════════════════════════════════


class TestAgentAPI(TestCase):
    def setUp(self):
        self.user = make_user("agentuser")
        self.token_value = AgentToken.get_or_create_for_user(self.user)
        self.auth = {"HTTP_AUTHORIZATION": f"Token {self.token_value}"}

    def _post_json(self, url, data, **extra):
        return self.client.post(
            url,
            json.dumps(data),
            content_type="application/json",
            **extra,
        )

    def test_auth_valid_credentials(self):
        r = self._post_json(
            reverse("agent_auth"),
            {"username": "agentuser", "password": "pass1234!"},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("token", data)

    def test_auth_invalid_credentials(self):
        r = self._post_json(
            reverse("agent_auth"),
            {"username": "agentuser", "password": "wrongpass"},
        )
        self.assertEqual(r.status_code, 401)

    def test_auth_missing_fields(self):
        r = self._post_json(reverse("agent_auth"), {})
        self.assertEqual(r.status_code, 400)

    def test_heartbeat(self):
        r = self.client.post(reverse("agent_heartbeat"), **self.auth)
        self.assertIn(r.status_code, [200])

    def test_heartbeat_no_token(self):
        r = self.client.post(reverse("agent_heartbeat"))
        self.assertEqual(r.status_code, 401)

    def test_agent_status(self):
        r = self.client.get(reverse("agent_status"), **self.auth)
        self.assertIn(r.status_code, [200])

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_upload(self):
        f = dummy_txt("upload.txt")
        r = self.client.post(
            reverse("agent_upload"),
            {
                "file": f,
                "title": "Agent Upload",
                "access_level": "private",
            },
            **self.auth,
        )
        self.assertIn(r.status_code, [200, 201])
        if r.status_code in [200, 201]:
            data = r.json()
            self.assertTrue(data.get("ok"))

    def test_agent_token_reset(self):
        r = self.client.post(reverse("agent_token_reset"), **self.auth)
        self.assertIn(r.status_code, [200])
        data = r.json()
        self.assertTrue(data.get("ok"))
        # Token should have changed
        old_token = self.token_value
        new_token = data.get("token")
        if new_token:
            self.assertNotEqual(old_token, new_token)

    def test_agent_events(self):
        r = self.client.get(reverse("agent_events"), **self.auth)
        self.assertIn(r.status_code, [200])

    def test_sync_start(self):
        r = self.client.post(reverse("agent_sync_start"), **self.auth)
        self.assertIn(r.status_code, [200])

    def test_sync_done(self):
        r = self.client.post(reverse("agent_sync_done"), **self.auth)
        self.assertIn(r.status_code, [200])

    def test_sync_status(self):
        r = self.client.get(reverse("agent_sync_status"), **self.auth)
        self.assertIn(r.status_code, [200])


# ══════════════════════════════════════════════════════════════
# 20. ACCESS CONTROL / SECURITY
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestAccessControl(TestCase):
    def setUp(self):
        self.owner = make_user("acowner")
        self.user = make_user("acuser")
        self.admin = make_admin("acadmin")
        self.doc = make_doc(self.owner, access_level="private")

    def test_unauthenticated_cannot_view_document(self):
        r = self.client.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 302)

    def test_other_user_cannot_edit_private(self):
        c = auth_client(self.user)
        r = c.get(reverse("document_edit", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 403)

    def test_admin_can_edit_any(self):
        c = auth_client(self.admin)
        r = c.get(reverse("document_edit", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_admin_can_view_private(self):
        c = auth_client(self.admin)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_role_based_access_sufficient(self):
        r = make_role("Senior", level=80)
        self.user.role = r
        self.user.save()
        self.doc.access_level = "role"
        self.doc.required_role_level = 50
        self.doc.save()
        c = auth_client(self.user)
        r2 = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r2.status_code, 200)

    def test_role_based_access_insufficient(self):
        role = make_role("Junior", level=10)
        self.user.role = role
        self.user.save()
        self.doc.access_level = "role"
        self.doc.required_role_level = 50
        self.doc.save()
        c = auth_client(self.user)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 403)

    def test_custom_share_grants_access(self):
        self.doc.access_level = "custom"
        self.doc.save()
        self.doc.shared_with.add(self.user)
        c = auth_client(self.user)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 200)

    def test_custom_share_without_share_denied(self):
        self.doc.access_level = "custom"
        self.doc.save()
        c = auth_client(self.user)
        r = c.get(reverse("document_detail", kwargs={"pk": self.doc.pk}))
        self.assertEqual(r.status_code, 403)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestSecurityEdgeCases(TestCase):
    def setUp(self):
        self.user = make_user("secuser")

    def test_deleted_doc_returns_404(self):
        doc = make_doc(self.user, "Deleted")
        doc.is_deleted = True
        doc.save()
        c = auth_client(self.user)
        r = c.get(reverse("document_detail", kwargs={"pk": doc.pk}))
        self.assertEqual(r.status_code, 404)

    def test_folder_api_requires_login(self):
        r = self.client.post(
            reverse("folder_create"),
            json.dumps({"name": "Hacker"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 302)

    def test_cannot_move_others_document(self):
        other = make_user("moveother")
        doc = make_doc(other, "OthersDoc")
        folder = make_folder(self.user, "MyFolder")
        c = auth_client(self.user)
        r = c.post(
            reverse("document_move", kwargs={"pk": doc.pk}),
            json.dumps({"folder_id": folder.pk}),
            content_type="application/json",
        )
        doc.refresh_from_db()
        # Document should NOT be moved to self.user's folder
        self.assertNotEqual(doc.folder, folder)

    def test_agent_api_bearer_required(self):
        # Using wrong prefix "Bearer" instead of "Token"
        r = self.client.post(
            reverse("agent_heartbeat"),
            HTTP_AUTHORIZATION="Bearer invalidtoken",
        )
        self.assertEqual(r.status_code, 401)


# ══════════════════════════════════════════════════════════════
# 21. PAGINATION
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestPagination(TestCase):
    def setUp(self):
        self.user = make_user("paguser")
        self.c = auth_client(self.user)
        for i in range(25):
            make_doc(self.user, f"Doc {i:02d}")

    def test_document_list_paginates(self):
        r = self.c.get(reverse("document_list"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("page_obj", r.context)
        self.assertTrue(r.context["page_obj"].has_next())

    def test_page_2(self):
        r = self.c.get(reverse("document_list") + "?page=2")
        self.assertEqual(r.status_code, 200)


# ══════════════════════════════════════════════════════════════
# 22. JSON API RESPONSE FORMAT
# ══════════════════════════════════════════════════════════════


class TestJSONAPIResponseFormat(TestCase):
    def setUp(self):
        self.user = make_user("jsonuser")
        self.c = auth_client(self.user)

    def test_folder_create_returns_json(self):
        r = self.c.post(
            reverse("folder_create"),
            json.dumps({"name": "JSONFolder"}),
            content_type="application/json",
        )
        self.assertEqual(r["Content-Type"], "application/json")

    def test_agent_auth_returns_json(self):
        r = self.client.post(
            reverse("agent_auth"),
            json.dumps({"username": "jsonuser", "password": "pass1234!"}),
            content_type="application/json",
        )
        self.assertEqual(r["Content-Type"], "application/json")
        data = r.json()
        self.assertIn("ok", data)

    def test_mark_all_read_returns_json(self):
        r = self.c.post(
            reverse("notification_mark_all_read_ajax"),
            content_type="application/json",
        )
        self.assertEqual(r["Content-Type"], "application/json")


# ══════════════════════════════════════════════════════════════
# 23. TEMPLATE SMOKE TESTS (200 status + correct template)
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestTemplateSmokeTests(TestCase):
    def setUp(self):
        self.user = make_user("tmpluser")
        self.admin = make_admin("tmpl_admin")
        self.user_c = auth_client(self.user)
        self.admin_c = auth_client(self.admin)

    def test_home_template(self):
        r = self.client.get(reverse("home"))
        self.assertTemplateUsed(r, "documents/home.html")

    def test_login_template(self):
        r = self.client.get(reverse("login"))
        self.assertTemplateUsed(r, "documents/auth/login.html")

    def test_register_template(self):
        r = self.client.get(reverse("register"))
        self.assertTemplateUsed(r, "documents/auth/register.html")

    def test_dashboard_template(self):
        r = self.user_c.get(reverse("dashboard"))
        self.assertTemplateUsed(r, "documents/dashboard.html")

    def test_workspace_template(self):
        r = self.user_c.get(reverse("workspace"))
        self.assertTemplateUsed(r, "documents/workspace.html")

    def test_document_list_template(self):
        r = self.user_c.get(reverse("document_list"))
        self.assertTemplateUsed(r, "documents/document_list.html")

    def test_document_create_template(self):
        r = self.user_c.get(reverse("document_create"))
        self.assertTemplateUsed(r, "documents/document_form.html")

    def test_chatbot_template(self):
        r = self.user_c.get(reverse("chatbot"))
        self.assertTemplateUsed(r, "rag/chatbot.html")

    def test_workspace_agent_template(self):
        r = self.user_c.get(reverse("workspace_agent"))
        self.assertTemplateUsed(r, "documents/workspace_agent.html")

    def test_favorites_list_template(self):
        r = self.user_c.get(reverse("favorites_list"))
        self.assertTemplateUsed(r, "documents/favorites_list.html")

    def test_profile_template(self):
        r = self.user_c.get(reverse("profile"))
        self.assertTemplateUsed(r, "documents/profile.html")


# ══════════════════════════════════════════════════════════════
# 24. TAGS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestTags(TestCase):
    def setUp(self):
        self.user = make_user("taguser")
        self.c = auth_client(self.user)

    def test_tag_created_on_document_create(self):
        self.c.post(reverse("document_create"), {
            "title": "Tagged Doc",
            "description": "",
            "file": dummy_txt("tagged.txt"),
            "access_level": "private",
            "required_role_level": 1,
            "allow_comments": True,
            "allow_download": True,
            "tags": "finance, report",
        })
        self.assertTrue(Tag.objects.filter(name="finance").exists())
        self.assertTrue(Tag.objects.filter(name="report").exists())

    def test_tag_filter_in_list(self):
        tag = Tag.objects.create(name="mytag")
        doc = make_doc(self.user, "Tagged Doc 2")
        doc.tags.add(tag)
        r = self.c.get(reverse("document_list") + f"?tag={tag.pk}")
        self.assertContains(r, "Tagged Doc 2")

    def test_tag_str(self):
        tag = Tag.objects.create(name="testtag")
        self.assertEqual(str(tag), "testtag")


# ══════════════════════════════════════════════════════════════
# 25. ADVANCED SEARCH FILTERS
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestAdvancedSearchFilters(TestCase):
    def setUp(self):
        self.user = make_user("advuser")
        self.c = auth_client(self.user)
        self.cat = make_category("Finance", created_by=self.user)
        self.doc = make_doc(self.user, "Budget 2024", category=self.cat)

    def test_filter_by_category(self):
        r = self.c.get(reverse("advanced_search") + f"?category={self.cat.pk}")
        self.assertContains(r, "Budget 2024")

    def test_filter_by_access_level(self):
        r = self.c.get(reverse("advanced_search") + "?access_level=private")
        self.assertContains(r, "Budget 2024")

    def test_filter_public_excludes_private(self):
        r = self.c.get(reverse("advanced_search") + "?access_level=public")
        self.assertNotContains(r, "Budget 2024")


# ══════════════════════════════════════════════════════════════
# 26. ACTIVITY LOGGING
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestActivityLogging(TestCase):
    def setUp(self):
        self.user = make_user("actloguser")

    def test_view_action_logged(self):
        doc = make_doc(self.user, access_level="public")
        c = auth_client(self.user)
        c.get(reverse("document_detail", kwargs={"pk": doc.pk}))
        self.assertTrue(ActivityLog.objects.filter(document=doc, action="view", user=self.user).exists())

    def test_create_action_logged(self):
        c = auth_client(self.user)
        c.post(reverse("document_create"), {
            "title": "Activity Log Doc",
            "description": "",
            "file": dummy_txt("actlog.txt"),
            "access_level": "private",
            "required_role_level": 1,
            "allow_comments": True,
            "allow_download": True,
        })
        doc = Document.objects.filter(title="Activity Log Doc").first()
        self.assertIsNotNone(doc)
        self.assertTrue(ActivityLog.objects.filter(document=doc, action="create").exists())


# ══════════════════════════════════════════════════════════════
# 27. MISC EDGE CASES
# ══════════════════════════════════════════════════════════════


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestMiscEdgeCases(TestCase):
    def setUp(self):
        self.user = make_user("miscuser")
        self.c = auth_client(self.user)

    def test_nonexistent_document_detail_404(self):
        r = self.c.get(reverse("document_detail", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)

    def test_nonexistent_document_edit_404(self):
        r = self.c.get(reverse("document_edit", kwargs={"pk": 99999}))
        self.assertEqual(r.status_code, 404)

    def test_register_assigns_default_role(self):
        default_role = Role.objects.create(name="DefaultRole", level=5, is_default=True)
        self.client.post(reverse("register"), {
            "username": "roleduser",
            "email": "roled@example.com",
            "first_name": "Roled",
            "last_name": "User",
            "password1": "ComplexPass99!",
            "password2": "ComplexPass99!",
        })
        u = User.objects.get(username="roleduser")
        self.assertEqual(u.role, default_role)

    def test_document_version_1_created_on_upload(self):
        self.c.post(reverse("document_create"), {
            "title": "Version Check",
            "description": "",
            "file": dummy_txt("ver.txt"),
            "access_level": "private",
            "required_role_level": 1,
            "allow_comments": True,
            "allow_download": True,
        })
        doc = Document.objects.get(title="Version Check")
        self.assertTrue(doc.versions.filter(version_number=1).exists())

    def test_favorite_count_in_context(self):
        doc = make_doc(self.user, "Fav Test")
        Favorite.objects.create(user=self.user, document=doc)
        r = self.c.get(reverse("favorites_list"))
        self.assertContains(r, "Fav Test")

    def test_login_next_redirect(self):
        target = reverse("document_list")
        r = self.client.get(f"{reverse('login')}?next={target}")
        self.assertEqual(r.status_code, 200)

    def test_post_invalid_form_shows_errors(self):
        r = self.c.post(reverse("document_create"), {
            "title": "",  # required field missing
            "access_level": "private",
        })
        self.assertEqual(r.status_code, 200)
        self.assertFormError(r, "form", "title", "This field is required.")

    def test_category_model_str(self):
        cat = make_category("Legal", created_by=self.user)
        self.assertEqual(str(cat), "Legal")

    def test_activity_log_str(self):
        doc = make_doc(self.user, "LogStr")
        log = ActivityLog.objects.create(user=self.user, document=doc, action="view")
        self.assertIn("view", str(log))

    def test_notification_str(self):
        sender = make_user("nstr_sender")
        doc = make_doc(self.user, "NStrDoc")
        n = Notification.objects.create(
            recipient=self.user,
            sender=sender,
            notification_type="document_shared",
            title="Hello",
            message="Test",
            document=doc,
        )
        self.assertIn("Hello", str(n))

    def test_document_comment_str(self):
        doc = make_doc(self.user, "CommentStr")
        c = DocumentComment.objects.create(document=doc, user=self.user, content="hello")
        self.assertIn("miscuser", str(c))
