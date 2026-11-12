import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import DiagnosisWorkbench from '../src/components/DiagnosisWorkbench.vue'

const cncAsset = {
  asset_id: 'cnc-demo-001',
  pack_id: 'cnc_pack_v1.0.0',
  model_name: 'VF-2',
  controller_or_firmware_scope: 'NGC',
}

describe('DiagnosisWorkbench', () => {
  it('constructs the diagnosis request from the selected asset server context', async () => {
    const request = vi.fn().mockResolvedValue({
      status: 'answered',
      confirmed_facts: [], candidate_causes: ['换刀位置确认未完成。'], inspection_steps: [],
      safety_prerequisites: [], uncertainties: [], required_information: [], escalation_conditions: [], citations: [],
    })
    const wrapper = mount(DiagnosisWorkbench, {
      props: { asset: cncAsset },
      global: { provide: { api: { request } } },
    })

    await wrapper.get('textarea[name="question"]').setValue('报警 2066，换刀中断。')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(request).toHaveBeenCalledWith('/api/diagnosis/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: '报警 2066，换刀中断。',
        pack_id: 'cnc_pack_v1.0.0',
        asset_id: 'cnc-demo-001',
        model: 'VF-2',
        controller: 'NGC',
      }),
    })
    expect(wrapper.text()).toContain('换刀位置确认未完成。')
  })

  it('clears an earlier device result when the selected asset changes', async () => {
    const request = vi.fn().mockResolvedValue({
      status: 'answered',
      confirmed_facts: [], candidate_causes: ['仅属于 CNC 的候选原因。'], inspection_steps: [],
      safety_prerequisites: [], uncertainties: [], required_information: [], escalation_conditions: [], citations: [],
    })
    const wrapper = mount(DiagnosisWorkbench, {
      props: { asset: cncAsset },
      global: { provide: { api: { request } } },
    })
    await wrapper.get('textarea[name="question"]').setValue('CNC 报警')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('仅属于 CNC 的候选原因。')

    await wrapper.setProps({
      asset: {
        asset_id: 'pump-demo-001', pack_id: 'dry_vacuum_pump_pack_v1.0.0',
        model_name: 'nXDS', controller_or_firmware_scope: null,
      },
    })

    expect(wrapper.text()).not.toContain('仅属于 CNC 的候选原因。')
  })
})
