from django.db import migrations


TAG_DEFAULTS = [
	"舒適通勤",
	"運動性能",
	"節能省油",
	"長途旅行",
	"新手友善",
	"家庭首選",
	"越野冒險",
	"科技配備",
	"豪華旗艦",
	"性價比高",
]


def create_default_tags(apps, schema_editor):
	Tag = apps.get_model("motry", "Tag")
	for name in TAG_DEFAULTS:
		Tag.objects.get_or_create(name=name)


def remove_default_tags(apps, schema_editor):
	Tag = apps.get_model("motry", "Tag")
	Tag.objects.filter(name__in=TAG_DEFAULTS).delete()


class Migration(migrations.Migration):
	dependencies = [
		("motry", "0001_initial"),
	]

	operations = [
		migrations.RunPython(create_default_tags, remove_default_tags),
	]
