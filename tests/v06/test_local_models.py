from __future__ import annotations

from industrialops.retrieval.local_models import LocalBgeM3


def test_bge_m3_caps_model_input_to_a_retrieval_safe_length() -> None:
    class Client:
        max_seq_length = 8192

    class EmbeddingModel:
        client = Client()

    LocalBgeM3._cap_sequence_length(EmbeddingModel())

    assert EmbeddingModel.client.max_seq_length == 512
