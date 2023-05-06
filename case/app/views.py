from django.db.models import Q
from rest_framework import generics, viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny

from .models import User, FriendshipRelation
from .serializers import (
    UserSerializer, 
    FriendshipRequestSerializer,
    FriendshipAcceptSerializer,
)


class RegistrationView(generics.CreateAPIView):
    """View provides User registration."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes=(AllowAny,)


class FriendshipRequestView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """View provides retrieve a list of friendship request objects and create friendship request."""

    filter_backends = (SearchFilter,)
    search_fields = ('=user_sender__username', '=user_recipient__username')
    serializer_class = FriendshipRequestSerializer

    def get_queryset(self):
        flag_in = 'incoming' in self.request.query_params
        flag_out = 'outgoing' in self.request.query_params
        if (flag_in and flag_out) or (not flag_in and not flag_out):
            queryset = FriendshipRelation.objects.filter(
                Q(user_sender=self.request.user)|Q(user_recipient=self.request.user),
                accept=None
            ).select_related('user_sender', 'user_recipient')
        elif flag_in and not flag_out:
            queryset = FriendshipRelation.objects.filter(
                user_recipient = self.request.user,
                accept=None
            ).select_related('user_sender', 'user_recipient')
        elif flag_out and not flag_in:
            queryset = FriendshipRelation.objects.filter(
                user_sender = self.request.user,
                accept=None
            ).select_related('user_sender', 'user_recipient')
        return queryset
    
    def perform_create(self, serializer):
        try:
            mutual_request = FriendshipRelation.objects.get(
                user_sender=self.request.data.get('user_recipient'),
                user_recipient=self.request.user,
                accept=None,
            )
        except FriendshipRelation.DoesNotExist:
            serializer.save(user_sender=self.request.user)
        else:
            mutual_request.delete()
            serializer.save(user_sender=self.request.user, accept=True)


class FriendshipAcceptView(generics.UpdateAPIView):
    """View provides rejecting or accepting incoming friendship request."""

    serializer_class = FriendshipAcceptSerializer

    def get_queryset(self):
        queryset = FriendshipRelation.objects \
            .filter(accept=None) \
            .select_related('user_sender', 'user_recipient')
        return queryset
    

class FriendshipView(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    
    serializer_class=FriendshipRequestSerializer
    
    def get_queryset(self):
        queryset = FriendshipRelation.objects.filter(
            Q(user_sender=self.request.user)|Q(user_recipient=self.request.user),
            accept=True,
        ).select_related('user_sender', 'user_recipient')
        return queryset
