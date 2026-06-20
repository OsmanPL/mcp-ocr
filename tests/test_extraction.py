from mcp_ocr.extraction import extract_visible_key_values


def test_extracts_multiline_key_values_literally() -> None:
    raw = "LOTE\nABC123\nVENC\n20/10/2026\nFABR\n20/10/2024"

    assert extract_visible_key_values(raw) == {
        "LOTE": "ABC123",
        "VENC": "20/10/2026",
        "FABR": "20/10/2024",
    }


def test_extracts_inline_key_values_literally() -> None:
    raw = "LOTE: ABC123\nVENC: 20/10/2026\nFABR: 20/10/2024"

    assert extract_visible_key_values(raw) == {
        "LOTE": "ABC123",
        "VENC": "20/10/2026",
        "FABR": "20/10/2024",
    }


def test_keeps_key_with_empty_value_when_no_value_is_detected() -> None:
    raw = "LOTE\nVENC\n20/10/2026"

    assert extract_visible_key_values(raw) == {
        "LOTE": "",
        "VENC": "20/10/2026",
    }


def test_does_not_normalize_visible_text() -> None:
    raw = "FáBR.\n20-Oct-2024\nbatch_no: AbC-123"

    assert extract_visible_key_values(raw) == {
        "FáBR.": "20-Oct-2024",
        "batch_no": "AbC-123",
    }
