import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';

// 静态导入所有语言的 messages（避免 Node.js ESM import() 的 JSON 缓存问题）
import enMessages from '../messages/en/common.json';
import zhMessages from '../messages/zh/common.json';
import esMessages from '../messages/es/common.json';

const allMessages: Record<string, any> = {
  en: enMessages,
  zh: zhMessages,
  es: esMessages,
};

const locales = ['en', 'zh', 'es'];

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !locales.includes(locale)) {
    locale = 'en';
  }

  if (!allMessages[locale]) {
    notFound();
  }

  return {
    locale,
    messages: allMessages[locale],
  };
});

export { locales };

