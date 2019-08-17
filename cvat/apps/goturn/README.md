# Modification on Other APP Modules

## Setup REST API
**cvat/settings/base.py**  

add cvat.apps.goturn -> ‘INSTALLED_APPS’

## URLs
change **cvat/urls.py** add 

“if apps.is_installed('cvat.apps.goturn'):
    urlpatterns.append(path('goturn/', include('cvat.apps.goturn.urls')))”

## Database Model
**cvat/apps/engine/models.py**

TrackedShape: line 309, add “keyframe=models.BooleanField(default=True)”

**cvat/apps/engine/annotation.py**

add “trackedshape__keyframe”
