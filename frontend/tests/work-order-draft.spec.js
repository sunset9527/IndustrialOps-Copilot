import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import WorkOrderDraftDrawer from '../src/components/WorkOrderDraftDrawer.vue'

const asset = { asset_id: 'cnc-demo-001', display_name: 'CNC 演示机 001' }
const answeredDiagnosis = {
  request_id: 'diagnosis-001', status: 'answered',
  candidate_causes: ['换刀位置确认未完成。'], inspection_steps: ['确认能量隔离。'],
}

describe('WorkOrderDraftDrawer', () => {
  it('creates an evidence-bound draft only from an answered diagnosis and shows pending approval', async () => {
    const request = vi.fn().mockResolvedValue({
      work_order_id: 'wo-001', thread_id: 'thread-001', status: 'draft', approval_status: 'pending_approval', citations_snapshot: [],
    })
    const wrapper = mount(WorkOrderDraftDrawer, {
      props: { asset, diagnosis: answeredDiagnosis },
      global: { provide: { api: { request } } },
    })

    await wrapper.get('button[name="open-draft"]').trigger('click')
    await wrapper.get('input[name="title"]').setValue('检查 CNC 换刀位置确认')
    await wrapper.get('textarea[name="description"]').setValue('根据诊断记录检查位置确认链路。')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(request).toHaveBeenCalledWith('/api/work-orders/drafts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        diagnosis_request_id: 'diagnosis-001', asset_id: 'cnc-demo-001', title: '检查 CNC 换刀位置确认',
        description: '根据诊断记录检查位置确认链路。', priority: 'medium',
      }),
    })
    expect(wrapper.text()).toContain('等待人工审批')
    expect(wrapper.text()).toContain('thread-001')
  })

  it('does not expose draft creation for a blocked or evidence-insufficient diagnosis', () => {
    const wrapper = mount(WorkOrderDraftDrawer, {
      props: { asset, diagnosis: { ...answeredDiagnosis, status: 'blocked', inspection_steps: [] } },
      global: { provide: { api: { request: vi.fn() } } },
    })

    expect(wrapper.find('button[name="open-draft"]').exists()).toBe(false)
  })
})
