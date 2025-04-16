from wagtail import hooks
from .models import ContentManagerGroup
from wagtail.snippets.models import register_snippet

register_snippet(ContentManagerGroup)