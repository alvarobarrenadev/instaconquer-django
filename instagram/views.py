from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import RedirectURLMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from .forms import RegistrationForm, LoginForm
from profiles.forms import FollowForm
from profiles.models import Follow, UserProfile
from posts.models import Post

class HomeView(TemplateView):
    template_name = "general/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = Post.objects.select_related('user__profile')
        recent_profiles = UserProfile.objects.select_related('user').order_by('-pk')

        if self.request.user.is_authenticated:
            followed_users = Follow.objects.filter(
                follower__user=self.request.user,
            ).values_list('following__user', flat=True)
            posts = posts.filter(Q(user=self.request.user) | Q(user_id__in=followed_users))
            recent_profiles = recent_profiles.exclude(user=self.request.user)

        context['last_posts'] = posts.order_by('-created_at')[:10]
        context['recent_profiles'] = recent_profiles[:3]
        return context



class LoginView(RedirectURLMixin, FormView):
    template_name = "general/login.html"
    form_class = LoginForm
    next_page = reverse_lazy('home')

    def form_valid(self, form):
        usuario = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=usuario, password=password)

        if user is not None:
            login(self.request, user)
            messages.add_message(self.request, messages.SUCCESS, f'Bienvenido de nuevo {user.username}')
            return HttpResponseRedirect(self.get_success_url())

        else:
            messages.add_message(
                self.request, messages.ERROR, 'Usuario no válido o contraseña no válida')
            return super(LoginView, self).form_invalid(form)


class RegisterView(CreateView):
    template_name = "general/register.html"
    model = User
    success_url = reverse_lazy('login')
    form_class = RegistrationForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Usuario creado correctamente.")
        return super(RegisterView, self).form_valid(form)


class LegalView(TemplateView):
    template_name = "general/legal.html"


class ContactView(TemplateView):
    template_name = "general/contact.html"

@method_decorator(login_required, name='dispatch')
class ProfileDetailView(DetailView, FormView):
    model = UserProfile
    template_name = "general/profile_detail.html"
    context_object_name = "profile"
    form_class = FollowForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        follower = self.request.user.profile
        following = self.object

        if follower == following:
            messages.add_message(
                self.request,
                messages.ERROR,
                'No puedes seguirte a ti mismo.',
            )
            return HttpResponseRedirect(self.get_success_url())

        if Follow.objects.filter(
              follower=follower,
              following=following
        ).exists():
            Follow.objects.filter(
                  follower=follower,
                  following=following
              ).delete()
            messages.add_message(self.request, messages.SUCCESS, f"Se ha dejado de seguir a {following.user.username}")
        else:
            Follow.objects.get_or_create(
              follower=follower,
              following=following
            )
            messages.add_message(self.request, messages.SUCCESS, f"Se empieza a seguir a {following.user.username}")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profile_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Comprobamos si seguimos al usuario
        following = Follow.objects.filter(
            follower=self.request.user.profile,
            following=self.object,
        ).exists()
        context['following'] = following
        return context


class ProfileListView(ListView):
    model = UserProfile
    template_name = "general/profile_list.html"
    context_object_name = "profiles"

    def get_queryset(self):
        profiles = UserProfile.objects.select_related('user').order_by('user__username')
        if self.request.user.is_authenticated:
            return profiles.exclude(user=self.request.user)
        return profiles


@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = UserProfile
    template_name = "general/profile_update.html"
    context_object_name = "profile"
    fields = ['profile_picture', 'bio', 'birth_date']

    def dispatch(self, request, *args, **kwargs):
        user_profile = self.get_object()
        if user_profile.user != self.request.user:
            return HttpResponseRedirect(reverse('home'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Perfil editado correctamente.")
        return super(ProfileUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('profile_detail', args=[self.object.pk])


@login_required
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Se ha cerrado sesión correctamente.")
    return HttpResponseRedirect(reverse('home'))
