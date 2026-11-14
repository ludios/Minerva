"""
Demos that show off Minerva, served by `minerva-site`:

- `/whiteboard/` (`minerva.demos.whiteboard`): a whiteboard that everyone
  viewing it draws on together.
- `/bluesky-stream/` (`minerva.demos.bskystream`): a live stream of public
  Bluesky posts.

Their JavaScript is in `js_minerva/demos/`, and compiled into `static/` by
`scripts/build_js.py`.  The `_dev` pages (`/whiteboard_dev/`, ...) load the
uncompiled JavaScript instead, which needs Closure Library and Coreweb.

These demos used to live in the separate DemosMinerva repository.  Its other
demo streamed public LiveJournal posts, until LiveJournal turned off its Atom
stream; the Bluesky stream demo replaces it.
"""
