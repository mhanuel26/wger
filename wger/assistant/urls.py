from django.conf.urls import (
    include,
    url
)

from wger.assistant import views

patterns_assistant = [
    url(r'^webhook$', views.webhook, name='webhook'),
]

urlpatterns = [
    url(r'^', include(patterns_assistant, namespace="assistant")),
]