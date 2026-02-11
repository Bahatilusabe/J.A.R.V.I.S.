// Minimal toast hook used in the dashboard pages.
// If the project has a richer notification system, replace this implementation.
export function useToast() {
  const toast = ({ title, description, variant }: { title: string; description?: string; variant?: string }) => {
    // Keep simple: console and a non-blocking DOM update could be added here.
    // For now, fallback to console and a small non-intrusive alert for visibility in dev.
    // Avoid blocking alerts in production usage.
    // eslint-disable-next-line no-console
    console.log('[toast]', variant || 'info', title, description || '')
  }

  return { toast }
}

export default useToast
