from app.models.attraction import Attraction, AttractionTranslation
from app.models.attraction_media import AttractionMedia
from app.models.attraction_ticket import AttractionTicket
from app.models.attraction_wishlist import AttractionWishlist
from app.models.custom_tour import (
    BaseService,
    CustomTourAttraction,
    CustomTourRequest,
    CustomTourSegment,
    CustomTourSegmentTour,
    CustomTourService,
)
from app.models.destination import Destination, DestinationTranslation
from app.models.enquiry import Enquiry
from app.models.order import Order, OrderPassenger
from app.models.review import Review
from app.models.tour import Tour, TourDate, TourImage, TourTranslation
from app.models.user import User
from app.models.wishlist import Wishlist

__all__ = [
    "Tour",
    "TourTranslation",
    "TourDate",
    "TourImage",
    "User",
    "Order",
    "OrderPassenger",
    "Review",
    "Destination",
    "DestinationTranslation",
    "Wishlist",
    "AttractionWishlist",
    "AttractionTicket",
    "Attraction",
    "AttractionTranslation",
    "AttractionMedia",
    "Enquiry",
    "BaseService",
    "CustomTourRequest",
    "CustomTourSegment",
    "CustomTourSegmentTour",
    "CustomTourAttraction",
    "CustomTourService",
]
