from industrialops.evaluation.v07.deepseek_ragas import parse_structured_response

class Schema:
    @classmethod
    def model_validate_json(cls, content):
        return {"validated": content}

def test_parses_deepseek_json_with_the_ragas_schema():
    assert parse_structured_response(content='{"ok":true}', response_model=Schema) == {"validated": '{"ok":true}'}
