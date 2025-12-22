from django import forms
from .models import Post, Comment, Tag, Vehicle, UserVehicle, VehicleImage


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
		fields = ["post", "parent", "body_text", "image_url", "image"]
		widgets = {
			"post": forms.HiddenInput(),
			"parent": forms.HiddenInput(),
			"body_text": forms.Textarea(attrs={"rows": 2}),
			"image_url": forms.URLInput(attrs={"placeholder": "圖片網址（選填，可替代檔案上傳）"}),
		}

	def clean(self):
		cleaned_data = super().clean()
		parent = cleaned_data.get("parent")
		post = cleaned_data.get("post")
		if parent and post and parent.post_id != post.id:
			self.add_error("parent", "回覆的留言不屬於此貼文。")
		return cleaned_data


BRAND_CHOICES = (
	("Yamaha", "Yamaha"),
	("Honda", "Honda"),
	("Kawasaki", "Kawasaki"),
	("Suzuki", "Suzuki"),
	("Ducati", "Ducati"),
	("KTM", "KTM"),
)


class VehicleCreateForm(forms.ModelForm):
	# 用選單限制輸入；實際存回文字欄位
	brand = forms.ChoiceField(choices=BRAND_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
	cover_url = forms.URLField(required=False)
	intro_md = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)

	class Meta:
		model = Vehicle
		fields = [
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


class VehicleIntroForm(forms.ModelForm):
	intro_md = forms.CharField(
		required=False,
		label="車輛簡介",
		widget=forms.Textarea(
			attrs={
				"rows": 8,
				"placeholder": "介紹這台車的定位、世代演進、技術亮點或值得一提的故事，並附上可信來源。",
				"class": "vehicle-intro__textarea",
			}
		),
		help_text="可使用 Markdown 語法；請引用可信來源並保持中立語氣。",
	)

	class Meta:
		model = Vehicle
		fields = ["intro_md"]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields["intro_md"].widget.attrs["data-intro-input"] = "true"


class VehiclePhotoForm(forms.ModelForm):
	image = forms.ImageField(
		required=False,
		widget=forms.FileInput(attrs={"accept": "image/*", "class": "vehicle-photo__file-input"}),
		label="上傳圖片",
	)
	image_url = forms.URLField(
		required=False,
		widget=forms.URLInput(
			attrs={
				"placeholder": "或貼上圖片網址（需為公開圖片）",
				"class": "vehicle-photo__url-input",
			}
		),
		label="圖片網址",
	)

	class Meta:
		model = VehicleImage
		fields = ["image", "image_url"]

	def clean(self):
		data = super().clean()
		if not data.get("image") and not data.get("image_url"):
			raise forms.ValidationError("請上傳圖片或貼上圖片網址，至少擇一。")
		return data
