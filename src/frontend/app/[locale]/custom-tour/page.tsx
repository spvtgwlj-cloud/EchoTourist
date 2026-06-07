'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import type { Tour, BaseService, CustomTourCreateRequest, CustomTourSegmentInput } from '@/lib/types';
import {
  MapPin, CalendarDays, Users, Globe, Landmark, Wrench,
  ChevronRight, ChevronLeft, Check, Send, Loader2, ArrowLeft,
  Phone, Plus, Minus, Trash2, BookCopy, Info
} from 'lucide-react';
import AttractionInfoModal from '@/components/attractions/AttractionInfoModal';

interface DestinationItem {
  id: string;
  slug: string;
  name: string;
}

interface AttractionItem {
  id: string;
  slug: string;
  name: string;
  description?: string;
  image_url?: string;
  rating?: number;
  ticket_price?: number;
  ticket_currency?: string;
  destination_id: string;
  tickets?: Array<{ id: string; ticket_type: string; price: number; currency: string; availability: number; status: string }>;
  media?: Array<{ id: string; url: string; media_type: string; alt_text?: string; sort_order: number }>;
}

// 导游语言预设选项
const GUIDE_LANGUAGE_OPTIONS = [
  { value: 'English', labelKey: 'guideLangEn' },
  { value: 'Spanish', labelKey: 'guideLangEs' },
  { value: 'French', labelKey: 'guideLangFr' },
  { value: 'Chinese (Mandarin)', labelKey: 'guideLangZh' },
];

interface SegmentForm {
  destination_id: string;
  custom_destination: string;  // 当用户选择了"其他目的地"时存储自定义地址
  isCustomDest: boolean;       // 用户是否选择了"其他目的地"
  start_date: string;
  end_date: string;
  attraction_ids: string[];
  tour_ids: string[];
}

const emptySegment = (): SegmentForm => ({
  destination_id: '',
  custom_destination: '',
  isCustomDest: false,
  start_date: '',
  end_date: '',
  attraction_ids: [],
  tour_ids: [],
});

const STEPS = ['step1', 'step2', 'step3', 'step4'] as const;

export default function CustomTourPage() {
  const t = useTranslations('customTour');
  const locale = useLocale();
  const router = useRouter();

  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submittedId, setSubmittedId] = useState('');

  // Data lists
  const [destinations, setDestinations] = useState<DestinationItem[]>([]);
  const [attractions, setAttractions] = useState<AttractionItem[]>([]);
  const [baseServices, setBaseServices] = useState<BaseService[]>([]);
  const [tours, setTours] = useState<Tour[]>([]);

  // ── Form fields ─────────────────────────────────────────────
  // Guide language: presets with custom override
  const [guideLangPreset, setGuideLangPreset] = useState('');
  const [guideLangCustom, setGuideLangCustom] = useState('');

  const guideLanguage = guideLangPreset === '__custom__' ? guideLangCustom : guideLangPreset;

  const [paxCount, setPaxCount] = useState(2);

  // Segments (at least 1)
  const [segments, setSegments] = useState<SegmentForm[]>([emptySegment()]);

  // Services
  const [selectedServices, setSelectedServices] = useState<{ service_id: string; quantity: number }[]>([]);

  // Contact
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [specialRequests, setSpecialRequests] = useState('');

  // Price
  const [estimatedPrice, setEstimatedPrice] = useState<number | null>(null);

  // Attraction info modal
  const [infoAttraction, setInfoAttraction] = useState<AttractionItem | null>(null);

  // ── Load data ───────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      api.get<{ destinations: DestinationItem[] }>('/destinations?locale=' + locale),
      api.get<{ attractions: AttractionItem[] }>('/attractions?locale=' + locale),
      api.get<{ services: BaseService[]; total: number }>('/custom-tours/base-services?locale=' + locale),
      api.get<{ tours: Tour[] }>('/tours?locale=' + locale + '&page_size=50&status=published'),
    ])
      .then(([destRes, attrRes, svcRes, tourRes]) => {
        setDestinations(destRes.destinations || []);
        setAttractions(attrRes.attractions || []);
        setBaseServices(svcRes.services || []);
        setTours(tourRes.tours || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [locale]);

  // ── Segment helpers ─────────────────────────────────────────
  const updateSegment = (idx: number, patch: Partial<SegmentForm>) => {
    setSegments(prev => prev.map((s, i) => i === idx ? { ...s, ...patch } : s));
  };

  const addSegment = () => setSegments(prev => [...prev, emptySegment()]);
  const removeSegment = (idx: number) => {
    if (segments.length <= 1) return;
    setSegments(prev => prev.filter((_, i) => i !== idx));
  };

  const toggleAttraction = (segIdx: number, attrId: string) => {
    updateSegment(segIdx, {
      attraction_ids: segments[segIdx].attraction_ids.includes(attrId)
        ? segments[segIdx].attraction_ids.filter(id => id !== attrId)
        : [...segments[segIdx].attraction_ids, attrId],
    });
  };

  const toggleTour = (segIdx: number, tourId: string) => {
    updateSegment(segIdx, {
      tour_ids: segments[segIdx].tour_ids.includes(tourId)
        ? segments[segIdx].tour_ids.filter(id => id !== tourId)
        : [...segments[segIdx].tour_ids, tourId],
    });
  };

  // ── Service helpers ─────────────────────────────────────────
  const updateService = (serviceId: string, delta: number) => {
    setSelectedServices(prev => {
      const exists = prev.find(s => s.service_id === serviceId);
      if (exists) {
        const newQty = Math.max(0, exists.quantity + delta);
        if (newQty === 0) return prev.filter(s => s.service_id !== serviceId);
        return prev.map(s => s.service_id === serviceId ? { ...s, quantity: newQty } : s);
      }
      if (delta > 0) return [...prev, { service_id: serviceId, quantity: 1 }];
      return prev;
    });
  };

  const getServiceQty = (serviceId: string) =>
    selectedServices.find(s => s.service_id === serviceId)?.quantity || 0;

  // ── Price calculation ───────────────────────────────────────
  const recalcPrice = useCallback(async () => {
    const isValid = segments.some(s => (s.destination_id || s.isCustomDest) && s.start_date && s.end_date);
    if (!isValid) { setEstimatedPrice(null); return; }

    const totalDays = segments.reduce((sum, s) => {
      if (!s.start_date || !s.end_date) return sum;
      return sum + Math.max(1, (new Date(s.end_date).getTime() - new Date(s.start_date).getTime()) / (1000 * 60 * 60 * 24));
    }, 0);

    try {
      const res = await api.post<{ subtotal: number }>('/custom-tours/quote', {
        segments: segments.map(s => ({
          destination_id: s.destination_id,
          start_date: s.start_date,
          end_date: s.end_date,
          attraction_ids: s.attraction_ids,
          tour_ids: s.tour_ids,
        })),
        pax_count: paxCount,
        guide_language: guideLanguage || undefined,
        services: selectedServices.map(s => ({ service_id: s.service_id, quantity: s.quantity })),
        contact_name: contactName || 'temp',
        contact_email: contactEmail || 'temp@temp.com',
        locale,
      });
      setEstimatedPrice(res.subtotal);
    } catch {
      // Fallback local calculation
      let svcTotal = 0;
      for (const s of selectedServices) {
        const svc = baseServices.find(b => b.id === s.service_id);
        if (!svc) continue;
        if (svc.unit_type === 'per_day') svcTotal += svc.unit_price * s.quantity * totalDays;
        else if (svc.unit_type === 'per_pax') svcTotal += svc.unit_price * s.quantity * paxCount;
        else svcTotal += svc.unit_price * s.quantity;
      }
      setEstimatedPrice(Math.round(svcTotal * 100) / 100);
    }
  }, [segments, paxCount, guideLanguage, selectedServices, contactName, contactEmail, locale, baseServices]);

  useEffect(() => {
    const hasAnyData = segments.some(s => s.destination_id && s.start_date && s.end_date);
    if (hasAnyData) recalcPrice();
  }, [segments, paxCount, selectedServices, recalcPrice]);

  // ── Validation ──────────────────────────────────────────────
  const validateSegments = () => {
    return segments.every(s => (s.destination_id || (s.isCustomDest && s.custom_destination.trim())) && s.start_date && s.end_date);
  };

  const canProceedStep = (step: number) => {
    switch (step) {
      case 0: return validateSegments();
      case 1: return true;
      case 2: return true;
      case 3: return !!contactName && !!contactEmail;
      default: return true;
    }
  };

  // ── Navigation ──────────────────────────────────────────────
  const handleNext = () => {
    if (canProceedStep(currentStep) && currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };
  const handlePrev = () => {
    if (currentStep > 0) { setCurrentStep(currentStep - 1); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  };

  // ── Submit ──────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!canProceedStep(3)) return;
    setSubmitting(true);
    try {
      const body: CustomTourCreateRequest = {
        segments: segments.map(s => ({
          destination_id: s.isCustomDest ? undefined : s.destination_id,
          custom_destination: s.isCustomDest ? s.custom_destination : undefined,
          start_date: s.start_date,
          end_date: s.end_date,
          attraction_ids: s.attraction_ids,
          tour_ids: s.tour_ids,
        })),
        pax_count: paxCount,
        guide_language: guideLanguage || undefined,
        services: selectedServices.map(s => ({ service_id: s.service_id, quantity: s.quantity })),
        contact_name: contactName,
        contact_email: contactEmail,
        contact_phone: contactPhone || undefined,
        special_requests: specialRequests || undefined,
        locale,
      };
      const res = await api.post<{ status: string; request: { id: string } }>('/custom-tours/requests', body);
      setSubmitted(true);
      setSubmittedId(res.request.id);
    } catch (e: any) {
      alert(e?.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  // ── Loading ─────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <Skeleton className="h-10 w-64 mb-6" />
        <Skeleton className="h-6 w-96 mb-12" />
        <div className="space-y-4">{[1,2,3].map(i => <Skeleton key={i} className="h-20 w-full" />)}</div>
      </div>
    );
  }

  // ── Success ─────────────────────────────────────────────────
  if (submitted) {
    return (
      <div className="container mx-auto px-4 py-20 max-w-2xl text-center">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-green-100 mb-6">
          <Check className="h-10 w-10 text-green-600" />
        </div>
        <h1 className="text-3xl font-bold mb-4">{t('submitted')}</h1>
        <p className="text-muted-foreground mb-6 max-w-md mx-auto">{t('submittedDesc')}</p>
        <div className="flex justify-center gap-4">
          <Button onClick={() => router.push(`/${locale}/user/custom-requests`)}>{t('viewRequest')}</Button>
          <Link href={`/${locale}`}><Button variant="outline">{t('backToHome')}</Button></Link>
        </div>
      </div>
    );
  }

  // ── Derived ─────────────────────────────────────────────────
  const totalDays = segments.reduce((sum, s) => {
    if (!s.start_date || !s.end_date) return sum;
    return sum + Math.max(1, (new Date(s.end_date).getTime() - new Date(s.start_date).getTime()) / (1000 * 60 * 60 * 24));
  }, 0);

  return (
    <div className="container mx-auto px-4 py-12 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{t('title')}</h1>
        <p className="text-muted-foreground mt-2">{t('subtitle')}</p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-2 mb-10">
        {STEPS.map((step, i) => (
          <div key={step} className="flex items-center gap-2">
            <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
              i <= currentStep ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'
            }`}>{i + 1}</div>
            <span className={`text-sm hidden sm:inline ${i <= currentStep ? 'text-primary font-medium' : 'text-gray-400'}`}>
              {t(step)}
            </span>
            {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4 text-gray-300" />}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* ── Main Form ──────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-6">

          {/* Step 1: Travel Details (Multi-segment + Guide Language) */}
          {currentStep === 0 && (
            <>
              {/* Guide Language — 放在旅游基本信息最前 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5 text-primary" />
                    {t('guideLanguage')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {GUIDE_LANGUAGE_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setGuideLangPreset(opt.value)}
                        className={`px-4 py-2 rounded-full text-sm border transition-colors ${
                          guideLangPreset === opt.value
                            ? 'bg-primary text-white border-primary'
                            : 'bg-white border-gray-200 hover:border-gray-300 text-muted-foreground'
                        }`}
                      >
                        {opt.value}
                      </button>
                    ))}
                    <button
                      onClick={() => setGuideLangPreset('__custom__')}
                      className={`px-4 py-2 rounded-full text-sm border transition-colors ${
                        guideLangPreset === '__custom__'
                          ? 'bg-primary text-white border-primary'
                          : 'bg-white border-gray-200 hover:border-gray-300 text-muted-foreground'
                      }`}
                    >
                      Other/自定义
                    </button>
                  </div>
                  {guideLangPreset === '__custom__' && (
                    <Input
                      placeholder="Please specify your preferred guide language / 请指定您偏好的导游语言"
                      value={guideLangCustom}
                      onChange={e => setGuideLangCustom(e.target.value)}
                    />
                  )}
                </CardContent>
              </Card>

              {/* Pax Count */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    {t('paxCount')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-3">
                    <Button variant="outline" size="sm" onClick={() => setPaxCount(Math.max(1, paxCount - 1))} disabled={paxCount <= 1}>
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="text-lg font-semibold w-8 text-center">{paxCount}</span>
                    <Button variant="outline" size="sm" onClick={() => setPaxCount(Math.min(100, paxCount + 1))}>
                      <Plus className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-muted-foreground">{t('people')}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Multi-segment Itinerary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-primary" />
                    {t('itinerarySegments') || 'Itinerary Segments'}
                  </CardTitle>
                  <CardDescription>
                    {t('addSegmentsHint') || 'Add multiple segments for multi-city itineraries'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {segments.map((seg, idx) => (
                    <div key={idx} className="p-4 border rounded-lg bg-gray-50/50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-semibold text-primary">
                          {t('segmentLabel') || 'Segment'} {idx + 1}
                        </span>
                        {segments.length > 1 && (
                          <Button variant="ghost" size="sm" className="text-red-500" onClick={() => removeSegment(idx)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>

                      <div className="space-y-3">
                        {/* Destination */}
                        <div>
                          <Label>{t('destination')} *</Label>
                          <select
                            value={seg.isCustomDest ? '__custom__' : seg.destination_id}
                            onChange={e => {
                              const val = e.target.value;
                              if (val === '__custom__') {
                                updateSegment(idx, { destination_id: '', custom_destination: '', isCustomDest: true });
                              } else {
                                updateSegment(idx, { destination_id: val, custom_destination: '', isCustomDest: false });
                              }
                            }}
                            className="w-full h-10 px-3 rounded-md border border-input bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary mt-1"
                          >
                            <option value="">{t('selectDestination')}</option>
                            {destinations.map(d => (
                              <option key={d.id} value={d.id}>{d.name}</option>
                            ))}
                            <option value="__custom__">{t('otherDestination') || '其他目的地 / Other Destination'}</option>
                          </select>
                          {seg.isCustomDest && (
                            <div className="mt-2">
                              <input
                                type="text"
                                placeholder={t('customDestinationPlaceholder') || '请输入目的地地址 / Enter destination address'}
                                value={seg.custom_destination}
                                onChange={e => updateSegment(idx, { custom_destination: e.target.value })}
                                className="w-full h-10 px-3 rounded-md border border-input bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                              />
                            </div>
                          )}
                        </div>

                        {/* Dates */}
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label>{t('startDate')} *</Label>
                            <Input
                              type="date"
                              value={seg.start_date}
                              onChange={e => updateSegment(idx, { start_date: e.target.value })}
                              min={new Date().toISOString().split('T')[0]}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <Label>{t('endDate')} *</Label>
                            <Input
                              type="date"
                              value={seg.end_date}
                              onChange={e => updateSegment(idx, { end_date: e.target.value })}
                              min={seg.start_date || new Date().toISOString().split('T')[0]}
                              className="mt-1"
                            />
                          </div>
                        </div>

                        {/* Attractions for this segment */}
                        <div>
                          <Label className="mb-1 block">{t('chooseAttractions')}</Label>
                          <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                            {attractions
                              .filter(a => !seg.destination_id || a.destination_id === seg.destination_id)
                              .map(attr => (
                                <div
                                  key={attr.id}
                                  className={`flex items-center gap-1 p-2 rounded border cursor-pointer text-xs transition-colors ${
                                    seg.attraction_ids.includes(attr.id)
                                      ? 'border-primary bg-primary/5'
                                      : 'border-gray-200 hover:border-gray-300'
                                  }`}
                                >
                                  <div
                                    className="flex items-center gap-1 flex-1 min-w-0"
                                    onClick={() => toggleAttraction(idx, attr.id)}
                                  >
                                    <div className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                                      seg.attraction_ids.includes(attr.id)
                                        ? 'bg-primary border-primary text-white'
                                        : 'border-gray-300'
                                    }`}>
                                      {seg.attraction_ids.includes(attr.id) && <Check className="h-2.5 w-2.5" />}
                                    </div>
                                    <span className="truncate">{attr.name}</span>
                                  </div>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.stopPropagation(); setInfoAttraction(attr); }}
                                    className="shrink-0 p-0.5 rounded hover:bg-gray-200 text-muted-foreground hover:text-primary transition-colors"
                                    title="View details"
                                  >
                                    <Info className="h-3 w-3" />
                                  </button>
                                </div>
                              ))}
                            {attractions.filter(a => !seg.destination_id || a.destination_id === seg.destination_id).length === 0 && (
                              <p className="text-xs text-muted-foreground col-span-2 py-2 text-center">
                                {t('noAttractionsForDest') || 'No attractions for this destination'}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Existing Tour Products — 支持多选 */}
                        <div>
                          <Label className="mb-1 block">{t('selectExistingTours') || 'Select Existing Tours'}</Label>
                          <div className="max-h-40 overflow-y-auto space-y-1">
                            {tours.filter(t => t.status === 'published').map(tour => (
                              <label
                                key={tour.id}
                                className={`flex items-center gap-2 p-2 rounded border cursor-pointer text-xs transition-colors ${
                                  seg.tour_ids.includes(tour.id)
                                    ? 'border-primary bg-primary/5'
                                    : 'border-gray-200 hover:border-gray-300'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={seg.tour_ids.includes(tour.id)}
                                  onChange={() => toggleTour(idx, tour.id)}
                                  className="accent-primary"
                                />
                                <span className="truncate">{tour.name} ({tour.duration_days}d, ${tour.start_price})</span>
                              </label>
                            ))}
                            {tours.filter(t => t.status === 'published').length === 0 && (
                              <p className="text-xs text-muted-foreground py-2">{t('noToursAvailable') || 'No tours available'}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Add Segment Button */}
                  <Button variant="outline" onClick={addSegment} className="w-full">
                    <Plus className="h-4 w-4 mr-2" />
                    {t('addSegment') || 'Add Segment'}
                  </Button>
                </CardContent>
              </Card>
            </>
          )}

          {/* Step 2: Attractions Overview (per segment, already handled in step 1) */}
          {currentStep === 1 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Landmark className="h-5 w-5 text-primary" />
                  {t('chooseAttractions')}
                </CardTitle>
                <CardDescription>{t('chooseAttractionsDesc')}</CardDescription>
              </CardHeader>
              <CardContent>
                {segments.map((seg, idx) => {
                  const dest = destinations.find(d => d.id === seg.destination_id);
                  const destDisplay = seg.isCustomDest ? seg.custom_destination : (dest?.name || '-');
                  const segAttractions = attractions.filter(a => seg.attraction_ids.includes(a.id));
                  const segTours = tours.filter(t => seg.tour_ids.includes(t.id));
                  return (
                    <div key={idx} className="mb-4 p-3 border rounded-lg">
                      <p className="text-sm font-semibold text-primary mb-2">
                        {t('segmentLabel') || 'Segment'} {idx + 1}: {destDisplay}
                      </p>
                      {segAttractions.length > 0 && (
                        <div className="mb-2">
                          <p className="text-xs text-muted-foreground mb-1">{t('chooseAttractions')}:</p>
                          <div className="flex flex-wrap gap-1">
                            {segAttractions.map(a => (
                              <span
                                key={a.id}
                                onClick={() => setInfoAttraction(attractions.find(at => at.id === a.id) || a)}
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700 cursor-pointer hover:bg-blue-100 transition-colors"
                                title="View details"
                              >
                                {a.name}
                                <Info className="h-2.5 w-2.5 opacity-50" />
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {segTours.length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">{t('baseTour')}:</p>
                          <div className="flex flex-wrap gap-1">
                            {segTours.map(t => (
                              <span key={t.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-50 text-green-700">
                                {t.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {segAttractions.length === 0 && segTours.length === 0 && (
                        <p className="text-xs text-muted-foreground">No attractions or tours selected</p>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {/* Step 3: Base Services */}
          {currentStep === 2 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wrench className="h-5 w-5 text-primary" />
                  {t('selectServices')}
                </CardTitle>
                <CardDescription>{t('selectServicesDesc')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {baseServices.length === 0 && (
                  <p className="text-sm text-muted-foreground py-4 text-center">No base services available yet</p>
                )}
                {baseServices.map(svc => {
                  const qty = getServiceQty(svc.id);
                  const unitLabel = svc.unit_type === 'per_day' ? `/${t('days')}`
                    : svc.unit_type === 'per_pax' ? `/${t('people')}`
                    : `/${t('perTrip')}`;
                  const displayName = locale === 'zh' && svc.name_zh ? svc.name_zh
                    : locale === 'es' && svc.name_es ? svc.name_es
                    : locale === 'fr' && svc.name_fr ? svc.name_fr
                    : svc.name;
                  const displayDesc = locale === 'zh' && svc.description_zh ? svc.description_zh
                    : locale === 'es' && svc.description_es ? svc.description_es
                    : locale === 'fr' && svc.description_fr ? svc.description_fr
                    : svc.description;

                  return (
                    <div key={svc.id} className="flex items-center justify-between p-3 rounded-lg border">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm">{displayName}</p>
                        <p className="text-xs text-muted-foreground">
                          ${svc.unit_price} {unitLabel}
                          {displayDesc && <span className="ml-1 text-muted-foreground/60">— {displayDesc}</span>}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 ml-3 shrink-0">
                        <Button variant="outline" size="sm" onClick={() => updateService(svc.id, -1)} disabled={qty === 0}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-6 text-center text-sm font-medium">{qty}</span>
                        <Button variant="outline" size="sm" onClick={() => updateService(svc.id, 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {/* Step 4: Confirm & Contact */}
          {currentStep === 3 && (
            <>
              {/* Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>{t('subtotal')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Guide Language */}
                  <div className="flex justify-between text-sm">
                    <span>{t('guideLanguage')}</span>
                    <span className="font-medium">{guideLanguage || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>{t('paxCount')}</span>
                    <span className="font-medium">{paxCount} {t('people')}</span>
                  </div>

                  {/* Segments */}
                  <div className="border-t pt-2">
                    <p className="text-sm font-medium mb-2">{t('itinerarySegments') || 'Itinerary'}: {segments.length} segments</p>
                    {segments.map((seg, idx) => {
                      const dest = destinations.find(d => d.id === seg.destination_id);
                      const destDisplay2 = seg.isCustomDest ? seg.custom_destination : (dest?.name || '-');
                      const segTours = tours.filter(t => seg.tour_ids.includes(t.id));
                      return (
                        <div key={idx} className="text-xs text-muted-foreground mb-2 pl-2 border-l-2 border-primary/30">
                          <p className="font-medium text-primary">{t('segmentLabel') || 'Seg'} {idx + 1}: {destDisplay2}</p>
                          <p>{seg.start_date} → {seg.end_date}</p>
                          {segTours.length > 0 && <p>{t('baseTour')}: {segTours.map(t => t.name).join(', ')}</p>}
                        </div>
                      );
                    })}
                  </div>

                  {selectedServices.length > 0 && (
                    <div className="border-t pt-2 text-sm">
                      <p className="text-muted-foreground mb-1">{t('selectServices')}:</p>
                      {selectedServices.map(s => {
                        const svc = baseServices.find(b => b.id === s.service_id);
                        if (!svc) return null;
                        return (
                          <div key={s.service_id} className="flex justify-between text-xs text-muted-foreground pl-2">
                            <span>{svc.name} × {s.quantity}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div className="border-t pt-3 flex justify-between text-lg font-bold">
                    <span>{t('subtotal')}</span>
                    <span>${estimatedPrice?.toFixed(2) || '0.00'}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{t('priceNote')}</p>
                </CardContent>
              </Card>

              {/* Contact Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Phone className="h-5 w-5 text-primary" />
                    {t('contactInfo')}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>{t('contactName')} *</Label>
                    <Input placeholder={t('contactName')} value={contactName} onChange={e => setContactName(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>{t('contactEmail')} *</Label>
                    <Input type="email" placeholder={t('contactEmail')} value={contactEmail} onChange={e => setContactEmail(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>{t('contactPhone')}</Label>
                    <Input placeholder={t('contactPhone')} value={contactPhone} onChange={e => setContactPhone(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>{t('specialRequests')}</Label>
                    <textarea
                      rows={4}
                      className="w-full rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder={t('specialRequestsPlaceholder')}
                      value={specialRequests}
                      onChange={e => setSpecialRequests(e.target.value)}
                    />
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* ── Sidebar ─────────────────────────────────────── */}
        <div className="lg:col-span-1">
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle className="text-base">{t('subtotal')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-3xl font-bold text-primary">
                ${estimatedPrice?.toFixed(2) || '0.00'}
              </div>
              <p className="text-xs text-muted-foreground">{t('priceNote')}</p>
              <div className="text-xs text-muted-foreground space-y-1">
                {guideLanguage && <p>🗣 {guideLanguage}</p>}
                <p>👥 {paxCount} {t('people')}</p>
                <p>📍 {segments.length} segment(s), {totalDays} {t('days')}</p>
                {selectedServices.length > 0 && <p>🔧 {selectedServices.length} {t('selectServices').toLowerCase()}</p>}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Attraction Info Modal — 仅在 infoAttraction 非 null 时渲染 */}
      {infoAttraction && (
        <AttractionInfoModal
          attraction={{
            id: infoAttraction.id,
            slug: infoAttraction.slug,
            name: infoAttraction.name,
            description: infoAttraction.description,
            image_url: infoAttraction.image_url,
            rating: infoAttraction.rating || 0,
            media: (infoAttraction.media || []).map(m => ({
              id: m.id,
              url: m.url,
              media_type: m.media_type,
              alt_text: m.alt_text,
              sort_order: m.sort_order,
            })),
          }}
          locale={locale}
          open={true}
          onOpenChange={(open) => { if (!open) setInfoAttraction(null); }}
        />
      )}

      {/* ── Navigation Buttons ────────────────────────────── */}
      <div className="flex justify-between mt-8 max-w-4xl mx-auto">
        <div>
          {currentStep > 0 ? (
            <Button variant="outline" onClick={handlePrev}>
              <ChevronLeft className="h-4 w-4 mr-2" /> Back
            </Button>
          ) : (
            <Link href={`/${locale}`}><Button variant="ghost"><ArrowLeft className="h-4 w-4 mr-2" /> Back</Button></Link>
          )}
        </div>
        <div>
          {currentStep < STEPS.length - 1 ? (
            <Button onClick={handleNext} disabled={!canProceedStep(currentStep)}>
              Next <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={!canProceedStep(3) || submitting}>
              {submitting ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> {t('submitting')}</>
              ) : (
                <><Send className="h-4 w-4 mr-2" /> {t('submitRequest')}</>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
