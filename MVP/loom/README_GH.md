# Week Trial Report (GitHub-friendly)

> This README is optimized for GitHub rendering. GitHub Markdown does **not** play videos inline in README;
> instead, use **clickable thumbnails** that open the `.mp4` file, or host an HTML page via **GitHub Pages**.

## Demo Videos (click the thumbnail)
[![Batch Insert Demo](demos/Week_Trail_Demo_01_BatchInsert.png)](demos/Week_Trail_Demo_01_BatchInsert.mp4)
[![From Page Edit Demo](demos/Week_Trail_Demo_05_FromPage_Edit.png)](demos/Week_Trail_Demo_05_FromPage_Edit.mp4)

> Generate thumbnails with ffmpeg:
>
> ```bash
> ffmpeg -ss 00:00:02 -i demos/Week_Trail_Demo_01_BatchInsert.mp4 -frames:v 1 demos/Week_Trail_Demo_01_BatchInsert.png
> ffmpeg -ss 00:00:02 -i demos/Week_Trail_Demo_05_FromPage_Edit.mp4 -frames:v 1 demos/Week_Trail_Demo_05_FromPage_Edit.png
> ```
>
> Recommended video encoding: H.264 + AAC (`.mp4`).

## Repo structure
```
/ (repo root)
├─ README.md
├─ docs/                  # for GitHub Pages (optional)
│   └─ index.html
└─ demos/                 # videos + thumbnails
    ├─ Week_Trail_Demo_01_BatchInsert.mp4
    ├─ Week_Trail_Demo_01_BatchInsert.png
    ├─ Week_Trail_Demo_05_FromPage_Edit.mp4
    └─ Week_Trail_Demo_05_FromPage_Edit.png
```

## Use GitHub Pages (for inline playback)
1. Put your HTML report into `docs/index.html` (template below).
2. Go to **Settings → Pages → Build and deployment → Source = Deploy from a branch → Branch = main /docs**.
3. Open the published URL; the `<video>` players will work inline.

---

### Minimal `docs/index.html` (use this with GitHub Pages)
See `docs/index.html` in this repo for a ready-to-use template.
