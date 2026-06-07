'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { useAuthStore } from '@/lib/stores/auth-store';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Loader2, Save, ArrowLeft, CalendarRange, Plus, Trash2, Upload, X, Film, Image as ImageIcon } from 'lucide-react';
import Link from 'next/link';
import type { TourImage } from '@/lib/types';

// ── Types ─────────────────────────────────────────────────────────

interface TranslationData {
  locale: string;
  name: string;
  subtitle?: string;
  description?: string;
  highlights: string[];
  includes: string[];
  excludes: string[];
}

interface TourDetail {
  id: string; slug: string; name: string; subtitle?: string;
  description?: string; status: string; type: string;
  duration_days: number; duration_nights: number;
  max_pax?: number; min_pax: number;
  start_price: number; currency: string; difficulty: string;
  sort_order?: number;
  highlights: string[]; includes: string[]; excludes: string[];
  images: TourImage[];
  translations: TranslationData[];
}

const LOCALES = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
];

// ── Helpers ───────────────────────────────────────────────────────

/** 从 translations 数组中构建 locale → TranslationData 映射。 */
function buildTranslationsMap(translations: TranslationData[]): Record<string, TranslationData> {
  const map: Record<string, TranslationData> = {};
  for (const t of translations) {
    map[t.locale] = { ...t };
  }
  return map;
}

/** 根据可用 locale 补齐缺失的翻译条目（用空值填充）。 */
function ensureAllLocales(map: Record<string, TranslationData>): Record<string, TranslationData> {
  const result = { ...map };
  for (const { code } of LOCALES) {
    if (!result[code]) {
      result[code] = { locale: code, name: '', subtitle: '', description: '', highlights: [''], includes: [''], excludes: [''] };
    }
  }
  return result;
}

// ── Component ─────────────────────────────────────────────────────

export default function EditTourPage() {
  const { id } = useParams<{ id: string }>();
  const pageLocale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  const [tour, setTour] = useState<TourDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // ── 产品基础字段 ──────────────────────────────
  const [status, setStatus] = useState('draft');
  const [type, setType] = useState('group_tour');
  const [sortOrder, setSortOrder] = useState(0);
  const [durationDays, setDurationDays] = useState(1);
  const [durationNights, setDurationNights] = useState(0);
  const [maxPax, setMaxPax] = useState(20);
  const [minPax, setMinPax] = useState(1);
  const [startPrice, setStartPrice] = useState(0);
  const [currency, setCurrency] = useState('USD');
  const [difficulty, setDifficulty] = useState('easy');
  const [theme, setTheme] = useState('citywalk');
  const [images, setImages] = useState<TourImage[]>([]);

  // ── 多语言翻译数据 ────────────────────────────
  const [activeLocale, setActiveLocale] = useState(pageLocale);
  const [translationsMap, setTranslationsMap] = useState<Record<string, TranslationData>>({});

  // 当前 activeLocale 对应表单字段（方便直接绑定）
  const current = translationsMap[activeLocale] || { locale: activeLocale, name: '', subtitle: '', description: '', highlights: [''], includes: [''], excludes: [''] };

  /** 更新当前 locale 的某个字段值。 */
  const updateCurrent = useCallback((field: string, value: string | string[]) => {
    setTranslationsMap(prev => ({
      ...prev,
      [activeLocale]: { ...(prev[activeLocale] || { locale: activeLocale, name: '', highlights: [''], includes: [''], excludes: [''] }), [field]: value },
    }));
  }, [activeLocale]);

  const handleListChange = (list: string[], setter: (v: string[]) => void, index: number, value: string) => {
    const next = [...list]; next[index] = value; setter(next);
    updateCurrent(list === current.highlights ? 'highlights' : list === current.includes ? 'includes' : 'excludes', next);
  };

  const addListItem = (listKey: 'highlights' | 'includes' | 'excludes') => {
    const list = current[listKey] || [];
    const next = [...list, ''];
    updateCurrent(listKey, next);
  };

  const removeListItem = (listKey: 'highlights' | 'includes' | 'excludes', index: number) => {
    const list = current[listKey] || [];
    if (list.length <= 1) return;
    const next = list.filter((_, i) => i !== index);
    updateCurrent(listKey, next);
  };

  // ── 初始加载 ──────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${pageLocale}/auth`); return; }
    api.get<TourDetail>(`/admin/tours/${id}?locale=${pageLocale}`)
      .then((data) => {
        setTour(data);
        setStatus(data.status); setType(data.type);
        setSortOrder(data.sort_order ?? 0);
        setDurationDays(data.duration_days); setDurationNights(data.duration_nights);
        setMaxPax(data.max_pax || 20); setMinPax(data.min_pax || 1);
        setStartPrice(data.start_price); setCurrency(data.currency); setDifficulty(data.difficulty);
        setTheme((data as any).theme || 'citywalk');
        setImages(data.images || []);

        // 构建多语言翻译映射
        const map = ensureAllLocales(buildTranslationsMap(data.translations || []));
        // 确保当前页面 locale 有数据
        if (map[pageLocale] && !map[pageLocale].name && data.name) {
          map[pageLocale].name = data.name;
          map[pageLocale].subtitle = data.subtitle || '';
          map[pageLocale].description = data.description || '';
          map[pageLocale].highlights = data.highlights?.length ? [...data.highlights] : [''];
          map[pageLocale].includes = data.includes?.length ? [...data.includes] : [''];
          map[pageLocale].excludes = data.excludes?.length ? [...data.excludes] : [''];
        }
        setTranslationsMap(map);
      })
      .catch(() => setError('Failed to load tour'))
      .finally(() => setLoading(false));
  }, [id, pageLocale, isAuthenticated, user, router]);

  // ── 保存 ──────────────────────────────────────
  const handleSave = async () => {
    setError(''); setSuccess(''); setSaving(true);
    try {
      // 收集所有翻译数据为数组（跳过完全空的条目）
      const allTranslations = Object.values(translationsMap)
        .filter(t => t.name || t.subtitle || t.description ||
          (t.highlights && t.highlights.some(Boolean)) ||
          (t.includes && t.includes.some(Boolean)) ||
          (t.excludes && t.excludes.some(Boolean)))
        .map(t => ({
        locale: t.locale,
        name: t.name || '',
        subtitle: t.subtitle || undefined,
        description: t.description || undefined,
        highlights: (t.highlights || []).filter(Boolean),
        includes: (t.includes || []).filter(Boolean),
        excludes: (t.excludes || []).filter(Boolean),
      }));

      await api.patch(`/admin/tours/${id}`, {
        status, type,
        sort_order: sortOrder,
        duration_days: durationDays, duration_nights: durationNights,
        max_pax: maxPax, min_pax: minPax,
        start_price: startPrice, currency, difficulty, theme,
        translations: allTranslations,
      });
      const fresh = await api.get<TourDetail>(`/admin/tours/${id}?locale=${pageLocale}`);
      setTour(fresh); setImages(fresh.images || []);
      const map = ensureAllLocales(buildTranslationsMap(fresh.translations || []));
      setTranslationsMap(map);
      setSuccess('Tour updated successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally { setSaving(false); }
  };

  // ── 图片/视频上传 ─────────────────────────────
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true); setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/v1/admin/upload', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Upload failed'); }
      const data = await res.json();
      setImages([...images, {
        id: `temp_${Date.now()}`,
        url: data.url,
        alt_text: file.name.split('.')[0],
        sort_order: images.length + 1,
        type: data.type === 'video' ? 'video' : 'image',
      }]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally { setUploading(false); e.target.value = ''; }
  };

  const handleDeleteImage = async (img: TourImage) => {
    if (!window.confirm(`Delete this ${img.type}? This action cannot be undone.`)) return;
    try {
      if (!img.id.startsWith('temp_')) {
        await api.delete(`/admin/tours/${id}/images/${img.id}`);
      }
      setImages(images.filter((i) => i.id !== img.id));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  const isVideo = (url: string) => {
    const ext = url.split('?')[0].toLowerCase();
    return ext.endsWith('.mp4') || ext.endsWith('.webm') || ext.endsWith('.mov');
  };

  // ── 多语言切换栏 ──────────────────────────────
  const LocaleTabs = () => (
    <div className="flex gap-1 border-b pb-2 mb-4">
      {LOCALES.map(({ code, label }) => {
        const hasData = translationsMap[code] && !!(translationsMap[code].name);
        return (
          <button
            key={code}
            type="button"
            onClick={() => {
              // 切换时，当前表单数据已通过 updateCurrent 同步到 translationsMap
              setActiveLocale(code);
            }}
            className={`px-4 py-1.5 text-sm rounded-t-md border-b-2 transition-colors ${
              activeLocale === code
                ? 'border-blue-500 text-blue-600 font-medium bg-blue-50'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-gray-50'
            }`}
          >
            {label}
            {hasData && activeLocale !== code && (
              <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-green-400 align-middle" />
            )}
          </button>
        );
      })}
    </div>
  );

  // ── Loading / Empty ────────────────────────────
  if (loading) return <AdminLayout><div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div></AdminLayout>;
  if (!tour) return <AdminLayout><div className="text-center py-20 text-muted-foreground">Tour not found</div></AdminLayout>;

  return (
    <AdminLayout>
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/${pageLocale}/admin/tours`} className="text-muted-foreground hover:text-foreground"><ArrowLeft className="h-5 w-5" /></Link>
          <div><h1 className="text-2xl font-bold">Edit Tour</h1><p className="text-sm text-muted-foreground">{tour.slug}</p></div>
        </div>
        <div className="flex items-center gap-3">
          <Link href={`/${pageLocale}/admin/tours/${id}/dates`}><Button variant="outline"><CalendarRange className="h-4 w-4 mr-2" />Manage Dates</Button></Link>
          <Button onClick={handleSave} disabled={saving}>
            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            <Save className="h-4 w-4 mr-2" />Save Changes
          </Button>
        </div>
      </div>

      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>}
      {success && <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">{success}</div>}

      <div className="space-y-6">

        {/* ── 基本信息 ─────────────────────────────── */}
        <section className="bg-white rounded-lg border p-6 space-y-4">
          <h2 className="text-lg font-semibold">Basic Information</h2>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <div><label className="block text-sm font-medium mb-1">Slug</label><input readOnly value={tour.slug} className="w-full border rounded-md px-3 py-2 text-sm bg-gray-50 text-gray-500" /></div>
            <div><label className="block text-sm font-medium mb-1">Status</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full border rounded-md px-3 py-2 text-sm">
                <option value="draft">Draft</option><option value="published">Published</option>
              </select>
            </div>
            <div><label className="block text-sm font-medium mb-1">Sort Order</label>
              <input type="number" min={0} step={1} value={sortOrder}
                onChange={(e) => setSortOrder(Number(e.target.value))}
                className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
            <div><label className="block text-sm font-medium mb-1">Type</label>
              <select value={type} onChange={(e) => setType(e.target.value)} className="w-full border rounded-md px-3 py-2 text-sm">
                <option value="group_tour">Group Tour</option><option value="private_tour">Private Tour</option>
              </select>
            </div>
            <div><label className="block text-sm font-medium mb-1">Difficulty</label>
              <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="w-full border rounded-md px-3 py-2 text-sm">
                <option value="easy">Easy</option><option value="moderate">Moderate</option><option value="challenging">Challenging</option>
              </select>
            </div>
            <div><label className="block text-sm font-medium mb-1">Theme</label>
              <select value={theme} onChange={(e) => setTheme(e.target.value)} className="w-full border rounded-md px-3 py-2 text-sm">
                <option value="citywalk">City Walk</option>
                <option value="culture_history">Culture & History</option>
                <option value="nature">Nature & Scenery</option>
                <option value="food">Food & Culinary</option>
                <option value="honeymoon">Honeymoon & Romance</option>
                <option value="family">Family</option>
                <option value="luxury">Luxury</option>
                <option value="adventure">Adventure</option>
                <option value="photography">Photography</option>
                <option value="wellness">Wellness & Spa</option>
                <option value="hidden_gems">Hidden Gems</option>
                <option value="festival">Festival & Events</option>
              </select>
            </div>
            <div><label className="block text-sm font-medium mb-1">Duration (Days)</label>
              <input type="number" min={0.5} step={0.5} value={durationDays} onChange={(e) => setDurationDays(Number(e.target.value))} className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
            <div><label className="block text-sm font-medium mb-1">Duration (Nights)</label>
              <input type="number" min={0} value={durationNights} onChange={(e) => setDurationNights(Number(e.target.value))} className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
            <div><label className="block text-sm font-medium mb-1">Start Price ($)</label>
              <input type="number" min={0} step="0.01" value={startPrice} onChange={(e) => setStartPrice(Number(e.target.value))} className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
            <div><label className="block text-sm font-medium mb-1">Currency</label>
              <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="w-full border rounded-md px-3 py-2 text-sm">
                <option value="USD">USD</option><option value="CNY">CNY</option><option value="EUR">EUR</option>
              </select>
            </div>
            <div><label className="block text-sm font-medium mb-1">Max Pax</label>
              <input type="number" min={1} value={maxPax} onChange={(e) => setMaxPax(Number(e.target.value))} className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
            <div><label className="block text-sm font-medium mb-1">Min Pax</label>
              <input type="number" min={1} value={minPax} onChange={(e) => setMinPax(Number(e.target.value))} className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
          </div>
        </section>

        {/* ── 名称与描述（多语言）──────────────────── */}
        <section className="bg-white rounded-lg border p-6 space-y-4">
          <h2 className="text-lg font-semibold">Name & Description</h2>
          <LocaleTabs />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name ({activeLocale.toUpperCase()}) *</label>
              <input value={current.name} onChange={(e) => updateCurrent('name', e.target.value)}
                className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Subtitle ({activeLocale.toUpperCase()})</label>
              <input value={current.subtitle || ''} onChange={(e) => updateCurrent('subtitle', e.target.value)}
                className="w-full border rounded-md px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description ({activeLocale.toUpperCase()})</label>
            <textarea value={current.description || ''} onChange={(e) => updateCurrent('description', e.target.value)}
              rows={5} className="w-full border rounded-md px-3 py-2 text-sm" />
          </div>
        </section>

        {/* ── 亮点 / 包含 / 不包含（多语言）───────── */}
        <section className="bg-white rounded-lg border p-6 space-y-6">
          <h2 className="text-lg font-semibold">Features</h2>
          <LocaleTabs />
          {(['highlights', 'includes', 'excludes'] as const).map((listKey) => {
            const labels = { highlights: 'Highlights', includes: 'Includes', excludes: 'Excludes' };
            const list = current[listKey] || [''];
            return (
              <div key={listKey}>
                <label className="block text-sm font-medium mb-2">{labels[listKey]} ({activeLocale.toUpperCase()})</label>
                {list.map((item: string, i: number) => (
                  <div key={i} className="flex items-center gap-2 mb-2">
                    <input value={item} onChange={(e) => {
                      const next = [...list]; next[i] = e.target.value;
                      updateCurrent(listKey, next);
                    }} className="flex-1 border rounded-md px-3 py-1.5 text-sm" placeholder={`${labels[listKey]} item...`} />
                    <button type="button" onClick={() => removeListItem(listKey, i)} className="text-red-400 hover:text-red-600"><Trash2 className="h-4 w-4" /></button>
                  </div>
                ))}
                <Button type="button" variant="ghost" size="sm" onClick={() => addListItem(listKey)}>
                  <Plus className="h-3 w-3 mr-1" /> Add
                </Button>
              </div>
            );
          })}
        </section>

        {/* ── 图片和视频管理 ───────────────────────── */}
        <section className="bg-white rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Photos & Videos</h2>
            <div className="flex items-center gap-2">
              <label className="cursor-pointer">
                <input type="file" accept="image/*,video/mp4,video/webm,video/quicktime" className="hidden"
                  onChange={handleUpload} disabled={uploading} />
                <span className="inline-flex items-center px-3 py-2 border rounded-md text-sm font-medium hover:bg-gray-50 cursor-pointer">
                  {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
                  {uploading ? 'Uploading...' : 'Upload Media'}
                </span>
              </label>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Supported formats: JPG, PNG, WebP, GIF, SVG, MP4, WebM, MOV (max 60MB per file)
          </p>

          {images.length === 0 ? (
            <div className="border-2 border-dashed rounded-lg p-10 text-center text-muted-foreground">
              <ImageIcon className="h-10 w-10 mx-auto mb-2 opacity-40" />
              <p>No media uploaded yet. Click "Upload Media" to add images or videos.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {images.map((img) => (
                <div key={img.id} className="relative group rounded-lg border overflow-hidden bg-gray-50">
                  {img.type === 'video' || isVideo(img.url) ? (
                    <div className="relative aspect-[4/3] flex items-center justify-center bg-gray-100">
                      <video src={img.url} className="w-full h-full object-cover" preload="metadata" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="bg-black/50 rounded-full p-2"><Film className="h-6 w-6 text-white" /></div>
                      </div>
                    </div>
                  ) : (
                    <div className="aspect-[4/3] overflow-hidden">
                      <img src={img.url} alt={img.alt_text || ''} className="w-full h-full object-cover"
                        onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder.svg'; }} />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <button onClick={() => handleDeleteImage(img)}
                      className="bg-red-500 text-white rounded-full p-1.5 hover:bg-red-600 transition-colors">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="px-2 py-1 text-xs text-muted-foreground truncate bg-white border-t">
                    {img.type === 'video' ? '🎬 ' : '🖼️ '}{img.alt_text || img.url.split('/').pop()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </AdminLayout>
  );
}
