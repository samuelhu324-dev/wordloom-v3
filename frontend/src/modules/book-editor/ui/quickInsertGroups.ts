import type { MessageKey } from '@/i18n/I18nContext';
import type { QuickInsertAction, TranslateFn } from '../model/quickActions';

const GROUP_DEFINITIONS: Array<{ titleKey: MessageKey; actionIds: string[] }> = [
  { titleKey: 'books.blocks.editor.quickMenu.groups.favorites', actionIds: ['todo', 'bulleted-list', 'numbered-list'] },
  { titleKey: 'books.blocks.editor.quickMenu.groups.structure', actionIds: ['callout', 'quote', 'panel'] },
];

const FALLBACK_GROUP_KEY: MessageKey = 'books.blocks.editor.quickMenu.groups.more';

export interface QuickInsertGroup {
  title: string;
  actions: QuickInsertAction[];
}

export const groupQuickInsertActions = (actions: QuickInsertAction[], t: TranslateFn): QuickInsertGroup[] => {
  const actionMap = new Map(actions.map((action) => [action.id, action]));
  const grouped: QuickInsertGroup[] = [];

  GROUP_DEFINITIONS.forEach((definition) => {
    const groupItems = definition.actionIds
      .map((id) => actionMap.get(id))
      .filter((item): item is QuickInsertAction => Boolean(item));
    if (groupItems.length > 0) {
      grouped.push({ title: t(definition.titleKey), actions: groupItems });
      groupItems.forEach((item) => actionMap.delete(item.id));
    }
  });

  if (actionMap.size > 0) {
    grouped.push({ title: t(FALLBACK_GROUP_KEY), actions: Array.from(actionMap.values()) });
  }

  return grouped;
};
