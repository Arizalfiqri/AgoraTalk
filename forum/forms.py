from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Thread, Comment

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    jurusan = forms.CharField(max_length=100, required=False)
    angkatan = forms.CharField(max_length=4, required=False)
    
    class Meta:
        model = User
        fields = ("username", "email", "jurusan", "angkatan", "password1", "password2")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.jurusan = self.cleaned_data["jurusan"]
        user.angkatan = self.cleaned_data["angkatan"]
        user.role = 'mahasiswa'
        if commit:
            user.save()
        return user

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title', 'content', 'image', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Judul thread...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Tulis konten thread...'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2, tag3...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = True
        self.fields['category'].empty_label = "-- Pilih Komunitas --"
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Ukuran gambar tidak boleh lebih dari 10MB.")
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("File harus berupa gambar.")
        return image

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tulis komentar...'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'jurusan', 'angkatan', 'instagram', 'linkedin', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'jurusan': forms.TextInput(attrs={'class': 'form-control'}),
            'angkatan': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'linkedin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'linkedin.com/in/username'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }