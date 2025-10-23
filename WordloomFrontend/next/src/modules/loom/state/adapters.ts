export function adaptAdvancedToQuery(adv: any) {
  const q: Record<string, any> = {};
  if (adv?.keywords) q.q = adv.keywords;
  if (adv?.sourceSelect) q.source_name = adv.sourceSelect;
  if (adv?.regex) q.regex = true;
  if (adv?.exact) q.exact = true;
  return q;
}
