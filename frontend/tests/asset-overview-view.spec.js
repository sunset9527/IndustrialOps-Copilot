import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it, vi } from 'vitest'

import AssetOverviewView from '../src/views/AssetOverviewView.vue'

describe('AssetOverviewView', () => {
  it('loads and displays assets from the API', async () => {
    const request = vi.fn().mockResolvedValue({
      items: [{
        asset_id: 'pump-demo-001',
        display_name: '真空泵演示机 001',
        equipment_model_id: 'edwards-nxds-standard',
        pack_id: 'dry_vacuum_pump_pack_v1.0.0',
        manufacturer: 'Edwards',
        model_name: 'nXDS',
        controller_or_firmware_scope: null,
        status: 'available',
        synthetic: true,
      }],
    })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div />' } },
        { path: '/diagnosis/:assetId', name: 'diagnosis', component: { template: '<div />' } },
      ],
    })
    await router.push('/')
    await router.isReady()

    const wrapper = mount(AssetOverviewView, {
      global: { plugins: [router], provide: { api: { request } } },
    })
    await flushPromises()

    expect(request).toHaveBeenCalledWith('/api/equipment/assets')
    expect(wrapper.text()).toContain('真空泵演示机 001')
    expect(wrapper.text()).toContain('dry_vacuum_pump_pack_v1.0.0')
  })

  it('shows a retry path for a failed asset request and renders the recovered response', async () => {
    const request = vi.fn()
      .mockRejectedValueOnce({ code: 'http_error', status: 502 })
      .mockResolvedValueOnce({ items: [] })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { template: '<div />' } }],
    })
    await router.push('/')
    await router.isReady()
    const wrapper = mount(AssetOverviewView, {
      global: { plugins: [router], provide: { api: { request } } },
    })
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('暂时无法加载设备')
    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('当前没有可用的演示设备')
  })
})
