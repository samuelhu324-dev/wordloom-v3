// Simple toast utility (no external deps)
// Usage: showToast("Message", 3000)

let container: HTMLDivElement | null = null;

function ensureContainer() {
  if (typeof window === 'undefined') return null;
  if (!container) {
    container = document.createElement('div');
    container.id = 'wl-toast-container';
    container.style.position = 'fixed';
    container.style.top = '16px';
    container.style.right = '16px';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '8px';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }
  return container;
}

export function showToast(message: string, duration = 3000) {
  const root = ensureContainer();
  if (!root) return;
  const item = document.createElement('div');
  item.textContent = message;
  item.style.padding = '8px 12px';
  item.style.background = 'rgba(255,255,255,0.95)';
  item.style.border = '1px solid var(--color-border-soft)';
  item.style.borderRadius = '6px';
  item.style.fontSize = '14px';
  item.style.color = 'var(--color-text-primary)';
  item.style.boxShadow = '0 2px 6px rgba(0,0,0,0.08)';
  item.style.cursor = 'pointer';
  item.style.transition = 'opacity 200ms ease';
  item.style.opacity = '0';
  requestAnimationFrame(() => { item.style.opacity = '1'; });
  item.onclick = () => {
    item.style.opacity = '0';
    setTimeout(() => root.removeChild(item), 200);
  };
  root.appendChild(item);
  setTimeout(() => {
    item.style.opacity = '0';
    setTimeout(() => {
      if (item.parentElement === root) root.removeChild(item);
    }, 200);
  }, duration);
}
