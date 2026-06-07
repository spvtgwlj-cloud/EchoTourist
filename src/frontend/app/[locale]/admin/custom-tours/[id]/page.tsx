'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter, useParams } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, ArrowLeft, Check, X, MapPin } from 'lucide-react';
import Link from 'next/link';

interface SegmentData {
  id: string;
  segment_order: number;
  destination_id: string;
  destination_name: string;
  start_date: string;
  end_date: string;
  attractions: { id: string; attraction_id: string; attraction_name: string; sort_order: number }[];
  selected_tours: { id: string; tour_id: string; tour_name: string }[];
}

interface ServiceData {
  id: string;
  service_id: string;
  service_name: string;
  unit_price_snapshot: number;
  quantity: number;
  subtotal: number;
}

interface DetailData {
  id: string;
  request_no: string;
  user_id: string | null;
  pax_count: number;
  guide_language: string | null;
  contact_name: string;
  contact_email: string;
  contact_phone: string | null;
  special_requests: string | null;
  subtotal: number;
  confirmed_price: number | null;
  currency: string;
  status: string;
  admin_notes: string | null;
  locale: string;
  segments: SegmentData[];
  services: ServiceData[];
  created_at: string;
  updated_at: string;
}

export default function AdminCustomTourDetail() {
  const locale = useLocale();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { isAuthenticated, user } = useAuthStore();
  const [data, setData] = useState<DetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [confirmedPrice, setConfirmedPrice] = useState<number | null>(null);
  const [adminNotes, setAdminNotes] = useState('');

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    if (!params.id) return;
    loadDetail();
  }, [isAuthenticated, user, locale, router, params.id]);

  const loadDetail = () => {
    setLoading(true);
    api.get<DetailData>(`/admin/custom-tours/${params.id}`)
      .then((res) => {
        setData(res);
        setConfirmedPrice(res.confirmed_price ?? null);
        setAdminNotes(res.admin_notes || '');
      })
      .catch(() => router.push(`/${locale}/admin/custom-tours`))
      .finally(() => setLoading(false));
  };

  const handleUpdate = async (updates: Record<string, any>) => {
    setSaving(true);
    try {
      await api.patch(`/admin/custom-tours/${params.id}`, updates);
      loadDetail();
    } catch (e: any) {
      alert(e?.message || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <AdminLayout>
    <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div>
  </AdminLayout>;

  if (!data) return <AdminLayout><div className="text-center py-20 text-muted-foreground">Request not found</div></AdminLayout>;

  const STATUS_COLORS: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    quoted: 'bg-blue-100 text-blue-700',
    confirmed: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
    paid: 'bg-purple-100 text-purple-700',
  };

  const totalDays = data.segments.reduce((sum, s) => {
    return sum + Math.max(1, (new Date(s.end_date).getTime() - new Date(s.start_date).getTime()) / (1000 * 60 * 60 * 24));
  }, 0);

  return (
    <AdminLayout>
      {/* Header */}
      <div className="mb-6">
        <Link href={`/${locale}/admin/custom-tours`} className="text-sm text-muted-foreground hover:text-primary inline-flex items-center gap-1 mb-2">
          <ArrowLeft className="h-3 w-3" /> Back to Custom Tours
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold font-mono">{data.request_no}</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[data.status] || 'bg-gray-100'}`}>
                {data.status}
              </span>
              <span className="text-sm text-muted-foreground">{data.segments.length} segment(s)</span>
            </div>
          </div>
          <div className="flex gap-2">
            {data.status === 'pending' && (
              <>
                <Button variant="default" onClick={() => handleUpdate({ status: 'quoted', confirmed_price: confirmedPrice, admin_notes: adminNotes })} disabled={saving || confirmedPrice == null}>
                  <Check className="h-4 w-4 mr-2" /> Quote Price
                </Button>
                <Button variant="destructive" onClick={() => handleUpdate({ status: 'rejected', admin_notes: adminNotes })} disabled={saving}>
                  <X className="h-4 w-4 mr-2" /> Reject
                </Button>
              </>
            )}
            {data.status === 'quoted' && (
              <>
                <Button variant="default" className="bg-green-600" onClick={() => handleUpdate({ status: 'confirmed', admin_notes: adminNotes })} disabled={saving}>
                  <Check className="h-4 w-4 mr-2" /> Confirm
                </Button>
                <Button variant="destructive" onClick={() => handleUpdate({ status: 'rejected', admin_notes: adminNotes })} disabled={saving}>
                  <X className="h-4 w-4 mr-2" /> Reject
                </Button>
              </>
            )}
            {saving && <Loader2 className="h-5 w-5 animate-spin my-auto" />}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contact Info */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-bold mb-4">Contact & Travel Info</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-muted-foreground">Contact Name</dt><dd className="font-medium">{data.contact_name}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Email</dt><dd>{data.contact_email}</dd></div>
            {data.contact_phone && <div className="flex justify-between"><dt className="text-muted-foreground">Phone</dt><dd>{data.contact_phone}</dd></div>}
            <div className="flex justify-between"><dt className="text-muted-foreground">Pax</dt><dd>{data.pax_count}</dd></div>
            {data.guide_language && <div className="flex justify-between"><dt className="text-muted-foreground">Guide Language</dt><dd className="font-medium">{data.guide_language}</dd></div>}
            <div className="flex justify-between"><dt className="text-muted-foreground">Total Days</dt><dd>{totalDays}</dd></div>
            {data.special_requests && (
              <div className="pt-2 border-t col-span-2">
                <dt className="text-muted-foreground mb-1">Special Requests</dt>
                <dd className="text-sm whitespace-pre-wrap bg-gray-50 p-3 rounded">{data.special_requests}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Metadata */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-bold mb-4">Metadata</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-muted-foreground">Created</dt><dd>{data.created_at}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Updated</dt><dd>{data.updated_at}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">User ID</dt><dd className="font-mono text-xs">{data.user_id || 'Anonymous'}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Locale</dt><dd>{data.locale}</dd></div>
          </dl>
        </div>

        {/* Segments — 多段行程展示 */}
        <div className="lg:col-span-2 bg-white rounded-lg border p-6">
          <h2 className="font-bold mb-4">Itinerary Segments ({data.segments.length})</h2>
          <div className="space-y-4">
            {data.segments.map((seg) => (
              <div key={seg.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {seg.segment_order}
                    </span>
                    <h3 className="font-semibold text-sm">{seg.destination_name}</h3>
                  </div>
                  <span className="text-xs text-muted-foreground">{seg.start_date} → {seg.end_date}</span>
                </div>

                {/* Attractions */}
                {seg.attractions.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs text-muted-foreground mb-1">Attractions:</p>
                    <div className="flex flex-wrap gap-1">
                      {seg.attractions.map(a => (
                        <span key={a.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
                          {a.attraction_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Selected Tours */}
                {seg.selected_tours.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Selected Tours:</p>
                    <div className="flex flex-wrap gap-1">
                      {seg.selected_tours.map(t => (
                        <span key={t.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-50 text-green-700">
                          {t.tour_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {seg.attractions.length === 0 && seg.selected_tours.length === 0 && (
                  <p className="text-xs text-muted-foreground italic">No attractions or tours selected</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Services */}
        <div className="lg:col-span-2 bg-white rounded-lg border p-6">
          <h2 className="font-bold mb-4">Selected Services ({data.services.length})</h2>
          {data.services.length === 0 ? (
            <p className="text-sm text-muted-foreground">None selected</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="pb-2 font-medium">Service</th>
                  <th className="pb-2 font-medium">Qty</th>
                  <th className="pb-2 font-medium">Unit Price</th>
                  <th className="pb-2 font-medium">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {data.services.map(s => (
                  <tr key={s.id} className="border-b last:border-0">
                    <td className="py-2">{s.service_name}</td>
                    <td className="py-2">{s.quantity}</td>
                    <td className="py-2">${s.unit_price_snapshot}</td>
                    <td className="py-2">${s.subtotal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pricing & Admin Actions */}
        <div className="lg:col-span-2 bg-white rounded-lg border p-6">
          <h2 className="font-bold mb-4">Pricing & Admin Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <Label>Auto-calculated Subtotal</Label>
              <p className="text-2xl font-bold mt-1">${data.subtotal.toFixed(2)}</p>
            </div>
            <div>
              <Label>Confirmed Price (set by admin)</Label>
              <Input type="number" min={0} step={0.01} value={confirmedPrice ?? ''}
                onChange={e => setConfirmedPrice(e.target.value ? Number(e.target.value) : null)}
                placeholder="Enter confirmed price" />
            </div>
            <div className="flex items-end">
              <div>
                <Label>Status</Label>
                <p className="text-sm mt-1">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[data.status]}`}>
                    {data.status}
                  </span>
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4">
            <Label>Admin Notes</Label>
            <textarea rows={3} className="w-full mt-1 rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={adminNotes} onChange={e => setAdminNotes(e.target.value)} placeholder="Internal notes..." />
          </div>

          <div className="mt-4">
            <Button onClick={() => handleUpdate({ confirmed_price: confirmedPrice, admin_notes: adminNotes })} disabled={saving}>
              {saving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</> : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
