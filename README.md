# Cordite

Cordite is a utility script for quickly bootstrapping a React project with optional Tailwind CSS, Lucide React icons, and GitHub Pages deployment configuration.

# Fuse

`fuse.py` is a helper script for quickly setting up a new [Vite](https://vitejs.dev/) React project.
It initializes the project, removes the template files, and can optionally
add Tailwind CSS, [Lucide](https://lucide.dev/) icons, and GitHub Pages deployment support.

## Prerequisites

- [Node.js](https://nodejs.org/) and `npm` must be installed and available on your `PATH`.
- Python 3 (the script is run with `python3`).

## Usage

Run the script with the desired project name:

```bash
python3 fuse.py my-app
```

Common optional flags:

- `--tailwind` &ndash; install Tailwind CSS and configure it in `vite.config.js`.
- `--lucide` &ndash; install `lucide-react`.
- `--deploy` &ndash; configure the project for deployment to GitHub Pages.

Example combining all options:

```bash
python3 fuse.py my-app --tailwind --lucide --deploy
```

After the script completes you can change into the new directory and start developing:

```bash
cd my-app
npm run dev
```
=======

## License

This project is licensed under the [MIT License](LICENSE).

