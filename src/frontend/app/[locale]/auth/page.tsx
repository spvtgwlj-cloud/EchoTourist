'use client';

import { useTranslations } from 'next-intl';
import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Mail, Lock, User, Chrome, AlertCircle, Loader2 } from 'lucide-react';
import { useLocale } from 'next-intl';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function AuthPage() {
  const t = useTranslations('auth');
  const ct = useTranslations('common');
  const locale = useLocale();
  const router = useRouter();
  const searchParams = useSearchParams();
  const googleBtnRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<'signin' | 'signup'>(
    searchParams.get('mode') === 'signup' ? 'signup' : 'signin',
  );
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [googleLoading, setGoogleLoading] = useState(false);

  const { login, register, googleLogin, isLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.push(`/${locale}`);
    }
  }, [isAuthenticated, locale, router]);

  // 加载 Google Identity Services
  useEffect(() => {
    if (typeof window === 'undefined' || isAuthenticated) return;

    // 动态加载 Google 脚本
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.google && googleBtnRef.current) {
        window.google.accounts.id.initialize({
          client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
          callback: handleGoogleCredential,
        });
        // 用按钮 ID 渲染
        window.google.accounts.id.renderButton(
          googleBtnRef.current,
          { theme: 'outline', size: 'large', width: '100%', text: 'signin_with', shape: 'rect' },
        );
      }
    };
    document.body.appendChild(script);

    return () => {
      // 清理
      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing && document.body.contains(existing)) {
        document.body.removeChild(existing);
      }
    };
  }, [isAuthenticated]);

  const handleGoogleCredential = async (response: { credential: string }) => {
    setGoogleLoading(true);
    setError('');
    try {
      await googleLogin(response.credential);
      router.push(`/${locale}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed');
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError(t('required') || 'Please fill in all fields');
      return;
    }

    try {
      if (mode === 'signin') {
        await login(email, password);
      } else {
        if (!name) { setError(t('nameRequired') || 'Name is required'); return; }
        await register(email, password, name);
      }
      router.push(`/${locale}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>{mode === 'signin' ? t('welcomeBack') : t('createAccount')}</CardTitle>
          <CardDescription>
            {mode === 'signin' ? t('welcomeBack') : t('signUpAgreement')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-600">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t('name') || 'Name'}
                  className="w-full rounded-md border border-input bg-background py-2.5 pl-10 pr-4 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            )}
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('email') || 'Email'}
                className="w-full rounded-md border border-input bg-background py-2.5 pl-10 pr-4 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('password') || 'Password'}
                className="w-full rounded-md border border-input bg-background py-2.5 pl-10 pr-4 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
              {isLoading ? ct('loading') : (mode === 'signin' ? t('welcomeBack') : t('createAccount'))}
            </Button>
          </form>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">{ct('or')}</span>
            </div>
          </div>

          <div className="relative">
            {googleLoading && (
              <div className="absolute inset-0 flex items-center justify-center z-10 bg-card/80 rounded-md">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            )}
            <div ref={googleBtnRef} className="flex justify-center" />
            {!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && (
              <DevGoogleLogin onError={(msg) => setError(msg)} />
            )}
          </div>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            {mode === 'signin' ? t('noAccount') : t('hasAccount')}{' '}
            <button
              onClick={() => { setMode(mode === 'signin' ? 'signup' : 'signin'); setError(''); }}
              className="text-primary hover:underline font-medium"
            >
              {mode === 'signin' ? t('createAccount') : t('welcomeBack')}
            </button>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

// ── 开发模式 Google 登录 ──

function DevGoogleLogin({ onError }: { onError: (msg: string) => void }) {
  const locale = useLocale();
  const [devEmail, setDevEmail] = useState('');
  const [devLoading, setDevLoading] = useState(false);
  const [showDevForm, setShowDevForm] = useState(false);

  const handleDevGoogleLogin = async () => {
    setDevLoading(true);
    onError('');
    try {
      const email = devEmail.trim() || `devuser_${Date.now()}@example.com`;
      const name = email.split('@')[0];
      const res = await fetch('/api/v1/auth/google/dev', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Dev login failed' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      localStorage.setItem('auth_token', data.access_token);
      // 重新加载用户状态并跳转
      window.location.href = `/${locale}`;
    } catch (err: unknown) {
      onError(err instanceof Error ? err.message : 'Dev login failed');
    } finally {
      setDevLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      {/* Dev mode badge */}
      <div className="flex items-center justify-center gap-1.5 mb-1">
        <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
          🛠️ Dev Mode
        </span>
      </div>

      {showDevForm && (
        <div className="relative mb-2">
          <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="email"
            value={devEmail}
            onChange={(e) => setDevEmail(e.target.value)}
            placeholder="dev@example.com (optional, auto-generates if empty)"
            className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-4 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>
      )}

      <Button
        variant="outline"
        className="w-full border-amber-300 text-amber-700 hover:bg-amber-50 hover:text-amber-800"
        size="lg"
        type="button"
        disabled={devLoading}
        onClick={() => {
          if (showDevForm) {
            handleDevGoogleLogin();
          } else {
            setShowDevForm(true);
          }
        }}
      >
        {devLoading ? (
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
        ) : (
          <Chrome className="h-5 w-5 mr-2" />
        )}
        {showDevForm ? 'Dev Google Sign-In' : '🛠️ Dev Google Sign-In'}
      </Button>
      {showDevForm && (
        <p className="text-xs text-center text-muted-foreground">
          Enter a custom email or leave blank for a random email login
        </p>
      )}
    </div>
  );
}
