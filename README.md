# Book Poster

A Codex Skill for designing book posters from book research, real poster references, and iterative visual decisions.
The workflow connects a book's argument or story to composition, typography, source materials, production, and refinement.

This package contains 17 reviewed starter images and 300 minimal catalog records.
Catalog-only records have source-page links, no bundled image and no promise of download/reuse permission.
This is a historical starter, not the full private collection or a claim of balanced style coverage.

## Quick start

Open `library/gallery.html` to browse actual bundled references. `catalog.html` lists source-only entries too.
Copy `skills/book-poster` into your Codex skills directory; configure its `library.local.json` with the absolute path to this library.
The example relative path works when the Skill stays in this repository. You may point to your own library.
Python 3.10+ is required for the tools; Pillow is optional for full image decoding.

Ask Codex to use book-poster, name a book, and describe your audience. Open exploration shows at least four real references before choosing a direction.
The Skill requires the host's own research and image tools; it does not include a model service or API keys. PhotoCraft is optional for editable native assets.

```sh
python -X utf8 library/tools/library.py validate --root library
python -X utf8 library/tools/library.py search --root library --query "linework" --diverse --limit 4
python -X utf8 library/tools/release.py audit --root library
```

## License

Original code, Skill instructions, documentation, and original annotations are licensed under [MIT](LICENSE).
Reference images retain their individual rights; see [license scope](LICENSE-SCOPE.md) and [image credits](CREDITS.md).
The initial 17 bundled images carry the museum's public-domain/CC0 designation. Links to other works do not grant reuse permission.

See `library/PUBLIC-RELEASE.md` for auditing and exporting a reviewed library. Local configurations, private reports, and generated user posters are excluded.
