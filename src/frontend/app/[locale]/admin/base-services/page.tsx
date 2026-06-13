'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Edit3, Trash2, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { TableSkeleton } from '@/components/ui/skeletons';

interface ServiceItem {
  id: string;
  name: string;
  name_zh: string | null;
  name_es: string | null;
  name_fr: string | null;
  description: string | null;
  description_zh: string | null;
  description_es: string | null;
  description_fr: string | null;
  unit_type: string;
  unit_price: number;
  currency: string;
  category: string | null;
  sort_order: number;
  status: string;
}

export default function AdminBaseServices() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [showLangFields, setShowLangFields] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [nameZh, setNameZh] = useState('');
  const [nameEs, setNameEs] = useState('');
  const [nameFr, setNameFr] = useState('');
  const [description, setDescription] = useState('');
  const [descriptionZh, setDescriptionZh] = useState('');
  const [descriptionEs, setDescriptionEs] = useState('');
  const [descriptionFr, setDescriptionFr] = useState('');
  const [unitType, setUnitType] = useState('per_day');
  const [unitPrice, setUnitPrice] = useState(0);
  const [category, setCategory] = useState('');
  const [sortOrder, setSortOrder] = useState(0);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    loadServices();
  }, [isAuthenticated, user, locale, router]);

  const loadServices = () => {
    setLoading(true);
    api.get<{ services: ServiceItem[]; total: number }>('/admin/base-services', { cache: 'no-store' })
      .then((res) => { setServices(res.services || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const resetForm = () => {
    setName(''); setNameZh(''); setNameEs(''); setNameFr('');
    setDescription(''); setDescriptionZh(''); setDescriptionEs(''); setDescriptionFr('');
    setUnitType('per_day'); setUnitPrice(0); setCategory(''); setSortOrder(0);
    setEditId(null); setShowLangFields(false);
  };

  const openEdit = (svc: ServiceItem) => {
    setEditId(svc.id);
    setName(svc.name);
    setNameZh(svc.name_zh || '');
    setNameEs(svc.name_es || '');
    setNameFr(svc.name_fr || '');
    setDescription(svc.description || '');
    setDescriptionZh(svc.description_zh || '');
    setDescriptionEs(svc.description_es || '');
    setDescriptionFr(svc.description_fr || '');
    setUnitType(svc.unit_type);
    setUnitPrice(svc.unit_price);
    setCategory(svc.category || '');
    setSortOrder(svc.sort_order);
    setShowLangFields(!!(svc.name_zh || svc.name_es || svc.name_fr));
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!name) return;
    setSaving(true);
    try {
      const payload: Record<string, any> = {
        name, unit_type: unitType, unit_price: unitPrice, sort_order: sortOrder,
        name_zh: nameZh || undefined, name_es: nameEs || undefined, name_fr: nameFr || undefined,
        description: description || undefined,
        description_zh: descriptionZh || undefined,
        description_es: descriptionEs || undefined,
        description_fr: descriptionFr || undefined,
        category: category || undefined,
      };
      if (editId) {
        await api.put(`/admin/base-services/${editId}`, payload);
      } else {
        await api.post('/admin/base-services', payload);
      }
      setShowForm(false);
      resetForm();
      loadServices();
    } catch (e: any) {
      alert(e?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this base service?')) return;
    try {
      await api.delete(`/admin/base-services/${id}`);
      loadServices();
    } catch (e: any) {
      alert(e?.message || 'Delete failed');
    }
  };

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-32 bg-gray-200 animate-pulse rounded" /></div>
      <div className="h-10 w-32 bg-gray-200 animate-pulse rounded" />
    </div>
    <TableSkeleton rows={5} cols={6} />
  </AdminLayout>;

  const displayName = (svc: ServiceItem) => {
    if (locale === 'zh' && svc.name_zh) return svc.name_zh;
    return svc.name;
  };

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Base Services</h1>
          <p className="text-sm text-muted-foreground">{total} services</p>
        </div>
        <Button onClick={() => { resetForm(); setShowForm(true); }}>
          <Plus className="h-4 w-4 mr-2" /> Add Service
        </Button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-lg p-6 w-full max-w-xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">{editId ? 'Edit' : 'Add'} Base Service</h2>
            <div className="space-y-3">
              {/* EN Name */}
              <div>
                <Label>Name (English) *</Label>
                <Input value={name} onChange={e => setName(e.target.value)} />
              </div>
              {/* Description */}
              <div>
                <Label>Description (English)</Label>
                <Input value={description} onChange={e => setDescription(e.target.value)} />
              </div>

              {/* Multi-language toggle */}
              <button type="button" onClick={() => setShowLangFields(!showLangFields)}
                className="flex items-center gap-1 text-sm text-primary hover:underline">
                {showLangFields ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                {showLangFields ? 'Hide' : 'Show'} Multi-language Fields
              </button>

              {showLangFields && (
                <>
                  <div className="border-t pt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <Label>Name (中文)</Label>
                      <Input value={nameZh} onChange={e => setNameZh(e.target.value)} />
                    </div>
                    <div>
                      <Label>Name (Español)</Label>
                      <Input value={nameEs} onChange={e => setNameEs(e.target.value)} />
                    </div>
                    <div>
                      <Label>Name (Français)</Label>
                      <Input value={nameFr} onChange={e => setNameFr(e.target.value)} />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    <div>
                      <Label>Description (中文)</Label>
                      <Input value={descriptionZh} onChange={e => setDescriptionZh(e.target.value)} />
                    </div>
                    <div>
                      <Label>Description (Español)</Label>
                      <Input value={descriptionEs} onChange={e => setDescriptionEs(e.target.value)} />
                    </div>
                    <div>
                      <Label>Description (Français)</Label>
                      <Input value={descriptionFr} onChange={e => setDescriptionFr(e.target.value)} />
                    </div>
                  </div>
                </>
              )}

              <div className="border-t pt-3 grid grid-cols-2 gap-3">
                <div>
                  <Label>Unit Type</Label>
                  <select value={unitType} onChange={e => setUnitType(e.target.value)}
                    className="w-full h-10 px-3 rounded-md border border-input bg-white text-sm">
                    <option value="per_day">Per Day</option>
                    <option value="per_pax">Per Person</option>
                    <option value="per_trip">Per Trip</option>
                  </select>
                </div>
                <div>
                  <Label>Unit Price (USD)</Label>
                  <Input type="number" min={0} step={0.01} value={unitPrice} onChange={e => setUnitPrice(Number(e.target.value))} />
                </div>
                <div>
                  <Label>Category</Label>
                  <select value={category} onChange={e => setCategory(e.target.value)}
                    className="w-full h-10 px-3 rounded-md border border-input bg-white text-sm">
                    <option value="">Select category</option>
                    <option value="guide">Guide</option>
                    <option value="transport">Transport</option>
                    <option value="hotel">Hotel</option>
                    <option value="meal">Meal</option>
                    <option value="ticket">Ticket</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <Label>Sort Order</Label>
                  <Input type="number" min={0} value={sortOrder} onChange={e => setSortOrder(Number(e.target.value))} />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
                <Button onClick={handleSave} disabled={!name || saving}>
                  {saving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</> : 'Save'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3 font-medium">Name</th>
              <th className="text-left p-3 font-medium">Type</th>
              <th className="text-left p-3 font-medium">Price</th>
              <th className="text-left p-3 font-medium">Category</th>
              <th className="text-left p-3 font-medium">Order</th>
              <th className="text-left p-3 font-medium">Status</th>
              <th className="text-left p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {services.length === 0 ? (
              <tr><td colSpan={7} className="p-6 text-center text-muted-foreground">No services found</td></tr>
            ) : services.map((svc) => (
              <tr key={svc.id} className="border-b hover:bg-gray-50/50">
                <td className="p-3 font-medium">
                  {displayName(svc)}
                  {svc.name_zh && locale !== 'zh' && <span className="text-xs text-muted-foreground ml-1">({svc.name_zh})</span>}
                </td>
                <td className="p-3">
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{svc.unit_type}</span>
                </td>
                <td className="p-3">${svc.unit_price}</td>
                <td className="p-3">{svc.category || '-'}</td>
                <td className="p-3">{svc.sort_order}</td>
                <td className="p-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    svc.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}>{svc.status}</span>
                </td>
                <td className="p-3">
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(svc)}>
                      <Edit3 className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-red-600" onClick={() => handleDelete(svc.id)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
        <p className="font-medium mb-1">💡 About Base Services</p>
        <p>Base services are the smallest service units — editable by admin via the Edit button. Pre-seeded with common services like airport transfer, guide services (EN/ES/FR), vehicle, hotel, and meals.</p>
        <p className="mt-1">Pricing: <strong>Per Day</strong> = price × qty × total_days | <strong>Per Person</strong> = price × qty × pax | <strong>Per Trip</strong> = price × qty</p>
      </div>
    </AdminLayout>
  );
}
