import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import ApprovalPanel from '../src/components/ApprovalPanel.vue'

describe('ApprovalPanel', () => {
  it('submits an approver decision to the dedicated approval endpoint', async () => {
    const request = vi.fn().mockResolvedValue({ status: 'approved' })
    const wrapper = mount(ApprovalPanel, {
      props: { workOrder: { work_order_id: 'wo-001', status: 'draft' }, role: 'approver' },
      global: { provide: { api: { request } } },
    })

    await wrapper.get('button[name="approve"]').trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith('/api/work-orders/wo-001/approve', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: null }),
    })
    expect(wrapper.text()).toContain('approved')
  })
})
