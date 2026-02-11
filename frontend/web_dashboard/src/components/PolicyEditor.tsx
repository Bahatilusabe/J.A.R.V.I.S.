import { useState } from 'react'
import type { HealingPolicy } from '../types'
import policyService from '../services/policy.service'

interface PolicyEditorProps {
  policy: HealingPolicy
  onClose: () => void
  onSaved: (updated: HealingPolicy) => void
}

export default function PolicyEditor({ policy, onClose, onSaved }: PolicyEditorProps) {
  const [name, setName] = useState(policy.name)
  const [description, setDescription] = useState(policy.description || '')
  const [conditionsText, setConditionsText] = useState((policy.conditions || []).join('\n'))
  const [enabled, setEnabled] = useState(Boolean(policy.enabled))
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      const updates: Partial<HealingPolicy> = {
        name,
        description,
        conditions: conditionsText.split('\n').map((s) => s.trim()).filter(Boolean),
        enabled,
      }
      const updated = await policyService.updatePolicy(policy.id, updates)
      onSaved(updated)
    } catch (err) {
      console.warn('Failed to update policy', err)
      // Best-effort: fall back to local update
      onSaved({ ...policy, name, description, conditions: conditionsText.split('\n').map((s) => s.trim()).filter(Boolean), enabled })
    } finally {
      setSaving(false)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-slate-800 border border-slate-700 rounded p-6 mx-4">
        <h2 className="text-lg font-semibold text-slate-100">Edit Policy</h2>

        <div className="mt-4 grid grid-cols-1 gap-3">
          <label htmlFor="policy-name" className="text-xs text-slate-300">Name</label>
          <input id="policy-name" aria-label="Policy name" className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-100" value={name} onChange={(e) => setName(e.target.value)} />

          <label htmlFor="policy-desc" className="text-xs text-slate-300">Description</label>
          <textarea id="policy-desc" aria-label="Policy description" className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-100" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />

          <label htmlFor="policy-conds" className="text-xs text-slate-300">Conditions (one per line)</label>
          <textarea id="policy-conds" aria-label="Policy conditions" className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-100 font-mono" rows={4} value={conditionsText} onChange={(e) => setConditionsText(e.target.value)} />

          <div className="flex items-center gap-3">
            <input id="policy-enabled" aria-label="Policy enabled" type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
            <label htmlFor="policy-enabled" className="text-sm text-slate-200">Enabled</label>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-3 py-1 rounded bg-slate-700 text-slate-200">Cancel</button>
          <button onClick={save} disabled={saving} className="px-3 py-1 rounded bg-primary text-white">
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
