from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from api.models import UserProfile

class IndexView(TemplateView):
    template_name = 'home/index.html'
    extra_context = {'main_selected': 'index'}

class LoginView(TemplateView):
    template_name = 'home/login.html'

    def get(self, request):
        context = {
            'main_selected': 'login',
            "form": LoginForm
        }
        if request.user.is_authenticated:
            return redirect('dashboard-index')
        return render(request, self.template_name, context=context)

    def post(self, request):
        context = {
            'main_selected': 'login',
            "form": LoginForm
        }
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(
            username=username, 
            password=password
        )
        if user is not None:
            login(request, user)
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.is_first_login and not user_profile.is_admin():
                user_profile.is_first_login = False
                user_profile.save()
                return redirect('home-first-login')
            return redirect('dashboard-index')
        else:
            context['error'] = 'Invalid credentials'
            return render(request, self.template_name, context=context)

class LogoutView(TemplateView):

    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect('home-index')

class FirstLoginView(TemplateView):
    template_name = 'home/first-login.html'