"""Pure unittest tests: no server, Docker, database, or Streamlit needed."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import client


class FakeResponse:
    def __init__(self, body=None, status=200):
        self.body, self.status_code = body, status

    def json(self):
        return self.body


def valid_vision():
    return {"probabilities": {label: 0.2 for label in client.ALL_LABELS},
            "metadata_removed": True, "mode": "real", "latency_ms": 50}


def valid_llm():
    return {"soap": {k: f"test {k}" for k in "SOAP"}, "priority": "ROUTINE",
            "mode": "real", "latency_ms": 20}


class ContractTest(unittest.TestCase):
    def test_vision_accepts_contract(self):
        result = client.validate_vision(valid_vision())
        self.assertEqual(len(result["probabilities"]), 6)

    def test_vision_missing_label(self):
        data = valid_vision()
        del data["probabilities"]["No Finding"]
        with self.assertRaises(client.ServiceError):
            client.validate_vision(data)

    def test_vision_outside_zero_one(self):
        data = valid_vision()
        data["probabilities"]["Pneumonia"] = 1.2
        with self.assertRaises(client.ServiceError):
            client.validate_vision(data)

    def test_reject_nan(self):
        data = valid_vision()
        data["probabilities"]["Pneumonia"] = float("nan")
        with self.assertRaises(client.ServiceError):
            client.validate_vision(data)

    def test_soap_validates_all_four_parts(self):
        self.assertEqual(client.validate_soap(valid_llm())["priority"], "ROUTINE")
        data = valid_llm()
        del data["soap"]["P"]
        with self.assertRaises(client.ServiceError):
            client.validate_soap(data)

    def test_reject_bad_priority(self):
        data = valid_llm()
        data["priority"] = "CRITICAL"
        with self.assertRaises(client.ServiceError):
            client.validate_soap(data)

    def test_isolated_mock_is_deterministic(self):
        first = client.ui_mock_vision(b"synthetic test fixture")
        second = client.ui_mock_vision(b"synthetic test fixture")
        self.assertEqual(first, second)
        self.assertEqual(first["mode"], "ui-demo-mock")
        self.assertFalse(first["metadata_removed"])

    def test_isolated_pipeline_needs_no_http(self):
        with patch("client.requests.request") as call:
            result = client.analyze("synthetic example", image_name="test.png",
                                    image_bytes=b"fake image bytes", ui_mock=True)
            self.assertEqual(result["llm"]["mode"], "ui-demo-mock")
            self.assertEqual(result["source"], "ui_mock")
            call.assert_not_called()

    def test_live_flow_calls_p2_then_p3(self):
        with patch("client.requests.request", side_effect=[FakeResponse(valid_vision()), FakeResponse(valid_llm())]) as call:
            result = client.analyze("test symptoms", image_name="test.png", image_bytes=b"data",
                                    vision_url="http://vision:8000", llm_url="http://llm:8000")
            self.assertEqual(call.call_count, 2)
            self.assertEqual(call.call_args_list[0].args[:2], ("POST", "http://vision:8000/predict"))
            self.assertEqual(call.call_args_list[1].args[:2], ("POST", "http://llm:8000/soap"))
            self.assertEqual(result["source"], "vision_api")

    def test_manual_skips_vision(self):
        with patch("client.requests.request", return_value=FakeResponse(valid_llm())) as call:
            result = client.analyze("synthetic", manual_findings=valid_vision()["probabilities"],
                                    llm_url="http://llm:8000")
            self.assertEqual(call.call_count, 1)
            self.assertEqual(result["vision"]["mode"], "manual")

    def test_http_error_is_explicit(self):
        with patch("client.requests.request", return_value=FakeResponse({"detail": "secret request"}, 503)):
            with self.assertRaisesRegex(client.ServiceError, "HTTP 503") as raised:
                client.predict_image("http://vision:8000", "test.png", b"data", "image/png")
            self.assertNotIn("secret request", str(raised.exception))

    def test_large_upload_rejected_before_http(self):
        with patch("client.requests.request") as call:
            with patch.object(client, "MAX_UPLOAD_BYTES", 3):
                with self.assertRaises(client.ServiceError):
                    client.predict_image("http://vision:8000", "test.png", b"1234", "image/png")
            call.assert_not_called()

    def test_llm_fallback_mode_is_visible(self):
        data = valid_llm()
        data["mode"] = "mock"
        self.assertEqual(client.validate_soap(data)["mode"], "mock")

    def test_blank_symptoms_rejected(self):
        with self.assertRaises(client.ServiceError):
            client.analyze("   ", image_bytes=b"some")


if __name__ == "__main__":
    unittest.main()
