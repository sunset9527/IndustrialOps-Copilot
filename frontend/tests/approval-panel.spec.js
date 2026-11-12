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

  it('requires a rejection reason before submitting to the dedicated reject endpoint', async () => {
    const request = vi.fn().mockResolvedValue({ status: 'cancelled' })
    const wrapper = mount(ApprovalPanel, {
      props: { workOrder: { work_order_id: 'wo-002', status: 'draft' }, role: 'admin' },
      global: { provide: { api: { request } } },
    })

    await wrapper.get('button[name="reject"]').trigger('click')
    expect(wrapper.get('[role="alert"]').text()).toContain('请填写拒绝理由')
    expect(request).not.toHaveBeenCalled()

    await wrapper.get('textarea[name="rejectionReason"]').setValue('证据不足，需补充现场信息。')
    await wrapper.get('button[name="reject"]').trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith('/api/work-orders/wo-002/reject', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: '证据不足，需补充现场信息。' }),
    })
    expect(wrapper.text()).toContain('cancelled')
  })

  it('requests a server refresh when another approver has already decided', async () => {
    const wrapper = mount(ApprovalPanel, { props: { workOrder: { work_order_id: 'wo-003', status: 'draft' }, role: 'approver' }, global: { provide: { api: { request: vi.fn().mockRejectedValue({ code: 'approval_already_decided' }) } } } })
    await wrapper.get('button[name="approve"]').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('refresh')).toHaveLength(1)
  })
})
