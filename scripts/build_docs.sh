#!/bin/sh

set -e

cd "$(dirname "$0")/.."

for i in docs/*.rst
	do uv run --with docutils rst2html \
		--link-stylesheet --file-insertion-enabled --tab-width=6 \
		--stylesheet-path=style.css --report=3 $i \
		| sed "s/<p><!-- expect dupe --><p /<p /g" \
		| sed "s/<\/p><!-- expect dupe --><\/p>/<\/p>/g" \
		| tr "\r\n" "\n" \
		> docs/`basename $i .rst`.html
done

## rst2html.py --tab-width=6 --stylesheet-path=docs/style.css --warnings=_with_warnings_README.log README > _with_warnings_README.html 
