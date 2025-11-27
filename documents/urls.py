from django.urls import path
from . import views
from . import rag_views

urlpatterns = [
    # ============================================================
    # AUTHENTICATION URLS
    # ============================================================
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============================================================
    # HOME AND DASHBOARD
    # ============================================================
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # ============================================================
    # DOCUMENT URLS
    # ============================================================
    path('documents/', views.document_list_view, name='document_list'),
    path('documents/create/', views.document_create_view, name='document_create'),
    path('documents/<int:pk>/', views.document_detail_view, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_edit_view, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete_view, name='document_delete'),
    path('documents/<int:pk>/download/', views.document_download_view, name='document_download'),
    
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
    path('chatbot/history/', rag_views.chat_history_view, name='chat_history'),
    path('chatbot/session/<int:pk>/', rag_views.chat_session_detail_view, name='chat_session_detail'),
    path('chatbot/clear/', rag_views.clear_chat_view, name='clear_chat'),
    
    # ============================================================
    # DOCUMENT INDEXING URLS
    # ============================================================
    path('documents/<int:pk>/index/', rag_views.document_index_view, name='document_index'),
    path('documents/bulk-index/', rag_views.bulk_index_documents_view, name='bulk_index_documents'),
    
    # ============================================================
    # RAG SYSTEM INFO URLS
    # ============================================================
    path('rag/info/', rag_views.rag_system_info_view, name='rag_system_info'),
]