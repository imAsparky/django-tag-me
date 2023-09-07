# Generated by Django 4.2.4 on 2023-09-07 03:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaggedFieldModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(max_length=128)),
                ('model_verbose_name', models.CharField(max_length=128)),
                ('field_name', models.CharField(max_length=128)),
                ('field_verbose_name', models.CharField(max_length=128)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Tagged Field Model',
                'verbose_name_plural': 'Tagged Field Models',
            },
        ),
        migrations.CreateModel(
            name='UserTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('slug', models.SlugField(allow_unicode=True, max_length=100, unique=True, verbose_name='slug')),
                ('feature', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='Feature')),
                ('comment', models.CharField(blank=True, max_length=255, null=True, verbose_name='Comment')),
                ('field', models.CharField(blank=True, max_length=255, null=True, verbose_name='Field')),
                ('content_type', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_tag_content_id', to='contenttypes.contenttype', verbose_name='Content ID')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_tags', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User Tag',
                'verbose_name_plural': 'User Tags',
                'ordering': ['feature', 'field', 'name'],
                'indexes': [models.Index(fields=['user', 'content_type_id'], name='tag_me_user_user_id_0ef7f3_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='usertag',
            constraint=models.UniqueConstraint(fields=('user', 'content_type_id', 'field', 'name'), name='unique_user_field_tag'),
        ),
    ]
