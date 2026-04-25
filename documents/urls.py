from django.urls import path
from . import views
from . import rag_views
from . import agent_api

urlpatterns = [
    # ============================================================
    # AUTHENTICATION URLS
    # ============================================================
    path('register/', views.register_view, name='register'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('api/approval/status/', views.approval_status_api, name='approval_status_api'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/approvals/', views.approval_dashboard_view, name='approval_dashboard'),
    path('admin/users/<int:user_id>/approve/', views.approve_user_view, name='approve_user'),
    path('admin/users/<int:user_id>/reject/', views.reject_user_view, name='reject_user'),
    path('api/pending-users/count/', views.pending_users_api, name='pending_users_count'),
    path('api/dismiss-admin-popup/', views.dismiss_admin_popup, name='dismiss_admin_popup'),
    
    # ============================================================
    # HOME AND DASHBOARD
    # ============================================================
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # ============================================================
    # WORKSPACE (agent-style folder + document UI)
    # ============================================================
    path('workspace/',                      views.workspace_view,             name='workspace'),
    path('workspace/agent/',               views.workspace_agent_view,        name='workspace_agent'),
    path('workspace/agent/config/save/',   views.agent_config_save_view,      name='agent_config_save'),
    path('workspace/agent/process/start/', views.agent_process_start_view,    name='agent_process_start'),
    path('workspace/agent/process/stop/',  views.agent_process_stop_view,     name='agent_process_stop'),
    path('workspace/agent/process/status/',views.agent_process_status_view,   name='agent_process_status'),
    path('workspace/agent/download/',      views.agent_download_view,          name='agent_download'),
    path('workspace/agent/download/bat/',  views.agent_bat_download_view,      name='agent_bat_download'),
    path('workspace/agent/build/',         views.agent_build_exe_view,         name='agent_build_exe'),
    path('workspace/agent/build/log/',     views.agent_build_log_view,         name='agent_build_log'),

    # Folder CRUD (AJAX / JSON)
    path('api/folders/create/',              views.folder_create_api,    name='folder_create'),
    path('api/folders/<int:pk>/rename/',     views.folder_rename_api,    name='folder_rename'),
    path('api/folders/<int:pk>/delete/',     views.folder_delete_api,    name='folder_delete'),
    path('api/documents/<int:pk>/move/',     views.document_move_api,    name='document_move'),
    
    # ============================================================
    # DOCUMENT URLS
    # ============================================================
    path('documents/', views.document_list_view, name='document_list'),
    path('documents/create/', views.document_create_view, name='document_create'),
    path('documents/<int:pk>/', views.document_detail_view, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_edit_view, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete_view, name='document_delete'),
    path('documents/<int:pk>/download/', views.document_download_view, name='document_download'),
    path('documents/<int:doc_pk>/versions/<int:version_pk>/download/', views.version_download_view, name='version_download'),
    path('documents/<int:doc_pk>/versions/<int:version_pk>/restore/', views.version_restore_view,  name='version_restore'),
    
    # ============================================================
    # COMMENT URLS
    # ============================================================
    path('documents/<int:document_pk>/comments/create/', views.comment_create_view, name='comment_create'),
    path('comments/<int:pk>/delete/', views.comment_delete_view, name='comment_delete'),
    
    # ============================================================
    # FAVORITE URLS
    # ============================================================
    path('documents/<int:document_pk>/favorite/', views.favorite_toggle_view, name='favorite_toggle'),
    path('favorites/', views.favorites_list_view, name='favorites_list'),
    
    # ============================================================
    # SHARED LINK URLS
    # ============================================================
    path('documents/<int:document_pk>/share/', views.shared_link_create_view, name='shared_link_create'),
    path('share/<uuid:token>/', views.shared_link_access_view, name='shared_link_access'),
    
    # ============================================================
    # USER PROFILE URLS
    # ============================================================
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    
    # ============================================================
    # ADMIN - USER MANAGEMENT URLS
    # ============================================================
    path('admin/users/', views.admin_users_list_view, name='admin_users_list'),
    path('admin/users/<int:user_id>/update-role/', views.admin_user_update_role_view, name='admin_user_update_role'),
    
    # ============================================================
    # ADMIN - ROLE MANAGEMENT URLS
    # ============================================================
    path('admin/roles/', views.admin_roles_list_view, name='admin_roles_list'),
    path('admin/roles/create/', views.admin_role_create_view, name='admin_role_create'),
    path('admin/roles/<int:pk>/edit/', views.admin_role_edit_view, name='admin_role_edit'),
    path('admin/roles/<int:pk>/delete/', views.admin_role_delete_view, name='admin_role_delete'),
    
    # ============================================================
    # CATEGORY URLS
    # ============================================================
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    
    # ============================================================
    # NOTIFICATION URLS
    # ============================================================
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read-ajax/', views.notification_mark_all_read_ajax_view, name='notification_mark_all_read_ajax'),
    
    # ============================================================
    # SEARCH URLS
    # ============================================================
    path('search/', views.advanced_search_view, name='advanced_search'),
    
    # ============================================================
    # ACTIVITY LOG URLS
    # ============================================================
    path('activity/', views.activity_log_view, name='activity_log'),
    
    # ============================================================
    # RAG CHATBOT URLS
    # ============================================================
    path('chatbot/', rag_views.chatbot_view, name='chatbot'),
    path('chatbot/query/', rag_views.chatbot_query_api, name='chatbot_query'),
    path('chatbot/query/stream/', rag_views.chatbot_query_stream_view, name='chatbot_query_stream'),
    path('chatbot/voice/transcribe/', rag_views.voice_transcribe_view, name='voice_transcribe'),
    path('chatbot/history/', rag_views.chat_history_view, name='chat_history'),
    path('chatbot/session/<int:pk>/', rag_views.chat_session_detail_view, name='chat_session_detail'),
    path('chatbot/session/<int:pk>/delete/', rag_views.delete_session_view, name='delete_session'),
    path('chatbot/session/<int:pk>/rename/', rag_views.rename_session_view, name='rename_session'),
    path('chatbot/new/', rag_views.new_chat_view, name='new_chat'),
    path('chatbot/clear/', rag_views.clear_chat_view, name='clear_chat'),
    path('chatbot/session/<int:pk>/share/', rag_views.share_chat_view, name='share_chat'),
    path('chatbot/session/<int:pk>/public-share/', rag_views.toggle_public_share_view, name='toggle_public_share'),
    path('chatbot/shared-with-me/', rag_views.shared_with_me_view, name='shared_with_me'),
    path('chatbot/shared/<int:pk>/', rag_views.view_shared_chat_view, name='view_shared_chat'),
    path('chatbot/public/<uuid:token>/', rag_views.public_chat_view, name='public_chat'),

    # Voice Assistant (server-side Whisper STT + edge-tts TTS)
    path('voice/', rag_views.voice_assistant_view, name='voice_assistant'),
    path('voice/transcribe/', rag_views.voice_assistant_transcribe_view, name='voice_assistant_transcribe'),
    path('voice/synthesize/', rag_views.voice_synthesize_view, name='voice_synthesize'),
    
    # ============================================================
    # DOCUMENT INDEXING URLS
    # ============================================================
    path('documents/<int:pk>/index/', rag_views.document_index_view, name='document_index'),
    path('documents/<int:pk>/reindex/', rag_views.reindex_document_api, name='document_reindex'),
    path('documents/<int:pk>/index-status/', rag_views.document_index_status_view, name='document_index_status'),
    path('documents/bulk-index/', rag_views.bulk_index_documents_view, name='bulk_index_documents'),
    
    # ============================================================
    # RAG SYSTEM INFO URLS
    # ============================================================
    path('rag/info/', rag_views.rag_system_info_view, name='rag_system_info'),

    # ============================================================
    # DESKTOP AGENT API URLS  (no CSRF; token-authenticated)
    # ============================================================
    path('agent/auth/',         agent_api.agent_auth_view,        name='agent_auth'),
    path('agent/upload/',       agent_api.agent_upload_view,      name='agent_upload'),
    path('agent/events/',       agent_api.agent_events_view,      name='agent_events'),
    path('agent/heartbeat/',    agent_api.agent_heartbeat_view,   name='agent_heartbeat'),
    path('agent/token/reset/',  agent_api.agent_token_reset_view, name='agent_token_reset'),
    path('agent/status/',       agent_api.agent_status_view,      name='agent_status'),

    # Sync progress — called by desktop agent + polled by frontend
    path('agent/sync/start/',   views.agent_sync_start_view,      name='agent_sync_start'),
    path('agent/sync/done/',    views.agent_sync_done_view,        name='agent_sync_done'),
    path('agent/sync/status/',  views.agent_sync_status_view,     name='agent_sync_status'),
]