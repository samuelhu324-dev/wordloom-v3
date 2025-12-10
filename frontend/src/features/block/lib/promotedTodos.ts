import { BlockDto, TodoListBlockContent } from '@/entities/block';

export interface PromotedTodoItem {
  blockId: string;
  itemId: string;
  text: string;
  checked: boolean;
}

export const extractPromotedTodosFromBlocks = (blocks: BlockDto[]): PromotedTodoItem[] => {
  if (!Array.isArray(blocks) || blocks.length === 0) {
    return [];
  }

  return blocks
    .filter((block) => block.kind === 'todo_list')
    .flatMap((block) => {
      const content = block.content as TodoListBlockContent;
      const items = Array.isArray(content?.items) ? content.items : [];
      return items
        .filter((item) => item.isPromoted)
        .map((item) => ({
          blockId: block.id,
          itemId: item.id ?? '',
          text: item.text ?? '',
          checked: Boolean(item.checked),
        }));
    });
};
