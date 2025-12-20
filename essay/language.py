# essay/management/commands/create_languages.py
from django.core.management.base import BaseCommand
from essay.models import Language


class Command(BaseCommand):
    help = 'Create default languages'

    def handle(self, *args, **options):
        languages = [
            {'code': 'en', 'name': 'English'},
            {'code': 'ne', 'name': 'Nepali'},
            {'code': 'hi', 'name': 'Hindi'},
        ]
        
        created_count = 0
        for lang_data in languages:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults={'name': lang_data['name'], 'is_active': True}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created language: {language.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal languages created: {created_count}')
        )