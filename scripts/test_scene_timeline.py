"""No hardware or real waits: protect event annotation and session provenance."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scene_timeline import annotate, completion_label, drive_timeline, resolve_session


class SceneTimelineTests(unittest.TestCase):
    def run_clock(self, event, keys=None, stop_at=None):
        elapsed = [0.0]
        rows = []
        keys = dict(keys or {})

        def advance(seconds):
            elapsed[0] = round(elapsed[0] + seconds, 2)

        result = drive_timeline(
            event, lambda *row: rows.append(row), lambda message: None,
            lambda: keys.pop(elapsed[0], None), clock=lambda: elapsed[0],
            sleep=advance, active=lambda: stop_at is None or elapsed[0] < stop_at)
        return result, rows

    def test_plan_does_not_invent_completion(self):
        result, rows = self.run_clock("removal")
        self.assertEqual(result, "timeline_completed")
        self.assertEqual([r[2] for r in rows], [0, 20, 25, 60, 65, 80])
        self.assertTrue(all(r[0] == "planned_cue" for r in rows))

    def test_actual_keys_keep_their_times(self):
        result, rows = self.run_clock("move", {27.0: " ", 66.0: " "})
        self.assertEqual(result, "timeline_completed")
        self.assertEqual([(r[1], r[3]) for r in rows if r[0] == "operator_key"],
                         [("action_complete", 27.0), ("restore_complete", 66.0)])

    def test_abort_does_not_emit_success(self):
        result, rows = self.run_clock("occlusion", {22.0: "q"})
        self.assertEqual(result, "aborted")
        self.assertNotIn("end", [r[1] for r in rows])

    def test_capture_ending_aborts_timeline(self):
        result, rows = self.run_clock("static", stop_at=30)
        self.assertEqual(result, "aborted")
        self.assertEqual(rows[-1][0], "capture_stopped")

    def test_early_or_static_keys_are_not_event_truth(self):
        self.assertEqual(completion_label("move", 10), "unexpected_completion_key")
        self.assertEqual(completion_label("static", 30), "unexpected_completion_key")

    def test_interrupt_withdraws_export_declaration_and_preserves_abort(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder)
            with patch("scene_timeline.time.sleep"), patch("builtins.print"), \
                    patch("scene_timeline.drive_timeline", side_effect=KeyboardInterrupt):
                result = annotate(session, {"sensor": "camera"}, "move")
            self.assertEqual(result, 2)
            note = json.loads((session / "session-note.json").read_text())
            self.assertFalse(note["camera_fixed_declared_by_operator"])
            self.assertIn("operator_abort", (session / "events.csv").read_text())

    def test_timeline_completion_does_not_verify_physical_event(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder)
            with patch("scene_timeline.time.sleep"), patch("builtins.print"), \
                    patch("scene_timeline.drive_timeline", return_value="timeline_completed"):
                result = annotate(session, {"sensor": "camera"}, "removal")
            self.assertEqual(result, 0)
            record = json.loads((session / "trial-scene.json").read_text())
            self.assertFalse(record["required_completion_keys_present"])
            self.assertFalse(record["independent_event_verification"])

    def test_mouse_trial_has_distinct_provenance_without_measured_displacement(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder)
            with patch("scene_timeline.time.sleep"), patch("builtins.print"), \
                    patch("scene_timeline.drive_timeline", return_value="timeline_completed") as driver:
                annotate(session, {"sensor": "camera"}, "move", target="mouse")
            record = json.loads((session / "trial-scene.json").read_text())
            note = json.loads((session / "session-note.json").read_text())
            self.assertEqual(record["target"], "M01")
            self.assertEqual(note["target"], "M01")
            self.assertEqual(record["movement_marks"], ["M_A", "M_B"])
            self.assertEqual(driver.call_args.kwargs["target"], "mouse")
            self.assertIsNone(record["measured_move_m"])
            self.assertFalse(record["independent_event_verification"])

    def test_unsupported_mouse_event_creates_no_annotations(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Path(folder)
            with self.assertRaises(ValueError):
                annotate(session, {"sensor": "camera"}, "removal", target="mouse")
            self.assertEqual(list(session.iterdir()), [])

    def test_completed_unrecorded_and_existing_sessions_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            session = root / "data/live-camera-example"
            session.mkdir(parents=True)
            config = dict(windows_session=str(session), sensor="camera", algorithm="sensor",
                          session_type="stationary", record=True)
            config_file = session / "config.json"
            config_file.write_text(json.dumps(config))
            (session / "raw.db3").touch()
            self.assertEqual(resolve_session(root, latest="camera")[0], session.resolve())
            (session / "capture.json").touch()
            with self.assertRaisesRegex(ValueError, "already ended"):
                resolve_session(root, explicit=session)
            (session / "capture.json").unlink()
            (session / "session-note.json").write_text('{"old": true}')
            with self.assertRaisesRegex(ValueError, "already exists"):
                resolve_session(root, explicit=session)
            self.assertEqual((session / "session-note.json").read_text(), '{"old": true}')
            (session / "session-note.json").unlink()
            config["record"] = False
            config_file.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "-Record"):
                resolve_session(root, explicit=session)


if __name__ == "__main__":
    unittest.main()
