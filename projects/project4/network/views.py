import json
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import User, Post, Like


def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

@csrf_exempt
def post(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            if data.get("content") == "":
                return JsonResponse({
                    "error": "Post must contain at least one character."
                }, status=400)
            post = Post(
                user=request.user,
                content=data.get("content")
            )
            post.save()
            return JsonResponse({"message": "Post sent successfully."}, status=201)
        else:
            return JsonResponse({
                    "error": "You must be logged in to send a Post."
                }, status=400)
    elif request.method == "GET":
        posts = Post.objects.all()
        posts_dict = [post.serialize() for post in posts]
        for post in posts_dict:
            post['liked'] = True if request.user.likes.filter(post=Post.objects.get(id=post['id'])).exists() else False
        return JsonResponse(posts_dict, safe=False)
    else:
        return JsonResponse({"error": "POST or GET request required."}, status=400)

@csrf_exempt
def get_post(request, post_id):
    if request.method == "GET":
        try:
            post = Post.objects.get(user=request.user, pk=post_id)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)
        post_dict = post.serialize()
        post_dict['liked'] = True if request.user.likes.filter(post=post).exists() else False
        print(post_dict)
        return JsonResponse(post_dict)

@csrf_exempt
def likes(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            like = Like.objects.get(user=request.user, post=Post.objects.get(id=post_id))
        except Like.DoesNotExist:
            if data.get("like"):
                like = Like(
                    user=request.user,
                    post=Post.objects.get(user=request.user, pk=post_id)
                )
                like.save()
                return JsonResponse({'message': 'Post liked successfully.'}, status=200)
            else:
                return JsonResponse({'message': 'Post unliked successfully.'}, status=200)
        else:
            print("like")
            print(data.get("like"))
            if data.get("like"):
                return JsonResponse({'message': 'Post liked successfully.'}, status=200)
            else:
                like.delete()
                return JsonResponse({'message': 'Post unliked successfully.'}, status=200)