"""Include the same dashboard in the installable wheel and source checkout."""
from pathlib import Path
from shutil import copy2
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithDashboard(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        target = Path(self.build_lib) / "glinx_discovery" / "web"
        target.mkdir(parents=True, exist_ok=True)
        for name in ("index.html", "styles.css", "app.js", "model.js", "demo.json", "favicon.svg"):
            copy2(root / "dist" / name, target / name)


setup(cmdclass={"build_py": BuildWithDashboard})
