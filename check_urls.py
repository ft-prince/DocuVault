import sys, traceback
sys.path.insert(0, '.')

try:
    from documents.urls import urlpatterns
    chat_names = [p.name for p in urlpatterns if hasattr(p, 'name') and p.name and 'chat' in p.name.lower()]
    print("Chat URL names:", chat_names)
    all_names = [p.name for p in urlpatterns if hasattr(p, 'name')]
    print("All names:", all_names)
except Exception:
    traceback.print_exc()
