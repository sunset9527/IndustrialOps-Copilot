import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'

import AssetOverview from '../src/components/AssetOverview.vue'

describe('AssetOverview', () => {
  it('renders the server-owned model and knowledge-pack context for each asset', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/diagnosis/:assetId', name: 'diagnosis', component: { template: '<div />' } },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
      ],
    })
    const wrapper = mount(AssetOverview, {
      props: {
        assets: [{
          asset_id: 'cnc-demo-001',
          display_name: 'CNC 演示机 001',
          equipment_model_id: 'haas-vf2-ngc',
          pack_id: 'cnc_pack_v1.0.0',
          manufacturer: 'Haas',
          model_name: 'VF-2',
          controller_or_firmware_scope: 'NGC',
          status: 'available',
          synthetic: true,
        }],
      },
      global: { plugins: [router] },
    })

    await router.push('/diagnosis/cnc-demo-001')
    await router.isReady()

    expect(wrapper.text()).toContain('Haas VF-2 / NGC')
    expect(wrapper.text()).toContain('cnc_pack_v1.0.0')
    expect(wrapper.text()).toContain('合成演示资产')
    expect(wrapper.get('a').attributes('href')).toBe('/diagnosis/cnc-demo-001')
  })
})
