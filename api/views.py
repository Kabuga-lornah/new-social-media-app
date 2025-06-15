from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from core.models import Profile, Post, Comment
from api.serializers import (
    UserSerializer, 
    ProfileSerializer, 
    PostSerializer, 
    CommentSerializer,
)
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own profile.")
        serializer.save()

class PostListView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_at')
        author_id = self.request.query_params.get('author', None)
        if author_id is not None:
            queryset = queryset.filter(author__id=author_id)
        return queryset.select_related('author', 'author__profile').prefetch_related('likes', 'comments')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You can only update your own posts.")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post__id=post_id)\
            .select_related('author', 'author__profile', 'post')\
            .prefetch_related('likes')\
            .order_by('-created_at')
    
    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(author=self.request.user, post=post)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You can only update your own comments.")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class LikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        if request.user in post.likes.all():
            return Response({
                'status': 'already_liked',
                'likes_count': post.likes.count(),
                'is_liked': True
            }, status=status.HTTP_200_OK)
            
        post.likes.add(request.user)
        return Response({
            'status': 'liked',
            'likes_count': post.likes.count(),
            'is_liked': True
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        if request.user not in post.likes.all():
            return Response({
                'status': 'not_liked',
                'likes_count': post.likes.count(),
                'is_liked': False
            }, status=status.HTTP_200_OK)
            
        post.likes.remove(request.user)
        return Response({
            'status': 'unliked',
            'likes_count': post.likes.count(),
            'is_liked': False
        }, status=status.HTTP_200_OK)

class LikeCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user in comment.likes.all():
            return Response({
                'status': 'already_liked',
                'likes_count': comment.likes.count(),
                'is_liked': True
            }, status=status.HTTP_200_OK)
            
        comment.likes.add(request.user)
        return Response({
            'status': 'liked',
            'likes_count': comment.likes.count(),
            'is_liked': True
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user not in comment.likes.all():
            return Response({
                'status': 'not_liked',
                'likes_count': comment.likes.count(),
                'is_liked': False
            }, status=status.HTTP_200_OK)
            
        comment.likes.remove(request.user)
        return Response({
            'status': 'unliked',
            'likes_count': comment.likes.count(),
            'is_liked': False
        }, status=status.HTTP_200_OK)

class FollowUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, id=user_id)
        if user_to_follow == request.user:
            return Response(
                {'detail': 'Cannot follow yourself'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        profile = request.user.profile
        if user_to_follow in profile.following.all():
            return Response(
                {'status': 'already_following'},
                status=status.HTTP_200_OK
            )
            
        profile.following.add(user_to_follow)
        return Response(
            {'status': 'followed'},
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, user_id):
        user_to_unfollow = get_object_or_404(User, id=user_id)
        profile = request.user.profile
        
        if user_to_unfollow not in profile.following.all():
            return Response(
                {'status': 'not_following'},
                status=status.HTTP_200_OK
            )
            
        profile.following.remove(user_to_unfollow)
        return Response(
            {'status': 'unfollowed'},
            status=status.HTTP_200_OK
        )

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = StandardResultsPagination
    
    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        if not query:
            return User.objects.none()
            
        return User.objects.filter(
            username__icontains=query
        ).select_related('profile')