// Temporary debug tracer for detecting who causes full page navigations.
// Enable by setting `localStorage.setItem('jarvis_debug_location', '1')` or by adding ?debug=location to the URL.

declare global {
  interface Window {
    __JARVIS_DEBUG_LOCATION_INSTALLED?: boolean
  }
}

function getStack() {
  try {
    return new Error('Location change stack').stack
  } catch (err) {
    return 'no-stack'
  }
}

function emitEvent(detail: Record<string, unknown>) {
  try {
    const ev = new CustomEvent('jarvis:debug:location', { detail })
    window.dispatchEvent(ev)
  } catch (err) {
    // ignore
  }
}

export default function installDebugLocationTracer() {
  if (typeof window === 'undefined') return
  try {
    if (window.__JARVIS_DEBUG_LOCATION_INSTALLED) return
    window.__JARVIS_DEBUG_LOCATION_INSTALLED = true

    // Patch assign
    const origAssign = window.location.assign.bind(window.location) as (url: string | URL) => void
    window.location.assign = function (url: string | URL) {
      const stack = getStack()
      console.warn('[DebugLocationTracer] location.assign called', { url, stack })
      emitEvent({ type: 'assign', url, stack })
      return origAssign(url)
    }

    // Patch replace
    const origReplace = window.location.replace.bind(window.location) as (url: string | URL) => void
    window.location.replace = function (url: string | URL) {
      const stack = getStack()
      console.warn('[DebugLocationTracer] location.replace called', { url, stack })
      emitEvent({ type: 'replace', url, stack })
      return origReplace(url)
    }

    // Patch reload (some browsers ignore args - call without params)
    const origReload = window.location.reload.bind(window.location) as () => void
    window.location.reload = function (_forced?: boolean) {
      const stack = getStack()
      console.warn('[DebugLocationTracer] location.reload called', { forced: _forced, stack })
      emitEvent({ type: 'reload', forced: _forced, stack })
      return origReload()
    }

    // Try to patch href setter on Location.prototype (may fail in some browsers)
    try {
      const desc = Object.getOwnPropertyDescriptor(Location.prototype, 'href')
      if (desc && typeof desc.set === 'function') {
        const origSet = desc.set
        Object.defineProperty(Location.prototype, 'href', {
          ...desc,
          set: function (val: string) {
            const stack = getStack()
            console.warn('[DebugLocationTracer] location.href set', { val, stack })
            emitEvent({ type: 'href-set', val, stack })
            return origSet.call(this, val)
          },
        })
      }
    } catch (err) {
      console.warn('[DebugLocationTracer] failed to patch href setter', err)
    }

    // Patch history methods (pushState/replaceState) to log usage
    const origPush = history.pushState.bind(history) as (data: any, title: string, url?: string | URL | null) => void
    history.pushState = function (data: any, title: string, url?: string | URL | null) {
      const stack = getStack()
      console.debug('[DebugLocationTracer] history.pushState', { args: [data, title, url], stack })
      emitEvent({ type: 'pushState', args: [data, title, url], stack })
      return origPush(data, title, url)
    }

    const origReplaceState = history.replaceState.bind(history) as (data: any, title: string, url?: string | URL | null) => void
    history.replaceState = function (data: any, title: string, url?: string | URL | null) {
      const stack = getStack()
      console.debug('[DebugLocationTracer] history.replaceState', { args: [data, title, url], stack })
      emitEvent({ type: 'replaceState', args: [data, title, url], stack })
      return origReplaceState(data, title, url)
    }

    // Global beforeunload already exists in App; still log here for completeness
    window.addEventListener('beforeunload', () => {
      const stack = getStack()
      console.warn('[DebugLocationTracer] beforeunload', { href: window.location.href, stack })
      emitEvent({ type: 'beforeunload', href: window.location.href, stack })
    }, { capture: true })

    console.debug('[DebugLocationTracer] installed')
  } catch (err) {
    console.error('[DebugLocationTracer] failed to install', err)
  }
}