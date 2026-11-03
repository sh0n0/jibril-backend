from django.urls import path

from jibril_backend.corpus.views import CommentSearchView, SentenceSearchView

urlpatterns = [
    path(
        "oanc/sentences/search/",
        SentenceSearchView.as_view(),
        name="oanc-sentence-search",
    ),
    path(
        "reddit/comments/search/",
        CommentSearchView.as_view(),
        name="reddit-comment-search",
    ),
]
