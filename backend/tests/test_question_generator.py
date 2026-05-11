from app.tools.question_generator import _parse_questions_json


def test_parse_questions_json_raw():
    raw = '{"questions": [{"id": 1, "type": "technical", "question": "One?"}]}'
    out = _parse_questions_json(raw)
    assert out is not None
    assert len(out["questions"]) == 1
    assert out["questions"][0]["question"] == "One?"


def test_parse_questions_json_markdown_fence():
    raw = """Here you go:
```json
{"questions": [{"id": 1, "type": "behavioral", "question": "Tell me."}]}
```
"""
    out = _parse_questions_json(raw)
    assert out is not None
    assert out["questions"][0]["type"] == "behavioral"


def test_parse_questions_json_braces_in_prose():
    raw = 'Prefix text {"questions": [{"id": 1, "type": "technical", "question": "Q"}]} trailing'
    out = _parse_questions_json(raw)
    assert out is not None
    assert out["questions"][0]["question"] == "Q"
