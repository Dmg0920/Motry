from django import forms
from .models import Post, Comment, Tag, Vehicle, UserVehicle


class PostCreateForm(forms.Form):
	vehicle_id = forms.IntegerField(widget=forms.HiddenInput)
	user_vehicle_id = forms.ChoiceField(required=False)
	body_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), max_length=2000)
	tags = forms.ModelMultipleChoiceField(
		queryset=Tag.objects.all(),
		widget=forms.SelectMultiple(attrs={"class": "form-select form-select--multi"}),
	)
	image_1 = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
	image_2 = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
	image_3 = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
	image_4 = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
	image_5 = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
	image_6 = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))

	def clean_tags(self):
		tags = self.cleaned_data.get("tags")
		count = tags.count() if tags is not None else 0
		if count < 1 or count > 3:
			raise forms.ValidationError("標籤需介於 1 到 3 個")
		return tags

	def images(self):
		"""返回所有上傳的圖片檔案"""
		images = []
		for i in range(1, 7):
			img = self.cleaned_data.get(f"image_{i}")
			if img:
				images.append(img)
		return images[:6]

	def clean_user_vehicle_id(self):
		value = self.cleaned_data.get("user_vehicle_id")
		if not value:
			return None
		try:
			return int(value)
		except (TypeError, ValueError):
			raise forms.ValidationError("選擇的車輛無效")


class CommentCreateForm(forms.ModelForm):
	image = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*", "placeholder": "上傳圖片（選填）"}))
	
	class Meta:
		model = Comment
		fields = ["post", "body_text", "image_url", "image"]
		widgets = {
			"post": forms.HiddenInput(),
			"body_text": forms.Textarea(attrs={"rows": 2}),
			"image_url": forms.URLInput(attrs={"placeholder": "圖片網址（選填，可替代檔案上傳）"}),
		}


TYPE_CHOICES = (
	("car", "汽車"),
	("bike", "機車"),
)

BRANDS_BY_TYPE = {
	"car": (
		("BMW", "BMW"),
		("Toyota", "Toyota"),
		("Mercedes-Benz", "Mercedes-Benz"),
		("Audi", "Audi"),
		("Porsche", "Porsche"),
	),
	"bike": (
		("Yamaha", "Yamaha"),
		("Honda", "Honda"),
		("Kawasaki", "Kawasaki"),
		("Suzuki", "Suzuki"),
		("Ducati", "Ducati"),
		("KTM", "KTM"),
	),
}


class VehicleCreateForm(forms.ModelForm):
	# 用選單限制輸入；實際存回文字欄位
	type = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
	brand = forms.ChoiceField(choices=(), widget=forms.Select(attrs={"class": "form-select"}))
	cover_url = forms.URLField(required=False)
	intro_md = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)

	def __init__(self, *args, **kwargs):
		selected_type = kwargs.pop("selected_type", None)
		super().__init__(*args, **kwargs)
		if selected_type in BRANDS_BY_TYPE:
			self.fields["brand"].choices = BRANDS_BY_TYPE[selected_type]
			self.fields["type"].initial = selected_type
		else:
			# 預設用 car 清單（或可合併兩者）
			self.fields["brand"].choices = BRANDS_BY_TYPE["car"]
		self.fields["brand"].widget.attrs.setdefault("class", "form-select")

	class Meta:
		model = Vehicle
		fields = [
			"type",
			"brand",
			"model",
			"generation",
			"years_from",
			"years_to",
			"displacement_cc",
			"cylinders",
			"horsepower_ps",
			"msrp_new",
			"used_price_min",
			"used_price_max",
			"intro_md",
			"cover_url",
		]


class UserVehicleForm(forms.ModelForm):
	vehicle = forms.ModelChoiceField(queryset=Vehicle.objects.none(), widget=forms.Select(attrs={"class": "form-select"}))
	alias = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "車輛暱稱（選填）"}))
	notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "想分享的改裝、歷程…"}))
	image_url = forms.URLField(required=False, widget=forms.URLInput(attrs={"placeholder": "圖片網址（選填，可替代檔案上傳）"}))
	image = forms.ImageField(required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
	
	class Meta:
		model = UserVehicle
		fields = ["vehicle", "alias", "notes", "image_url", "image"]

	def __init__(self, user, *args, **kwargs):
		super().__init__(*args, **kwargs)
		existing_ids = user.user_vehicles.values_list("vehicle_id", flat=True)
		qs = Vehicle.objects.order_by("brand", "model")
		if existing_ids:
			qs = qs.exclude(id__in=existing_ids)
		self.fields["vehicle"].queryset = qs


class RatingForm(forms.Form):
	score = forms.ChoiceField(
		choices=[(str(i), f"{i} 分") for i in range(1, 6)],
		widget=forms.Select(attrs={"class": "form-select form-select--compact"}),
	)
