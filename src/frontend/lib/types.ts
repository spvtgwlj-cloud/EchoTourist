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
  theme: string;
  sort_order?: number;
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
  tour_id?: string;
  tour_name?: string;
  tour_date: string;
  attraction_id?: string;
  attraction_name?: string;
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
  tour_id?: string;
  tour_date_id?: string;
  attraction_id?: string;
  attraction_ticket_id?: string;
  pax_count: number;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  special_requests?: string;
  locale: string;
}

export interface AttractionTicket {
  id: string;
  attraction_id: string;
  ticket_type: string;
  price: number;
  currency: string;
  availability: number;
  status: string;
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

// ── 自定制旅程 Types（支持多段行程）─────────────────────────

export interface BaseService {
  id: string;
  name: string;
  name_zh?: string;
  name_es?: string;
  name_fr?: string;
  description?: string;
  description_zh?: string;
  description_es?: string;
  description_fr?: string;
  unit_type: 'per_day' | 'per_pax' | 'per_trip';
  unit_price: number;
  currency: string;
  category?: string;
  sort_order: number;
  status: string;
}

export interface CustomTourServiceInput {
  service_id: string;
  quantity: number;
}

/** 一段行程的输入 */
export interface CustomTourSegmentInput {
  destination_id?: string;
  custom_destination?: string;
  start_date: string;
  end_date: string;
  attraction_ids: string[];
  tour_ids: string[];
}

export interface CustomTourCreateRequest {
  segments: CustomTourSegmentInput[];
  pax_count: number;
  guide_language?: string;
  services: CustomTourServiceInput[];
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  special_requests?: string;
  locale: string;
}

export interface CustomTourSegmentTour {
  id: string;
  tour_id: string;
  tour_name: string;
}

export interface CustomTourSegmentItem {
  id: string;
  segment_order: number;
  destination_id: string;
  destination_name: string;
  start_date: string;
  end_date: string;
  attractions: { id: string; attraction_id: string; attraction_name: string; sort_order: number }[];
  selected_tours: CustomTourSegmentTour[];
}

export interface CustomTourServiceItem {
  id: string;
  service_id: string;
  service_name: string;
  unit_type: string;
  quantity: number;
  unit_price_snapshot: number;
  subtotal: number;
}

export interface CustomTourRequest {
  id: string;
  request_no: string;
  user_id?: string;
  pax_count: number;
  guide_language?: string;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  special_requests?: string;
  subtotal: number;
  confirmed_price?: number;
  currency: string;
  status: string;
  admin_notes?: string;
  locale: string;
  segments: CustomTourSegmentItem[];
  services: CustomTourServiceItem[];
  created_at: string;
  updated_at: string;
}
