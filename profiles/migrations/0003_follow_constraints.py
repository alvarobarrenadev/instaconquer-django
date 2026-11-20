from django.db import migrations, models


def clean_invalid_follows(apps, schema_editor):
    Follow = apps.get_model('profiles', 'Follow')
    seen = set()

    for follow in Follow.objects.order_by('pk').iterator():
        pair = (follow.follower_id, follow.following_id)
        if follow.follower_id == follow.following_id or pair in seen:
            follow.delete()
        else:
            seen.add(pair)


class Migration(migrations.Migration):
    dependencies = [
        ('profiles', '0002_remove_userprofile_followers'),
    ]

    operations = [
        migrations.RunPython(clean_invalid_follows, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(
                fields=('follower', 'following'),
                name='unique_follow',
            ),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')),
                name='prevent_self_follow',
            ),
        ),
    ]
