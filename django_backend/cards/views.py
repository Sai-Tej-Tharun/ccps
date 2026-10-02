from rest_framework import status
from rest_framework.generics import DestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Card
from .serializers import CardCreateSerializer, CardSerializer


class CardListCreateView(ListCreateAPIView):
    """
    GET  /api/cards/       — list ONLY the current user's saved cards
    POST /api/cards/       — add a card for the current user
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return CardCreateSerializer if self.request.method == "POST" else CardSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        card = serializer.save()
        return Response(CardSerializer(card).data, status=status.HTTP_201_CREATED)


class CardDeleteView(DestroyAPIView):
    """DELETE /api/cards/<id>/ — only the owning user may delete their own card."""

    permission_classes = [IsAuthenticated]
    serializer_class = CardSerializer

    def get_queryset(self):
        # Scoping the queryset to the current user means a request for
        # someone else's card ID 404s instead of leaking a 403 that would
        # confirm the card ID exists at all.
        return Card.objects.filter(user=self.request.user)
