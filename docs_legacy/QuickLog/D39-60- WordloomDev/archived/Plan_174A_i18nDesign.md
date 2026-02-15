行，恭喜你从「键盘炼狱」毕业，现在终于可以搞文明社会的东西了：多语言 😄

**状态（2025-12-06）**：✅ 已完成。实现细节记录在 `assets/docs/ADR/ADR-154-plan174-i18n.md`，并同步到 `DDD_RULES.yaml`(POLICY-I18N-PLAN174A-UI-LANGUAGE)、`HEXAGONAL_RULES.yaml`(i18n_runtime_strategy) 与 `VISUAL_RULES.yaml`(navigation_language_switcher)。本计划保留作为设计依据。

下面这一份就是可以直接丢给 Copilot 的计划书，按顺序执行即可。你可以整体贴进去（或者拆成几段 TODO）。

一、总体目标 & 范围（给 Copilot 的简述）

给 Wordloom 做一套「UI 语言切换：简体中文 / English」机制。

约束：

只翻译 UI 文案（按钮、菜单、提示、错误信息），不翻译业务数据（Book 名、Block 内容、翻译文本等）。

语言切换不改变 URL 结构（先不做 /en /zh 的路由前缀），使用「用户设置 + localStorage/cookie」来记住选择。

方案需要兼容 Next.js App Router（当前前端栈）+ React。

二、Domain / 后端层面的设计
1. User Settings：增加 UI 语言字段

在用户设置 / Profile 相关的 Domain 模块中：

// modules/users/domain/UserSettings.ts
type UiLanguage = 'zh-CN' | 'en-US';

class UserSettings {
  // ...
  uiLanguage: UiLanguage; // default: 'zh-CN'
}


需要的行为：

setUiLanguage(lang: UiLanguage): void


不做复杂逻辑，只是赋值 + 基本校验（必须是支持的枚举）。

对应仓储（UserSettingsRepository）加一个字段 ui_language，
API：GET/PUT /me/settings 时一并读写。

注：如果暂时不想动用户表，可以先只在前端用 localStorage，后端字段可以作为第二阶段。

三、前端 i18n 基础结构
2. 新建 i18n 目录 & 配置

在前端（假设是 frontend/）里新增：

frontend/
  src/
    i18n/
      locales/
        en-US.ts
        zh-CN.ts
      config.ts
      I18nContext.tsx
      useI18n.ts
      LanguageSwitcher.tsx

2.1 locales/*.ts：语言字典
// src/i18n/locales/en-US.ts
export const enUS = {
  'app.title': 'Wordloom',
  'nav.libraries': 'Libraries',
  'nav.bookshelves': 'Bookshelves',
  'nav.basement': 'Basement',
  'button.save': 'Save',
  'button.cancel': 'Cancel',
  'basement.empty': 'No books in basement.',
  // ... 后续逐步补充
} as const;

// src/i18n/locales/zh-CN.ts
export const zhCN = {
  'app.title': 'Wordloom',
  'nav.libraries': '文库',
  'nav.bookshelves': '书架',
  'nav.basement': '地窖',
  'button.save': '保存',
  'button.cancel': '取消',
  'basement.empty': '地窖里还没有书。',
  // ... 对应 en-US 的 key
} as const;


约定：

key 用「模块.语义」命名：nav.*, button.*, basement.*, editor.* 等；

不要用纯中文当 key（后续加语言会痛苦）。

2.2 config.ts：全局配置
// src/i18n/config.ts
export const supportedLanguages = ['zh-CN', 'en-US'] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];

export const defaultLanguage: SupportedLanguage = 'zh-CN';

3. I18nContext：React 上下文
// src/i18n/I18nContext.tsx
import React, { createContext, useEffect, useState } from 'react';
import { enUS } from './locales/en-US';
import { zhCN } from './locales/zh-CN';
import { defaultLanguage, type SupportedLanguage } from './config';

const dictionaries = {
  'zh-CN': zhCN,
  'en-US': enUS,
} as const;

type Messages = typeof enUS;

type I18nContextValue = {
  lang: SupportedLanguage;
  messages: Messages;
  t: (key: keyof Messages, vars?: Record<string, string | number>) => string;
  setLang: (lang: SupportedLanguage) => void;
};

export const I18nContext = createContext<I18nContextValue | null>(null);

const STORAGE_KEY = 'wordloom.uiLanguage';

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<SupportedLanguage>(defaultLanguage);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY) as SupportedLanguage | null;
    if (stored && (stored === 'zh-CN' || stored === 'en-US')) {
      setLangState(stored);
    }
  }, []);

  const setLang = (next: SupportedLanguage) => {
    setLangState(next);
    window.localStorage.setItem(STORAGE_KEY, next);
    // TODO: 同步到后端 /me/settings（后续步骤）
  };

  const messages = dictionaries[lang];

  const t: I18nContextValue['t'] = (key, vars) => {
    let template = messages[key] ?? (key as string);
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        template = template.replace(new RegExp(`{${k}}`, 'g'), String(v));
      }
    }
    return template;
  };

  return (
    <I18nContext.Provider value={{ lang, messages, t, setLang }}>
      {children}
    </I18nContext.Provider>
  );
};

4. useI18n hook
// src/i18n/useI18n.ts
import { useContext } from 'react';
import { I18nContext } from './I18nContext';

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx; // { lang, t, setLang, messages }
}

5. 在根布局中挂 Provider

在 Next.js App Router 下（例如 app/layout.tsx）：

// app/layout.tsx
import { I18nProvider } from '@/src/i18n/I18nContext';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}


后续可以根据 lang 动态设置 <html lang="">，第一步可以先写死。

四、语言切换组件 & 替换文案
6. LanguageSwitcher 组件
// src/i18n/LanguageSwitcher.tsx
import { useI18n } from './useI18n';

export function LanguageSwitcher() {
  const { lang, setLang } = useI18n();

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => setLang('zh-CN')}
        aria-pressed={lang === 'zh-CN'}
      >
        中
      </button>
      <span>/</span>
      <button
        type="button"
        onClick={() => setLang('en-US')}
        aria-pressed={lang === 'en-US'}
      >
        EN
      </button>
    </div>
  );
}


把这个按钮放到你顶部导航 / 设置面板里即可。

7. 替换现有硬编码文案

给 Copilot 的具体操作指示：

搜索所有中文/英文硬编码 UI 文案，比如 "文库", "Basement", "Save", "取消" 等；

对每一处：

在 locales/en-US.ts / zh-CN.ts 中新增对应 key；

在组件里用 const { t } = useI18n(); 引入；

把原来的文字替换为 t('nav.libraries') 等。

示例：

// 之前
<Link href="/admin/libraries">文库</Link>

// 之后
import { useI18n } from '@/src/i18n/useI18n';

const Nav = () => {
  const { t } = useI18n();
  return <Link href="/admin/libraries">{t('nav.libraries')}</Link>;
};

五、与后端用户设置同步（可选第二阶段）
8. 前端从 /me/settings 拉取默认语言

在 App 启动时（例如 I18nProvider 的 useEffect 中）：

如果 localStorage 没有语言设置，则调用 /me/settings；

若后端返回 uiLanguage 字段，则以它作为初始语言，并写入 localStorage。

9. 切换语言时同步到后端

在 setLang 中追加：

fetch('/api/me/settings', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ uiLanguage: next }),
});


这部分可以用你现有的 API Client 封装，不要求马上实现，保留 TODO 注释即可。

六、验证 & 回归 Checklist

让 Copilot 写/补充以下测试（Vitest/Playwright 任选）：

语言切换：

默认进入时使用 defaultLanguage 或 localStorage 值；

点击切换按钮后，UI 文字变更，localStorage wordloom.uiLanguage 更新。

同一组件多次渲染：

useI18n 不会导致无限重渲染；

切换语言只影响实际用到 t() 的组件。

错误 key 行为：

当 t('unknown.key') 时，返回 key 本身（或明确 fallback），避免页面崩溃。

七、给 Copilot 的一句总指令（可以原样贴）

任务说明（总结）：

为 Wordloom 前端实现一个简单的 UI i18n 系统，支持 zh-CN / en-US 切换。

使用 src/i18n 目录存放语言字典和 I18nProvider，通过 React Context + useI18n() 提供 t(key)。

语言偏好存入 localStorage（key: wordloom.uiLanguage），之后再与 /me/settings 同步。

不修改 keyboardDecider / block 编辑器逻辑，只替换 UI 文案。

需要提供：I18nProvider、useI18n、LanguageSwitcher、locales/en-US.ts & zh-CN.ts，以及一批将现有硬编码中文/英文替换为 t() 的示例组件。

这样一份丢给 Copilot，它基本可以照着把骨架搭完，你只需要审一下 key 命名和中文文案就行了。等 UI 稳定之后，再考虑要不要升级成 URL 级别的 /en、/zh 多语言路由，那就是下一季 DLC 的事情了。