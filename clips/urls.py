from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClipsList.as_view(), name='clip_list'),
    path('<int:pk>/', views.ClipsList.as_view(), name='play_clip'),
    path("create/", views.ClipUploadView.as_view(), name="add_clip"),
    path("update/<int:pk>/", views.ClipUpdateView.as_view(), name="update_clip"),
    path("delete/<int:pk>/", views.ClipDeleteView.as_view(), name="delete_clip"),
    path("trigger/", views.TriggerChime.as_view(), name="trigger_chime"),
    path("last-played/", views.LastPlayedView.as_view(), name="last_played"),
    # Playlists
    path("playlists/", views.PlaylistListView.as_view(), name="playlist_list"),
    path("playlists/<int:pk>/", views.PlaylistDetailView.as_view(), name="playlist_detail"),
    path("playlists/<int:pk>/rename/", views.PlaylistRenameView.as_view(), name="playlist_rename"),
    path("playlists/<int:pk>/activate/", views.PlaylistActivateView.as_view(), name="playlist_activate"),
    path("playlists/<int:pk>/delete/", views.PlaylistDeleteView.as_view(), name="playlist_delete"),
    path("playlists/<int:pk>/clips/add/", views.PlaylistClipAddView.as_view(), name="playlist_clip_add"),
    path("playlists/<int:pk>/clips/<int:clip_pk>/remove/", views.PlaylistClipRemoveView.as_view(), name="playlist_clip_remove"),
]