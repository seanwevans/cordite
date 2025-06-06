#!/usr/bin/env python3

"""fuse - jump start a react project"""

import argparse
import json
import os
import logging
import re
from pathlib import Path
import subprocess
import shlex
import sys

PROG = Path(__file__).stem
VERSION = "1.2.0"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def parse_args(args):
    """parse command line arguments"""

    argp = argparse.ArgumentParser(
        prog=PROG,
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False,
    )

    argp.add_argument(
        "project_name",
        help="The name of the react project you want to jump start",
    )

    argp.add_argument(
        "-t", "--tailwind", action="store_true", help="Install Tailwind CSS"
    )

    argp.add_argument(
        "-l", "--lucide", action="store_true", help="Install Lucide React"
    )

    argp.add_argument(
        "-d",
        "--deploy",
        action="store_true",
        help="Configure GitHub Pages deployment",
    )

    argp.add_argument(
        "--version",
        action="version",
        version=f"{PROG} v{VERSION}",
    )

    argp.add_argument(
        "--help",
        action="help",
        help="show this help message and exit",
    )

    return argp.parse_args(args)


def initialize_logs(
    params=None,
    log_file=None,
    stream_level=logging.DEBUG,
    file_level=logging.DEBUG,
):
    """initializes logs"""

    # Clear existing handlers to avoid duplicate logs when reinitializing
    logger.handlers.clear()

    log_format = logging.Formatter(
        "%(asctime)-23s %(module)s.%(funcName)s %(levelname)-8s %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)
    stream_handler.setLevel(stream_level)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="UTF-8")
        file_handler.setFormatter(log_format)
        file_handler.setLevel(file_level)
        logger.addHandler(file_handler)

    logger.info("🍍 %s (v%s)", Path(__file__).resolve(), VERSION)

    if params:
        logger.debug("Parameters:")
        for param, value in vars(params).items():
            logger.debug("  %-16s%s", param, value)

    logger.debug("Logs:")
    for log_handle in logger.handlers:
        logger.debug("  %s", log_handle)


def run_command(command):
    """Run a shell command and handle errors"""
    if isinstance(command, str):
        cmd_tokens = shlex.split(command)
    else:
        cmd_tokens = list(command)
    logger.debug("🧨 %s", cmd_tokens)
    try:
        subprocess.run(cmd_tokens, shell=False, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Command '%s' failed with exit code %s", command, exc.returncode, exc_info=True
        )
        return False
    except OSError as exc:
        logger.error("Failed to execute command '%s': %s", command, exc, exc_info=True)
        return False

def stand_up(project_name, install_tailwind=False, install_lucide=False):
    """initialize npm project"""
    npm_inited = run_command(
        [
            "npm",
            "create",
            "vite@latest",
            project_name,
            "--",
            "--template",
            "react",
        ]
    )
    if not npm_inited:
        raise RuntimeError("Failed to initialize project")

    try:
        os.chdir(project_name)
    except OSError as exc:
        logger.error("Failed to change directory to %s: %s", project_name, exc, exc_info=True)
        raise

    deps_installed = run_command(["npm", "install"])
    if not deps_installed:
        raise RuntimeError("Failed to install dependencies")

    if install_tailwind:
        twcss_installed = run_command(
            ["npm", "install", "tailwindcss", "@tailwindcss/vite"]
        )
        if not twcss_installed:
            raise RuntimeError("Failed to install tailwind CSS")

    if install_lucide:
        lucide_installed = run_command(["npm", "install", "lucide-react"])
        if not lucide_installed:
            raise RuntimeError("Failed to install Lucide-React")


def remove_cruft():
    """remove the cruft"""
    files_to_remove = [
        "src/App.css",
        "README.md",
        "src/assets/react.svg",
        "public/vite.svg",
    ]
    for file_to_remove in files_to_remove:
        try:
            os.remove(file_to_remove)
        except FileNotFoundError:
            logger.debug("%s does not exist, skipping", file_to_remove)
        except OSError as exc:
            logger.warning("Failed to unlink %s: %s", file_to_remove, exc, exc_info=True)

            
def create_gitignore():
    """create a gitignore"""
    gitignore_elems = [
        "node_modules",
        "*.log",
        "dist",
        ".vit",
        "stats.html",
        ".eslintcache",
    ]
    try:
        Path(".gitignore").write_text("\n".join(gitignore_elems), encoding="UTF-8")
    except OSError as exc:
        logger.error("Failed to write .gitignore: %s", exc, exc_info=True)
        raise

def create_vite_config(install_tailwind=False):
    """create a vite configuration"""
    vite_config_elems = [
        "import { defineConfig } from 'vite'",
        "import react from '@vitejs/plugin-react'",
        "",
        "export default defineConfig({",
        "  plugins: [",
        "    react(),",
        "",
        "  ]",
        "})",
    ]

    if install_tailwind:
        try:
            Path("src/index.css").write_text(
                '@import "tailwindcss";\n', encoding="UTF-8"
            )
        except OSError as exc:
            logger.error("Failed to update src/index.css: %s", exc, exc_info=True)
            raise
        vite_config_elems[2] = "import tailwindcss from '@tailwindcss/vite'"
        vite_config_elems[6] = "    tailwindcss(),"

    try:
        Path("vite.config.js").write_text(
            "\n".join(vite_config_elems), encoding="UTF-8"
        )
    except OSError as exc:
        logger.error("Failed to write vite.config.js: %s", exc, exc_info=True)
        raise


def fix_main_jsx():
    """fix src/main.jsx"""
    main_jsx = Path("src/main.jsx")
    try:
        jsx = main_jsx.read_text(encoding="UTF-8")
        jsx = "import React from 'react';\n" + jsx
        main_jsx.write_text(jsx, encoding="UTF-8")
    except OSError as exc:
        logger.error("Failed to patch src/main.jsx: %s", exc, exc_info=True)
        raise


def fix_index_html(project_name):
    """fix index.html"""
    index_html = Path("index.html")
    try:
        html = index_html.read_text(encoding="UTF-8")
        html = re.sub(
            r"<title>Vite \+ React<\/title>",
            f"<title>{project_name}</title>",
            html,
        )
        index_html.write_text(html, encoding="UTF-8")
    except OSError as exc:
        logger.error("Failed to update index.html: %s", exc, exc_info=True)
        raise


def setup_github_pages(project_name):
    """Configure project for GitHub Pages deployment"""

    ghpages_installed = run_command(
        ["npm", "install", "gh-pages", "--save-dev"]
    )
    if not ghpages_installed:
        raise RuntimeError("Failed to install gh-pages")

    pkg_file = Path("package.json")
    if not pkg_file.exists():
        logger.error("package.json not found")
        return

    try:
        pkg_json = json.loads(pkg_file.read_text(encoding="UTF-8"))
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse package.json: %s", exc, exc_info=True)
        return

    scripts = pkg_json.get("scripts", {})
    scripts["predeploy"] = "npm run build"
    scripts["deploy"] = "gh-pages -d dist"
    pkg_json["scripts"] = scripts

    pkg_file.write_text(json.dumps(pkg_json, indent=2), encoding="UTF-8")
    logger.info("Updated package.json with predeploy and deploy scripts")

    vite_config = Path("vite.config.js")
    if vite_config.exists():
        try:
            config_text = vite_config.read_text(encoding="UTF-8")
            config_text = re.sub(
                r"(defineConfig\(\s*\{)",
                r"\1\n  base: '/{}',".format(project_name),
                config_text,
                count=1,
            )
            vite_config.write_text(config_text, encoding="UTF-8")

            msg_prefix = "Updated vite.config.js with base property for "
            message = msg_prefix + "GitHub Pages"
            logger.info(message)
        except Exception as exc:
            logger.error("Failed to update vite.config.js: %s", exc)
    else:
        warn_prefix = "vite.config.js not found; cannot set base property for "
        warn_msg = warn_prefix + "GitHub Pages"
        logger.warning(warn_msg)


def create_project(
    working_dir, project_name, install_tailwind=False, install_lucide=False
):
    """do the thang"""
    os.chdir(working_dir)

    stand_up(
        project_name=project_name,
        install_tailwind=install_tailwind,
        install_lucide=install_lucide,
    )
    remove_cruft()
    create_gitignore()
    create_vite_config(install_tailwind=install_tailwind)
    fix_main_jsx()
    fix_index_html(project_name)


def main(args):
    """script entrypoint"""

    params = parse_args(args)
    initialize_logs(params)

    orig_dir = os.getcwd()
    create_project(
        orig_dir,
        params.project_name,
        install_tailwind=params.tailwind,
        install_lucide=params.lucide,
    )
    logger.info("💥 successfully created %s", params.project_name)

    if params.deploy:
        setup_github_pages(params.project_name)
        logger.info(
            "🚀 GitHub Pages deployment configured. To deploy, run "
            "'npm run deploy' after committing your changes."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
