"""The v0.3 LangGraph diagnosis workflow with evidence-bound answer generation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from industrialops.diagnosis.context import EquipmentContextResolver, ResolvedEquipmentContext
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.evidence import EvidenceGapDetector
from industrialops.diagnosis.faults import FaultDiagnosisService
from industrialops.diagnosis.intent import IntentRoute, IntentRouter
from industrialops.diagnosis.safety import SafetyDecision, SafetyPolicyGate
from industrialops.diagnosis.schemas import Citation, DiagnosisRequest, DiagnosisResult
from industrialops.knowledge.pack_loader import StructuredEvidence


EvidenceRetriever = Callable[[DiagnosisRequest, ResolvedEquipmentContext, IntentRoute], tuple[StructuredEvidence, ...]]


class DiagnosisGraphState(TypedDict, total=False):
    request_id: str
    request: dict[str, object]
    trace: tuple[str, ...]
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
        state = self._graph.invoke({"request": payload, "request_id": request_id, "trace": ()})
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

    @staticmethod
    def _request(state: DiagnosisGraphState) -> DiagnosisRequest:
        return DiagnosisRequest.model_validate(state["request"])

    def _intent_router(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        request = self._request(state)
        return {"route": self._router.route(request), "trace": self._trace(state, "intent_router")}

    def _equipment_context_resolver(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        return {"context": self._resolver.resolve(self._request(state)), "trace": self._trace(state, "equipment_context_resolver")}

    def _evidence_retriever(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        request = self._request(state)
        evidence = self._retrieve(request, state["context"], state["route"])
        return {"retrieved_evidence": evidence, "trace": self._trace(state, "evidence_retriever")}

    def _compatibility_validator(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        context = state["context"]
        evidence = tuple(item for item in state.get("retrieved_evidence", ()) if item.pack_id == context.pack_id)
        return {"compatible_evidence": evidence, "trace": self._trace(state, "compatibility_validator")}

    def _fault_diagnosis_service(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        return {"extraction": self._fault_service.extract(state.get("compatible_evidence", ())), "trace": self._trace(state, "fault_diagnosis_service")}

    def _safety_policy_gate(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        request = self._request(state)
        context = state.get("context")
        if context is None:
            context = ResolvedEquipmentContext("pack_unknown", request.pack_id, None, None, None, None, None, "PACK_UNKNOWN")
        return {
            "safety": self._safety_gate.evaluate(request, intent=state["route"].intent, context=context),
            "trace": self._trace(state, "safety_policy_gate"),
        }

    def _evidence_gap_detector(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
        decision = self._gap_detector.evaluate(state["route"].intent, state.get("compatible_evidence", ()))
        return {"evidence_decision": decision, "trace": self._trace(state, "evidence_gap_detector")}

    def _answer_composer(self, state: DiagnosisGraphState) -> DiagnosisGraphState:
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
            )
            return {"result": result, "trace": trace}
        if route.intent == "work_order_draft":
            result = DiagnosisResult(
                request_id=request_id, status="needs_information", intent=route.intent,
                uncertainties=("工单草稿与人工审批属于 v0.4，当前版本未开放。",),
                generation={"provider": "policy_gate", "fallback_used": False}, workflow_trace=trace,
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
        )
        return {"result": result, "trace": trace}
