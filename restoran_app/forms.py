from django import forms

from .models import Restaurant


class RestaurantForm(forms.ModelForm):
    """فرم افزودن / ویرایش رستوران (فقط برای سوپریوزر)."""

    class Meta:
        model = Restaurant
        fields = ('name', 'kind', 'description', 'address', 'image', 'logo',
                  'categories', 'foods', 'rating', 'is_open')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام رستوران'}),
            'kind': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                 'placeholder': 'توضیحات رستوران'}),
            # FileInput (نه ClearableFileInput) تا متن انگلیسی Currently/Clear نیاید
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                             'placeholder': 'آدرس کامل رستوران'}),
            'foods': forms.CheckboxSelectMultiple(),
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'categories': forms.CheckboxSelectMultiple(),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }