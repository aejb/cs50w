from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.forms import ModelForm
from django.contrib.auth.decorators import login_required

from .models import *

## Model Forms ##

class NewListing(ModelForm):
    """
    Form inherited from the Listing model
    """

    class Meta:
        model = Listing
        fields = ("title", "description", "starting_bid", "category", "condition", "image")


class NewBid(ModelForm):
    """
    Form inherited from the Bid model
    """

    class Meta:
        model = Bid
        fields = ('bid',)


## Routes ##

def index(request):
    """
    `.` route
    """

    user_object = User.objects.filter(id=request.user.id).first()
    
    def view_listing(item, user):
        rv = {**item.__dict__}
        rv['condition'] = Condition.objects.get(id=rv['condition_id'])
        rv['category'] = Category.objects.get(id=rv['category_id'])
        rv['owner'] = User.objects.get(id=rv['owner_id'])
        rv['bids_count'] = item.bids.count()
        if user is not None:
            try:
                user_object.watchlist.get(item=item)
            except AttributeError:
                watching = False
            except Watch.DoesNotExist:
                rv["watching"] = False
            else:
                rv["watching"] = True
        if item.bids.last() is None:
            rv['highest_bid'] = item.starting_bid
        else:
            rv['highest_bid'] = item.bids.last().bid
        return rv

    view_listings = [view_listing(item, user_object) for item in Listing.objects.filter(sold=False)]

    return render(request, "auctions/index.html", {
        "listings": view_listings,
        "categories": Category.objects.all()
    })


@login_required
def watchlist(request):
    user_object = User.objects.filter(id=request.user.id).first()
    watch_list = user_object.watchlist.all()
    item_list = []
    for i in watch_list:
        item_list.append(i.item)

    def view_listing(item, user):
        rv = {**item.__dict__}
        rv['condition'] = Condition.objects.get(id=rv['condition_id'])
        rv['category'] = Category.objects.get(id=rv['category_id'])
        rv['owner'] = User.objects.get(id=rv['owner_id'])
        rv['bids_count'] = item.bids.count()
        if user is not None:
            try:
                user_object.watchlist.get(item=item)
            except AttributeError:
                watching = False
            except Watch.DoesNotExist:
                rv["watching"] = False
            else:
                rv["watching"] = True
        return rv

    view_listings = [view_listing(item, user_object) for item in item_list]
    
    return render(request, "auctions/watchlist.html", {
        "watchlist": view_listings
    })

@login_required
def sell(request, listing_id):
    """
    POST-only for the owner of a listing to sell it
    """
    item_object = Listing.objects.filter(id=listing_id).first()
    if request.user.id == item_object.owner.id:
        item_object.sold = True
        item_object.save()
    return HttpResponseRedirect(reverse('index'))

@login_required
def watch(request, listing_id):
    """
    POST-only route to toggle watching an item
    """
    if request.method == "POST":
        user_object = User.objects.filter(id=request.user.id).first()
        item_object = Listing.objects.filter(id=listing_id).first()
        try:
            watch_entry = user_object.watchlist.get(item=item_object)
        except AttributeError:
            watching = False
        except Watch.DoesNotExist:
            form = Watch(user=user_object, item=item_object)
            form.save()
        else:
            watch_entry.delete()
        next_page = request.POST.get('next', '/')
        return HttpResponseRedirect(next_page)
    else:
        return HttpResponseRedirect(reverse("index"))

@login_required
def comment(request, listing_id):
    if request.method == "POST":
        user_object = User.objects.filter(id=request.user.id).first()
        item_object = Listing.objects.filter(id=listing_id).first()
        new_comment = Comment(user=user_object, item=item_object, comment=request.POST['comment'])
        new_comment.save()
        return redirect(f'/listing/{listing_id}')
    return HttpResponse(request.POST['comment'])

@login_required
def bid(request, listing_id):
    """
    POST/DELETE-only route to submit a bid on a listing
    """
    if request.method == "POST":
        item_object = Listing.objects.filter(id=listing_id).first()
        user_object = User.objects.filter(id=request.user.id).first()
        
        if item_object.bids.last() is None:
            current_highest_bid = item_object.starting_bid
        else:
            current_highest_bid = item_object.bids.last().bid
        
        if float(request.POST['bid']) > float(current_highest_bid):
            new_bid = Bid(bidder=user_object, item=item_object, bid=request.POST['bid'])
            new_bid.save()
            return redirect(f'/listing/{listing_id}')


def category(request, category_id):
    """
    Shows all listings in the given category
    """

    user_object = User.objects.filter(id=request.user.id).first()
    
    def view_listing(item):
        rv = {**item.__dict__}
        rv['condition'] = Condition.objects.get(id=rv['condition_id'])
        rv['category'] = Category.objects.get(id=rv['category_id'])
        rv['owner'] = User.objects.get(id=rv['owner_id'])
        try:
            user_object.watchlist.get(item=item)
        except AttributeError:
            watching = False
        except Watch.DoesNotExist:
            rv["watching"] = False
        else:
            rv["watching"] = True
        return rv

    view_listings = [view_listing(item) for item in Listing.objects.filter(sold=False, category=category_id)]


    return render(request, "auctions/category.html", {
        "listings": view_listings,
        "this_category": Category.objects.filter(id=category_id).first(),
        "categories": Category.objects.all()
    })


def categories(request):
    """
    Shows all listings in the given category
    """
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all()
    })


def listing(request, listing_id):
    """
    Route for a specified listing
    """
    user_object = User.objects.filter(id=request.user.id).first()
    item_object = Listing.objects.filter(id=listing_id).first()

    try:
        user_object.watchlist.get(item=item_object)
    except AttributeError:
        watching = False
    except Watch.DoesNotExist:
        watching = False
    else:
        watching = True

    listing = Listing.objects.get(id=listing_id)

    highest_bid_object = item_object.bids.last()
    highest_bid = {}

    if highest_bid_object is None:
        highest_bid['bid'] = item_object.starting_bid
        highest_bid['user'] = item_object.owner
    else:
        highest_bid['bid'] = highest_bid_object.bid
        highest_bid['user'] = highest_bid_object.bidder
        highest_bid['id'] = highest_bid_object.id
    highest_bid['min'] = float(highest_bid['bid']) + 1
 
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": NewBid(),
        "categories": Category.objects.all(),
        "watching": watching,
        "highest_bid": highest_bid,
        "comments": item_object.comments.all()
    })

@login_required
def new_listing(request):
    """
    Route to create a new listing
    """
    if request.method == "GET":
        return render(request, "auctions/new_listing.html", {
            "form": NewListing(),
            "categories": Category.objects.all()
        })
    else:
        form = NewListing(request.POST)
        saved_form = form.save(commit=False)
        saved_form.owner = User.objects.get(id=request.user.id)
        saved_form.save()
        return HttpResponseRedirect(reverse("index"))


def login_view(request):
    """
    Log in (builtin)
    """
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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password.",
                "categories": Category.objects.all()
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    """
    Log out (builtin)
    """
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    """
    Register an account (builtin)
    """
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match.",
                "categories": Category.objects.all()
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
