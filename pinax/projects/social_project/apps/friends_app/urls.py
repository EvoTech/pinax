from django.conf.urls.defaults import *



urlpatterns = patterns("",
    url(r"^$", "friends_app.views.friends", name="invitations"),
    url(r"^accept/(\w+)/$", "friends_app.views.accept_join", name="friends_accept_join"),
    url(r"^invite/$", "friends_app.views.invite", name="invite_to_join"),
)
