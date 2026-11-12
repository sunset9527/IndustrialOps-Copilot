import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import DiagnosisResult from '../src/components/DiagnosisResult.vue'

describe('DiagnosisResult', () => {
  it('keeps candidate causes, safety prerequisites, uncertainty and citations visibly separate', () => {
    const wrapper = mount(DiagnosisResult, {
      props: {
        result: {
          status: 'answered',
          confirmed_facts: ['报警 2066 与换刀中断有关。'],
          candidate_causes: ['换刀位置确认未完成。'],
          inspection_steps: ['确认已执行能量隔离。'],
          safety_prerequisites: ['停机、断电并挂牌上锁。'],
          uncertainties: ['不能依据当前证据确定唯一根因。'],
          required_information: [],
          escalation_conditions: ['状态异常时升级人工工程师。'],
          citations: [{
            source_id: 'haas-ngc-operator',
            document_revision: '2025',
            page_number: 87,
            evidence_locator: 'chapter-5/tool-changer',
          }],
        },
      },
    })

    expect(wrapper.text()).toContain('候选原因')
    expect(wrapper.text()).toContain('换刀位置确认未完成。')
    expect(wrapper.text()).toContain('安全前置条件')
    expect(wrapper.text()).toContain('停机、断电并挂牌上锁。')
    expect(wrapper.text()).toContain('不确定性')
    expect(wrapper.text()).toContain('不能依据当前证据确定唯一根因。')
    expect(wrapper.text()).toContain('haas-ngc-operator · 修订版 2025 · 第 87 页')
  })
})
