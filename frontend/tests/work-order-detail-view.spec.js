import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import WorkOrderDetailView from '../src/views/WorkOrderDetailView.vue'

describe('WorkOrderDetailView', () => {
  it('loads the server evidence snapshot and exposes approval only to an approver', async () => {
    const request = vi.fn().mockResolvedValue({ work_order_id: 'wo-001', status: 'draft', title: '检查换刀机构', citations_snapshot: [{ source_id: 'manual', page_number: 87 }], approval: null })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/work-orders/:workOrderId', component: WorkOrderDetailView }] })
    await router.push('/work-orders/wo-001'); await router.isReady()
    const wrapper = mount(WorkOrderDetailView, { global: { plugins: [router], provide: { api: { request }, auth: { user: ref({ role: 'approver' }) } } } })
    await flushPromises()
    expect(request).toHaveBeenCalledWith('/api/work-orders/wo-001')
    expect(wrapper.text()).toContain('manual')
    expect(wrapper.get('button[name="approve"]').exists()).toBe(true)
  })
})
