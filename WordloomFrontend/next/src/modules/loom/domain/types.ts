export type Entry = {
  id: number|string;
  text: string;
  translation: string;
  source_name?: string;
  created_at?: string;
};
export type Source = { id?: string|number; name: string };
