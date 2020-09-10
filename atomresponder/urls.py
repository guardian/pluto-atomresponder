from django.urls import path,re_path
from .views import JobNotifyView, ImportJobListView #, ResyncToAtomApi
# This new app handles the request to the URL by responding with the view which is loaded
# from portal.plugins.gnmkinesisresponder.views.py. Inside that file is a class which responsedxs to the
# request, and sends in the arguments template - the html file to view.
# name is shortcut name for the urls.

urlpatterns = [
   path(r'jobnotify', JobNotifyView.as_view(), name='import_notification'),
   path(r'admin/jobs', ImportJobListView.as_view(), name='job_list'),
   #re_path(r'^resync/(?P<item_id>\w{2}-\d+)$', ResyncToAtomApi.as_view(), name='resync_to_atom')
]
