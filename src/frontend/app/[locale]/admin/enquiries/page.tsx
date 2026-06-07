'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { MessageCircle, Mail, Phone, Users, MapPin, ChevronDown, ChevronUp, Check, X } from 'lucide-react';
import { TableSkeleton } from '@/components/ui/skeletons';

interface EnquiryItem {
  id: string; name: string; email: string; phone?: string;
  destination?: string; pax_count?: number; message: string;
  status: string; admin_notes?: string; created_at: string;
}

const STATUS_OPTIONS = ['new', 'read', 'contacted', 'closed'];

export default function AdminEnquiries() {
  const locale = useLocale();
  const router = useRouter();
  const t = useTranslations('admin');
  const { isAuthenticated, user } = useAuthStore();
  const [enquiries, setEnquiries] = useState<EnquiryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchEnquiries = (status: string) => {
    setLoading(true);
    const params = status ? `?status=${status}` : '';
    api.get<{ enquiries: EnquiryItem[]; total: number }>(`/admin/enquiries${params}`)
      .then((res) => { setEnquiries(res.enquiries || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    fetchEnquiries(filter);
  }, [isAuthenticated, user, locale, router, filter]);

  const updateStatus = async (id: string, status: string) => {
    await api.patch(`/admin/enquiries/${id}`, { status });
    fetchEnquiries(filter);
  };

  const deleteEnquiry = async (id: string) => {
    if (!confirm('Delete this enquiry?')) return;
    await api.delete(`/admin/enquiries/${id}`);
    fetchEnquiries(filter);
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-blue-100 text-blue-700',
      read: 'bg-yellow-100 text-yellow-700',
      contacted: 'bg-green-100 text-green-700',
      closed: 'bg-gray-100 text-gray-500',
    };
    return (
      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[status] || 'bg-gray-100'}`}>
        {status}
      </span>
    );
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString(locale === 'zh' ? 'zh-CN' : locale === 'es' ? 'es-ES' : 'en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  if (loading) return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div><div className="h-7 w-48 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-32 bg-gray-200 animate-pulse rounded mt-2" /></div>
      </div>
      <TableSkeleton rows={4} cols={6} />
    </AdminLayout>
  );

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{t('enquiries')} ({total})</h1>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setFilter('')} className={`rounded-md px-3 py-1.5 text-sm border ${!filter ? 'border-primary bg-primary/10 text-primary' : 'border-input text-muted-foreground'}`}>All</button>
          {STATUS_OPTIONS.map((s) => (
            <button key={s} onClick={() => setFilter(s)} className={`rounded-md px-3 py-1.5 text-sm border ${filter === s ? 'border-primary bg-primary/10 text-primary' : 'border-input text-muted-foreground'}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {enquiries.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <MessageCircle className="mx-auto h-12 w-12 text-muted-foreground/50 mb-3" />
          <p>No enquiries found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {enquiries.map((enq) => (
            <div key={enq.id} className="rounded-lg border bg-white overflow-hidden">
              {/* Row header */}
              <div className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50" onClick={() => setExpanded(expanded === enq.id ? null : enq.id)}>
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  {statusBadge(enq.status)}
                  <span className="font-medium truncate">{enq.name}</span>
                  <span className="text-sm text-muted-foreground truncate hidden sm:inline">{enq.email}</span>
                  <span className="text-xs text-muted-foreground hidden md:inline">{formatDate(enq.created_at)}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {expanded === enq.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </div>
              </div>

              {/* Expanded detail */}
              {expanded === enq.id && (
                <div className="border-t px-4 py-3 space-y-3 bg-gray-50/50">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <Mail className="h-3.5 w-3.5" />
                      <a href={`mailto:${enq.email}`} className="text-primary hover:underline">{enq.email}</a>
                    </div>
                    {enq.phone && (
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Phone className="h-3.5 w-3.5" />
                        <a href={`tel:${enq.phone}`} className="text-primary hover:underline">{enq.phone}</a>
                      </div>
                    )}
                    {enq.destination && (
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <MapPin className="h-3.5 w-3.5" />
                        {enq.destination}
                      </div>
                    )}
                    {enq.pax_count && (
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Users className="h-3.5 w-3.5" />
                        {enq.pax_count} travelers
                      </div>
                    )}
                  </div>
                  <div className="rounded-md bg-white border p-3 text-sm">
                    <p className="text-gray-700 whitespace-pre-wrap">{enq.message}</p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="flex gap-2">
                      {STATUS_OPTIONS.map((s) => (
                        <button
                          key={s}
                          onClick={() => updateStatus(enq.id, s)}
                          className={`rounded px-2.5 py-1 text-xs border font-medium transition-colors ${
                            enq.status === s
                              ? 'bg-primary text-white border-primary'
                              : 'bg-white text-muted-foreground border-input hover:border-primary/50'
                          }`}
                        >
                          {s === 'new' ? '📩 New' : s === 'read' ? '👁 Read' : s === 'contacted' ? '📞 Contacted' : '✅ Closed'}
                        </button>
                      ))}
                    </div>
                    <button onClick={() => deleteEnquiry(enq.id)} className="text-xs text-red-500 hover:text-red-700 ml-2">
                      <X className="h-3.5 w-3.5 inline" /> Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </AdminLayout>
  );
}
