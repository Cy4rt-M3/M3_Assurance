"""Controls importer entry point."""

from apps.controls_importer.importer import run_import


if __name__ == "__main__":
    count = run_import()
    print(f"[controls-importer] Successfully processed {count} controls")
