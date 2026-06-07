'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { MessageCircle, X, Send, Phone, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '@/lib/api';

export function InquiryForm() {
  const t = useTranslations('enquiry');
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', phone: '', destination: '', pax_count: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post('/enquiries', {
        ...form,
        pax_count: form.pax_count ? parseInt(form.pax_count, 10) : null,
      });
      setDone(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({ name: '', email: '', phone: '', destination: '', pax_count: '', message: '' });
    setDone(false);
    setError('');
  };

  return (
    <>
      {/* Floating trigger button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-medium text-white shadow-lg hover:bg-primary/90 transition-all"
        >
          <MessageCircle className="h-5 w-5" />
          {t('askUs')}
        </button>
      )}

      {/* Enquiry panel */}
      {open && (
        <div className="fixed bottom-6 right-6 z-40 w-96 max-w-[calc(100vw-2rem)] rounded-2xl border bg-white shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between bg-primary px-5 py-4 text-white">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              <span className="font-semibold">{t('title')}</span>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => setCollapsed(!collapsed)} className="rounded p-1 hover:bg-white/20">
                {collapsed ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
              <button onClick={() => { setOpen(false); resetForm(); }} className="rounded p-1 hover:bg-white/20">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Phone line */}
          <div className="flex items-center gap-2 border-b bg-gray-50 px-5 py-2.5 text-sm text-muted-foreground">
            <Phone className="h-3.5 w-3.5" />
            <span>{t('phoneLabel')}: <a href="tel:+8610-8888-8888" className="font-medium text-primary hover:underline">+86 10-8888-8888</a></span>
            <span className="ml-auto rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700">{t('support247')}</span>
          </div>

          {/* Body */}
          {!collapsed && (
            <div className="px-5 py-4">
              {done ? (
                <div className="text-center py-8">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                    <Send className="h-6 w-6 text-green-600" />
                  </div>
                  <p className="font-medium text-gray-800">{t('success')}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{t('successMessage')}</p>
                  <Button variant="outline" size="sm" className="mt-4" onClick={resetForm}>
                    {t('newEnquiry')}
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1">{t('name')} *</label>
                      <input
                        required
                        value={form.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        placeholder={t('namePlaceholder')}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1">{t('email')} *</label>
                      <input
                        required
                        type="email"
                        value={form.email}
                        onChange={(e) => handleChange('email', e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        placeholder={t('emailPlaceholder')}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1">{t('phone')}</label>
                      <input
                        value={form.phone}
                        onChange={(e) => handleChange('phone', e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        placeholder={t('phonePlaceholder')}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1">{t('destination')}</label>
                      <input
                        value={form.destination}
                        onChange={(e) => handleChange('destination', e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        placeholder={t('destinationPlaceholder')}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">{t('pax')}</label>
                    <input
                      type="number" min="1" max="50"
                      value={form.pax_count}
                      onChange={(e) => handleChange('pax_count', e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder={t('paxPlaceholder')}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">{t('message')} *</label>
                    <textarea
                      required
                      rows={3}
                      value={form.message}
                      onChange={(e) => handleChange('message', e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                      placeholder={t('messagePlaceholder')}
                    />
                  </div>

                  {error && (
                    <p className="text-xs text-red-500">{error}</p>
                  )}

                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        {t('sending')}
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <Send className="h-4 w-4" />
                        {t('submit')}
                      </span>
                    )}
                  </Button>
                </form>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
}
