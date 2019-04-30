from django.db.models import (
    CharField, Model, TextField,
    FloatField, DateTimeField, BooleanField,
    IntegerField, ForeignKey, DO_NOTHING
)
from jsonfield import JSONField


class Group(Model):
    id = CharField(max_length=24, unique=True, primary_key=True)
    name = CharField(max_length=32)
    alt = CharField(max_length=128)
    member_count = IntegerField()

    created = DateTimeField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Group'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.alt = self.alt.replace('\\', '')
        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)


class Post(Model):
    post_id = CharField(max_length=24, unique=True)
    group = ForeignKey(Group, on_delete=DO_NOTHING)
    author_info = JSONField(default={}, dump_kwargs={'ensure_ascii': False})
    alt = CharField(max_length=128)
    title = CharField(max_length=128)
    content = TextField()
    photo_list = JSONField(default=[], dump_kwargs={'ensure_ascii': False})

    rent = FloatField(null=True)
    subway = CharField(max_length=12, null=True)
    contact = CharField(max_length=68, null=True)

    is_matched = BooleanField(default=False)
    keyword_list = JSONField(default=[], dump_kwargs={'ensure_ascii': False})

    comment = CharField(max_length=128, null=True, blank=True)
    is_collected = BooleanField(default=False)

    created = DateTimeField()
    updated = DateTimeField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Post'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.alt = self.alt.replace('\\', '')
        self.photo_list = [i.replace('\\', '') for i in self.photo_list]
        self.author_info['alt'] = self.author_info['alt'].replace('\\', '')
        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)
