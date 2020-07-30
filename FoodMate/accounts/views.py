from django.shortcuts import render
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm
from django.contrib.auth.views import auth_login


def login(request):
    return render(request, 'accounts/login.html')


def agreement(request):
    return render(request, 'accounts/agreement.html')


def signup(request):
    if request.method == 'POST':
        signup_form = CustomUserCreationForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save()
            auth_login(request, user)
            return render(request, 'accounts/agreement.html')
        else:
            print(signup_form.errors)
            print(signup_form.non_field_errors())
            signup_form = CustomUserCreationForm()
            return render(request, 'accounts/signup.html', {'form': signup_form})
    else:
        signup_form = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'form': signup_form})

