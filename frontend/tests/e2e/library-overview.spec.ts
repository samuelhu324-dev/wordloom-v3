import { test, expect } from '@playwright/test';

const ROUTE = '/admin/libraries';

const LIB_OVW_CREATE_VISIBLE = 'LIB-OVW-CreateVisible';
const LIB_OVW_TAGS_PLACEHOLDER = 'LIB-OVW-TagsPlaceholder';

function genLibraryName(prefix: string) {
  const suffix = Date.now().toString(36);
  return `${prefix}-${suffix}`;
}

test.describe('Library Overview', () => {
  test(`${LIB_OVW_CREATE_VISIBLE} 新建后无需刷新即可可见`, async ({ page }) => {
    const name = genLibraryName('E2E-Library');

    await page.goto(ROUTE);
    await page.getByTestId('library-create-button').click();
    await page.getByTestId('library-form-name').fill(name);
    await page.getByTestId('library-form-description').fill('E2E smoke description');
    await page.getByTestId('library-form-submit').click();

    const card = page.locator('[data-testid="library-card"]', { hasText: name }).first();
    await expect(card).toBeVisible();
  });

  test(`${LIB_OVW_TAGS_PLACEHOLDER} 清空 tags 后展示占位`, async ({ page }) => {
    const name = genLibraryName('E2E-Tags');
    const tagName = `TAG-${Date.now().toString(36).slice(-4)}`;

    await page.goto(ROUTE);
    await page.getByTestId('library-create-button').click();
    await page.getByTestId('library-form-name').fill(name);
    const tagInput = page.getByTestId('tag-multiselect-input');
    await tagInput.fill(tagName);
    await tagInput.press('Enter');
    await page.getByTestId('library-form-submit').click();

    const card = page.locator('[data-testid="library-card"]', { hasText: name }).first();
    await expect(card.getByText(tagName)).toBeVisible();

    await card.hover();
    await card.getByTestId('library-edit-button').click();

    const removeButtons = page.locator('[data-testid="tag-multiselect-remove"]');
    await expect(removeButtons.first()).toBeVisible();
    while (await removeButtons.count()) {
      await removeButtons.first().click();
    }

    await page.getByTestId('library-form-submit').click();
    await expect(card.getByTestId('library-tags-placeholder')).toBeVisible();
  });
});
