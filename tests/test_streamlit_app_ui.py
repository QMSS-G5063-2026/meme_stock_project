from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app" / "streamlit_app.py"


def run_app(event_window: str | None = None) -> AppTest:
    app = AppTest.from_file(str(APP_PATH))
    app.run(timeout=30)
    if event_window is not None:
        app.sidebar.selectbox[0].set_value(event_window)
        app.run(timeout=30)
    return app


def selectbox_values(app: AppTest) -> dict[str, str]:
    return {box.label: box.value for box in app.selectbox}


class StreamlitDashboardUiTests(unittest.TestCase):
    def test_has_methods_tab_for_demo_path(self) -> None:
        app = run_app()
        self.assertIn("Methods", [tab.label for tab in app.tabs])

    def test_mobile_css_has_overflow_guards(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 640px)", source)
        self.assertIn("overflow-x: auto", source)
        self.assertIn("overflow-wrap: anywhere", source)

    def test_later_event_window_explains_missing_reddit_coverage(self) -> None:
        app = run_app("AMC June 2021 run")
        warning_text = " ".join(str(w.value) for w in app.warning)
        markdown_text = " ".join(str(m.value) for m in app.markdown)

        self.assertIn("Reddit archive covers", warning_text + " " + markdown_text)
        self.assertNotIn("No Reddit attention table is available for the selected filters.", warning_text)

        values = selectbox_values(app)
        self.assertEqual(values["Map window"], "AMC June 2021 run")
        self.assertEqual(values["Network window"], "Full range")

    def test_january_map_defaults_to_gamestop(self) -> None:
        app = run_app("January 2021 squeeze")
        values = selectbox_values(app)
        self.assertEqual(values["Search term"], "GameStop")

    def test_event_annotations_use_text_labels_not_numbered_markers(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn('text=wrap_event_label(event["event"])', source)
        self.assertNotIn('text=f"#{idx + 1}"', source)
        self.assertNotIn("Numbered event markers", source)


if __name__ == "__main__":
    unittest.main()
