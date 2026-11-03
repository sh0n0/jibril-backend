from django.urls import path

from jibril_backend.corpus.views import SentenceSearchView

urlpatterns = [
    path("sentences/search/", SentenceSearchView.as_view(), name="sentence-search"),
]
