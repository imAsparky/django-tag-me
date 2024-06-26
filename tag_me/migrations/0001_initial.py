# Generated by Django 5.0.2 on 2024-06-26 07:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TagMeSynchronise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='default', max_length=255)),
                ('synchronise', models.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                'verbose_name': 'Tags Synchronised',
                'verbose_name_plural': 'Tags Synchronised',
            },
        ),
        migrations.CreateModel(
            name='UserTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='This is the tag', max_length=50, verbose_name='Name')),
                ('slug', models.SlugField(allow_unicode=True, max_length=100, unique=True, verbose_name='slug')),
                ('model_verbose_name', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='Feature')),
                ('comment', models.CharField(blank=True, max_length=255, null=True, verbose_name='Comment')),
                ('field_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Field')),
            ],
            options={
                'verbose_name': 'User Tag',
                'verbose_name_plural': 'User Tags',
                'ordering': ['model_verbose_name', 'field_name', 'name'],
            },
        ),
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
        migrations.AddConstraint(
            model_name='tagmesynchronise',
            constraint=models.UniqueConstraint(fields=('name',), name='unique_tag_synchronise_name'),
        ),
        migrations.AddField(
            model_name='usertag',
            name='content_type',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_tag_content_id', to='contenttypes.contenttype', verbose_name='Content ID'),
        ),
        migrations.AddField(
            model_name='usertag',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_tags', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddIndex(
            model_name='usertag',
            index=models.Index(fields=['user', 'content_type_id'], name='tag_me_user_user_id_0ef7f3_idx'),
        ),
        migrations.AddConstraint(
            model_name='usertag',
            constraint=models.UniqueConstraint(fields=('user', 'content_type_id', 'field_name', 'name'), name='unique_user_field_tag'),
        ),
    ]
