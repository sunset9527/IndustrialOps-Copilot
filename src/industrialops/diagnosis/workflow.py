"""The v0.3 LangGraph diagnosis workflow with evidence-bound answer generation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from industrialops.diagnosis.context import EquipmentContextResolver, ResolvedEquipmentContext
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.evidence import EvidenceGapDetector
from industrialops.diagnosis.faults import FaultDiagnosisService
from industrialops.diagnosis.intent import IntentRoute, IntentRouter
from industrialops.diagnosis.safety import SafetyDecision, SafetyPolicyGate
from industrialops.diagnosis.schemas import Citation, DiagnosisRequest, DiagnosisResult, WorkflowEvent
from industrialops.knowledge.pack_loader import StructuredEvidence


EvidenceRetriever = Callable[[DiagnosisRequest, ResolvedEquipmentContext, IntentRoute], tuple[StructuredEvidence, ...]]


class DiagnosisGraphState(TypedDict, total=False):
    request_id: str
    request: dict[str, object]
    trace: tuple[str, ...]
    events: tuple[WorkflowEvent, ...]
    route: IntentRoute
    context: ResolvedEquipmentContext
    retrieved_evidence: tuple[StructuredEvidence, ...]
    compatible_evidence: tuple[StructuredEvidence, ...]
    safety: SafetyDecision
    evidence_decision: object
    result: DiagnosisResult


class DiagnosisWorkflow:
    """Execute a compiled StateGraph for one diagnosis request at a time."""

    def __init__(
        self,
        *,
        resolver: EquipmentContextResolver,
        retrieve: EvidenceRetriever,
        answer_generator: DeepSeekAnswerGenerator,
    ) -> None:
        self._resolver = resolver
        self._retrieve = retrieve
        self._answer_generator = answer_generator
        self._router = IntentRouter()
        self._safety_gate = SafetyPolicyGate()
        self._gap_detector = EvidenceGapDetector()
        self._fault_service = FaultDiagnosisService()
        self._graph = self._build_graph()

    def invoke(self, request: Mapping[str, object]) -> DiagnosisResult:
        request_id = request.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id is required")
        payload = {key: value for key, value in request.items() if key != "request_id"}
        state = self._graph.invoke({"request": payload, "request_id": request_id, "trace": (), "events": ()})
        return state["result"]

    def _build_graph(self):
        graph = StateGraph(DiagnosisGraphState)
        graph.add_node("intent_router", self._intent_router)
        graph.add_node("equipment_context_resolver", self._equipment_context_resolver)
        graph.add_node("evidence_retriever", self._evidence_retriever)
        graph.add_node("compatibility_validator", self._compatibility_validator)
        graph.add_node("fault_diagnosis_service", self._fault_diagnosis_service)
        graph.add_node("safety_policy_gate", self._safety_policy_gate)
        graph.add_node("evidence_gap_detector", self._evidence_gap_detector)
        graph.add_node("answer_composer", self._answer_composer)
        graph.add_edge(START, "intent_router")
        graph.add_conditional_edges(
            "intent_router",
            lambda state: "answer_composer" if state["route"].intent in {"out_of_scope", "work_order_draft"} else "equipment_context_resolver",
        )
        graph.add_conditional_edges(
            "equipment_context_resolver",
            lambda state: "safety_policy_gate" if state["context"].status in {"pack_unknown", "model_out_of_scope"} else "evidence_retriever",
        )
        graph.add_edge("evidence_retriever", "compatibility_validator")
        graph.add_edge("compatibility_validator", "fault_diagnosis_service")
        graph.add_edge("fault_diagnosis_service", "safety_policy_gate")
        graph.add_edge("safety_policy_gate", "evidence_gap_detector")
        graph.add_edge("evidence_gap_detector", "answer_composer")
        graph.add_edge("answer_composer", END)
        return graph.compile()

    @staticmethod
    def _trace(state: DiagnosisGraphState, node: str) -> tuple[str, ...]:
        return (*state.get("trace", ()), node)

    def _record(
        self,
        state: DiagnosisGraphState,
        node: str,
        started: float,
        *,
        status: str = "completed",
        input_count: int,
        output_count: int,
        reason: str | None = None,
    ) -> dict[str, object]:
        event = WorkflowEvent(
            node=node,
            status=status,
            duration_ms=(time.perf_counter() - started) * 1000,
            input_count=input_count,
            output_count=output_count,
            reason=reason,
        )
        return {"trace": self._trace(state, node), "events": (*state.get("events", ()), event)}

    @staticmethod
    def _request(state: DiagnosisGraphState) -> DiagnosisRequest:
        return DiagnosisRequest.model_validate(state["request"])

    def _intent_router(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        request = self._request(state)
        return {"route": self._router.route(request), **self._record(state, "intent_router", started, input_count=1, output_count=1)}

    def _equipment_context_resolver(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        return {"context": self._resolver.resolve(self._request(state)), **self._record(state, "equipment_context_resolver", started, input_count=1, output_count=1)}

    def _evidence_retriever(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        request = self._request(state)
        evidence = self._retrieve(request, state["context"], state["route"])
        return {"retrieved_evidence": evidence, **self._record(state, "evidence_retriever", started, input_count=1, output_count=len(evidence))}

    def _compatibility_validator(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        context = state["context"]
        evidence = tuple(item for item in state.get("retrieved_evidence", ()) if item.pack_id == context.pack_id)
        return {"compatible_evidence": evidence, **self._record(state, "compatibility_validator", started, input_count=len(state.get("retrieved_evidence", ())), output_count=len(evidence))}

    def _fault_diagnosis_service(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        evidence = state.get("compatible_evidence", ())
        return {"extraction": self._fault_service.extract(evidence), **self._record(state, "fault_diagnosis_service", started, input_count=len(evidence), output_count=1)}

    def _safety_policy_gate(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        request = self._request(state)
        context = state.get("context")
        if context is None:
            context = ResolvedEquipmentContext("pack_unknown", request.pack_id, None, None, None, None, None, "PACK_UNKNOWN")
        safety = self._safety_gate.evaluate(request, intent=state["route"].intent, context=context)
        return {"safety": safety, **self._record(state, "safety_policy_gate", started, status=safety.status, input_count=1, output_count=1, reason=safety.rule_ids[0] if safety.rule_ids else None)}

    def _evidence_gap_detector(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        decision = self._gap_detector.evaluate(state["route"].intent, state.get("compatible_evidence", ()))
        return {"evidence_decision": decision, **self._record(state, "evidence_gap_detector", started, status=decision.status, input_count=len(state.get("compatible_evidence", ())), output_count=1)}

    def _answer_composer(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        started = time.perf_counter()
        request = self._request(state)
        route = state["route"]
        trace = self._trace(state, "answer_composer")
        request_id = state.get("request_id")
        if not isinstance(request_id, str):
            raise ValueError("request_id is required")
        if route.intent == "out_of_scope":
            result = DiagnosisResult(
                request_id=request_id, status="out_of_scope", intent=route.intent,
                uncertainties=("该请求不在已加载设备知识包的工业运维范围内。",),
                generation={"provider": "policy_gate", "fallback_used": False}, workflow_trace=trace,
                workflow_events=self._events(state, trace, started, "out_of_scope"),
            )
            return {"result": result, "trace": trace}
        if route.intent == "work_order_draft":
            result = DiagnosisResult(
                request_id=request_id, status="needs_information", intent=route.intent,
                uncertainties=("请先完成并保存一次诊断，再使用工单草稿接口提交人工审批。",),
                recommended_next_action="create_work_order_draft_from_diagnosis",
                generation={"provider": "policy_gate", "fallback_used": False}, workflow_trace=trace,
                workflow_events=self._events(state, trace, started, "needs_information"),
            )
            return {"result": result, "trace": trace}

        safety = state.get("safety", SafetyDecision("allow"))
        if safety.status != "allow":
            status = "blocked" if safety.status in {"blocked", "escalate"} else "needs_information"
            result = DiagnosisResult(
                request_id=request_id, status=status, intent=route.intent,
                required_information=("请提供设备型号后再继续。",) if safety.status == "needs_information" else (),
                escalation_conditions=safety.rule_ids,
                generation={"provider": "policy_gate", "fallback_used": False}, workflow_trace=trace,
                workflow_events=self._events(state, trace, started, status, safety.rule_ids[0] if safety.rule_ids else None),
            )
            return {"result": result, "trace": trace}

        evidence_decision = state.get("evidence_decision")
        extraction = state.get("extraction")
        allowed_fields = getattr(evidence_decision, "allowed_fields", ())
        evidence = state.get("compatible_evidence", ())
        citations = {
            item.evidence_id: Citation(
                evidence_id=item.evidence_id, pack_id=item.pack_id, source_id=item.source_id,
                document_revision=self._resolver.document_revision(item.pack_id, item.source_id),
                page_number=item.page_number, evidence_locator=item.evidence_locator,
            )
            for item in evidence
        }
        generated = self._answer_generator.generate(
            question=request.question,
            approved_evidence={item.evidence_id: item.evidence_text for item in evidence},
            citations=citations,
            allowed_fields=allowed_fields,
        )
        used_ids = tuple(dict.fromkeys(evidence_id for values in generated.items.values() for _, ids in values for evidence_id in ids))
        status = "answered" if getattr(evidence_decision, "status", "insufficient_evidence") == "sufficient" else "insufficient_evidence"
        result = DiagnosisResult(
            request_id=request_id, status=status, intent=route.intent,
            confirmed_facts=tuple(text for text, _ in generated.items.get("confirmed_facts", ())) or getattr(extraction, "confirmed_facts", ()),
            candidate_causes=tuple(text for text, _ in generated.items.get("candidate_causes", ())) or getattr(extraction, "candidate_causes", ()),
            inspection_steps=tuple(text for text, _ in generated.items.get("inspection_steps", ())) or getattr(extraction, "inspection_steps", ()),
            safety_prerequisites=getattr(extraction, "safety_prerequisites", ()),
            uncertainties=tuple(getattr(evidence_decision, "missing_evidence_types", ())),
            citations=tuple(citations[item] for item in used_ids),
            generation={"provider": generated.provider, "model": generated.model, "fallback_used": generated.provider != "deepseek", "fallback_reason": generated.fallback_reason},
            workflow_trace=trace,
            workflow_events=self._events(state, trace, started, status, generated.fallback_reason),
        )
        return {"result": result, "trace": trace}

    @staticmethod
    def _events(
        state: DiagnosisGraphState, trace: tuple[str, ...], started: float, final_status: str, reason: str | None = None
    ) -> tuple[WorkflowEvent, ...]:
        return (*state.get("events", ()), WorkflowEvent(node=trace[-1], status=final_status, duration_ms=(time.perf_counter() - started) * 1000, input_count=1, output_count=1, reason=reason))
