import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'essay_platform.settings')
import django
django.setup()
from essay.models import Language
Language.objects.get_or_create(code='en', defaults={'name':'English','is_active':True})
Language.objects.get_or_create(code='ne', defaults={'name':'Nepali','is_active':True})
Language.objects.get_or_create(code='hi', defaults={'name':'Hindi','is_active':True})
print("Languages added!")