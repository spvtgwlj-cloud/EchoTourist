export interface Tour {
  id: string;
  slug: string;
  name: string;
  subtitle?: string;
  description?: string;
  duration_days: number;
  duration_nights: number;
  start_price: number;
  currency: string;
  max_pax?: number;
  min_pax: number;
  difficulty: string;
  avg_rating: number;
  review_count: number;
  images: TourImage[];
  highlights: string[];
  includes: string[];
  excludes: string[];
  itinerary?: ItineraryDay[];
  destination_name?: string;
  category_name?: string;
  status: string;
  locale: string;
}

export interface TourImage {
  id: string;
  url: string;
  alt_text?: string;
  sort_order: number;
  type: string;  // "image" | "video"
}

export interface ItineraryDay {
  day: number;
  title: string;
  description: string;
  meals?: string[];
  accommodation?: string;
}

export interface TourDate {
  id: string;
  tour_id: string;
  start_date: string;
  end_date: string;
  price_per_pax: number;
  currency: string;
  availability: number;
  status: string;
}

export interface TourSearchResult {
  tours: Tour[];
  total: number;
  page: number;
  page_size: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  is_admin?: boolean;
  created_at: string;
}

export interface Order {
  id: string;
  order_no: string;
  tour_id: string;
  tour_name?: string;
  tour_date: string;
  status: string;
  pax_count: number;
  total: number;
  currency: string;
  contact_name: string;
  contact_email: string;
  created_at: string;
  payment_status?: string;
}

export interface BookingRequest {
  tour_id: string;
  tour_date_id: string;
  pax_count: number;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  special_requests?: string;
  locale: string;
}

export interface PaymentIntent {
  client_secret: string;
  session_id: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}
