export type {
	BookDto,
	CreateBookRequest,
	UpdateBookRequest,
	BackendBook,
	BookMaturity,
} from './types';
export { toBookDto } from './types';
export { buildBookRibbon, MATURITY_RIBBON_LABELS } from './lib/ribbon';
export type { BookRibbonResult } from './lib/ribbon';
export type {
	BookCoverIconId,
	BookCoverIconGroup,
	BookCoverIconMeta,
} from './lib/book-cover-icons';
export { BOOK_COVER_ICON_CATALOG } from './lib/book-cover-icons';
