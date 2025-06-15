from django.urls import path
from api.views import (
    UserListView,
    UserDetailView,
    ProfileDetailView,
    PostListView,
    PostDetailView,
    CommentListView,
    CommentDetailView,
    LikePostView,
    LikeCommentView,
    FollowUserView,
    UserSearchView
)

urlpatterns = [
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profiles/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    
    path('posts/<int:post_id>/like/', LikePostView.as_view(), name='like-post'),
    path('comments/<int:comment_id>/like/', LikeCommentView.as_view(), name='like-comment'),
    
    path('users/<int:user_id>/follow/', FollowUserView.as_view(), name='follow-user'),
    
    path('search/users/', UserSearchView.as_view(), name='user-search'),
]