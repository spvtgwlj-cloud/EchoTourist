'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { useAuthStore } from '@/lib/stores/auth-store';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Loader2, Plus, Trash2, Save, ArrowLeft, Check, X } from 'lucide-react';
import Link from 'next/link';

interface TourDateItem {
  id: string; tour_id: string;
  start_date: string; end_date: string;
  price_per_pax: number; currency: string;
  availability: number; status: string;
}

interface EditableDate extends TourDateItem {
  editing: boolean;
  editPrice: number;
  editAvailability: number;
  editStatus: string;
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function AddDateForm({ onAdd }: { onAdd: (d: { start_date: string; end_date: string; price_per_pax: number; availability: number }) => Promise<void> }) {
  const [startDate, setStartDate] = useState('');
  const [price, setPrice] = useState(0);
  const [avail, setAvail] = useState(10);
  const [adding, setAdding] = useState(false);

  const handleSubmit = async () => {
    if (!startDate) return;
    setAdding(true);
    try {
      await onAdd({
        start_date: startDate,
        end_date: startDate,
        price_per_pax: price,
        availability: avail,
      });
      setStartDate('');
      setPrice(0);
      setAvail(10);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="flex items-end gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
      <div>
        <label className="block text-xs font-medium mb-1 text-blue-700">Date</label>
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
          className="border rounded-md px-3 py-1.5 text-sm w-40" />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1 text-blue-700">Price ($)</label>
        <input type="number" min={0} step="0.01" value={price}
          onChange={(e) => setPrice(Number(e.target.value))}
          className="border rounded-md px-3 py-1.5 text-sm w-24" />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1 text-blue-700">Spots</label>
        <input type="number" min={0} value={avail}
          onChange={(e) => setAvail(Number(e.target.value))}
          className="border rounded-md px-3 py-1.5 text-sm w-20" />
      </div>
      <Button size="sm" onClick={handleSubmit} disabled={adding || !startDate}>
        {adding ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3 mr-1" />}
        Add
      </Button>
    </div>
  );
}

export default function TourDatesPage() {
  const { id } = useParams<{ id: string }>();
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  const [tourName, setTourName] = useState('');
  const [dates, setDates] = useState<EditableDate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadDates = useCallback(async () => {
    try {
      const [tourData, datesData] = await Promise.all([
        api.get<any>(`/admin/tours/${id}?locale=${locale}`, { cache: 'no-store' }),
        api.get<{ dates: TourDateItem[] }>(`/admin/tours/${id}/dates`, { cache: 'no-store' }),
      ]);
      setTourName(tourData.name || tourData.slug);
      setDates(datesData.dates.map((d) => ({
        ...d,
        editing: false,
        editPrice: d.price_per_pax,
        editAvailability: d.availability,
        editStatus: d.status,
      })));
    } catch {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [id, locale]);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) {
      router.push(`/${locale}/auth`);
      return;
    }
    loadDates();
  }, [isAuthenticated, user, locale, router, loadDates]);

  const showSuccess = (msg: string) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleAdd = async (data: { start_date: string; end_date: string; price_per_pax: number; availability: number }) => {
    await api.post(`/admin/tours/${id}/dates`, data);
    showSuccess('Date added!');
    await loadDates();
  };

  const toggleEdit = (dateId: string) => {
    setDates(dates.map((d) =>
      d.id === dateId
        ? { ...d, editing: !d.editing, editPrice: d.price_per_pax, editAvailability: d.availability, editStatus: d.status }
        : { ...d, editing: false }
    ));
  };

  const handleSave = async (date: EditableDate) => {
    try {
      await api.patch(`/admin/tours/${id}/dates/${date.id}`, {
        price_per_pax: date.editPrice,
        availability: date.editAvailability,
      });
      showSuccess('Date updated!');
      await loadDates();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Update failed');
    }
  };

  const handleDelete = async (dateId: string) => {
    if (!confirm('Delete this date? This cannot be undone.')) return;
    try {
      await api.delete(`/admin/tours/${id}/dates/${dateId}`);
      showSuccess('Date deleted!');
      await loadDates();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  if (loading) return <AdminLayout>
    <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div>
  </AdminLayout>;

  return (
    <AdminLayout>
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-1">
          <Link href={`/${locale}/admin/tours/${id}/edit`} className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Tour Dates</h1>
            <p className="text-sm text-muted-foreground">{tourName}</p>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-1 ml-9">
          Changes take effect immediately. Cache refreshes within 60 seconds.
        </p>
      </div>

      {error && <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>}
      {success && <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">{success}</div>}

      {/* Add new date */}
      <div className="mb-6">
        <h2 className="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide">Add New Date</h2>
        <AddDateForm onAdd={handleAdd} />
      </div>

      {/* Dates table */}
      <div className="bg-white rounded-lg border">
        {dates.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No dates yet. Add one above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-3 font-medium">Date</th>
                  <th className="text-left p-3 font-medium">Price</th>
                  <th className="text-left p-3 font-medium">Available</th>
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-right p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {dates.map((d) => (
                  <tr key={d.id} className="border-b hover:bg-gray-50/50">
                    <td className="p-3 font-medium whitespace-nowrap">
                      {formatDate(d.start_date)}
                      {d.start_date !== d.end_date && <span className="text-muted-foreground"> — {formatDate(d.end_date)}</span>}
                    </td>
                    <td className="p-3">
                      {d.editing ? (
                        <input type="number" min={0} step="0.01" value={d.editPrice}
                          onChange={(e) => setDates(dates.map((x) => x.id === d.id ? { ...x, editPrice: Number(e.target.value) } : x))}
                          className="w-24 border rounded px-2 py-1 text-sm" />
                      ) : (
                        <span className="font-medium">${d.price_per_pax}</span>
                      )}
                    </td>
                    <td className="p-3">
                      {d.editing ? (
                        <input type="number" min={0} value={d.editAvailability}
                          onChange={(e) => setDates(dates.map((x) => x.id === d.id ? { ...x, editAvailability: Number(e.target.value) } : x))}
                          className="w-20 border rounded px-2 py-1 text-sm" />
                      ) : (
                        <span className={`${d.availability <= 3 ? 'text-amber-600 font-medium' : ''}`}>
                          {d.availability} spots
                        </span>
                      )}
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        d.status === 'available' ? 'bg-green-100 text-green-700' :
                        d.status === 'sold_out' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>{d.status}</span>
                    </td>
                    <td className="p-3 text-right whitespace-nowrap">
                      {d.editing ? (
                        <span className="flex items-center justify-end gap-1">
                          <button onClick={() => handleSave(d)} className="p-1 text-green-600 hover:text-green-800">
                            <Check className="h-4 w-4" />
                          </button>
                          <button onClick={() => toggleEdit(d.id)} className="p-1 text-gray-400 hover:text-gray-600">
                            <X className="h-4 w-4" />
                          </button>
                        </span>
                      ) : (
                        <span className="flex items-center justify-end gap-1">
                          <button onClick={() => toggleEdit(d.id)} className="p-1 text-blue-600 hover:text-blue-800 text-xs font-medium">
                            Edit
                          </button>
                          <button onClick={() => handleDelete(d.id)} className="p-1 text-red-400 hover:text-red-600">
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="mt-4 flex gap-4 text-sm text-muted-foreground">
        <span>Total: <strong>{dates.length}</strong> dates</span>
        <span>Available: <strong className="text-green-600">{dates.filter(d => d.status === 'available').length}</strong></span>
        <span>Sold out: <strong className="text-red-600">{dates.filter(d => d.status === 'sold_out').length}</strong></span>
      </div>
    </AdminLayout>
  );
}
