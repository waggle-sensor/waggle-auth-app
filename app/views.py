from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer
from .forms import UpdateSSHPublicKeysForm, CompleteLoginForm

User = get_user_model()


class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "username"


class UserSelfDetailView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class TokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, format=None) -> Response:
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({"token": token.key})


class UserAccessView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, username: str, format=None) -> Response:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404

        access_by_vsn = {}

        for access in ["develop", "schedule", "access_files"]:
            vsns = user.project_set.filter(**{
                f"usermembership__can_{access}": True,
                f"nodemembership__can_{access}": True,
            }).values_list("nodes__vsn", flat=True)

            for vsn in vsns:
                if vsn not in access_by_vsn:
                    access_by_vsn[vsn] = set()
                access_by_vsn[vsn].add(access)

        data = [{"vsn": vsn, "access": sorted(access)} for vsn, access in sorted(access_by_vsn.items())]

        return Response(data)


class UpdateSSHPublicKeysView(FormView):
    form_class = UpdateSSHPublicKeysForm
    template_name="update-my-keys.html"
    success_url = "/"
    
    def get_initial(self):
        return {
            "ssh_public_keys": self.request.user.ssh_public_keys
        }

    def form_valid(self, form) -> HttpResponse:
        cleaned_data = form.cleaned_data
        user = self.request.user
        user.ssh_public_keys = cleaned_data["ssh_public_keys"]
        user.save()
        return HttpResponseRedirect("/")


class CompleteLoginView(FormView):

    form_class = CompleteLoginForm
    template_name = None

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            user_info = request.session["oidc_auth_user_info"]
        except KeyError:
            return HttpResponseBadRequest("missing oidc_auth_user_info session key")

        try:
            sub = user_info["sub"]
        except KeyError:
            return HttpResponseBadRequest("missing oidc user info subject from session data")

        try:
            user = User.objects.get(id=sub)
        except User.DoesNotExist:
            return super().get(request)

        return self.login_and_redirect(user)

    def form_valid(self, form):
        cleaned_data = form.cleaned_data

        user_info = self.request.session["oidc_auth_user_info"]

        user = User.objects.create(
            id=user_info["sub"],
            username=cleaned_data["username"],
            name=user_info.get("name"),
            email=user_info.get("email"),
            organization=user_info.get("organization"),
        )

        return self.login_and_redirect(user)
    
    def login_and_redirect(self, user):
        login(self.request, user)
        return redirect(self.request.session.get("oidc_auth_next", settings.LOGIN_REDIRECT_URL))
