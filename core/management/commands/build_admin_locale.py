import array
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.locale_es import ES

HEADER = (
    "Content-Type: text/plain; charset=UTF-8\n"
    "Content-Transfer-Encoding: 8bit\n"
    "Language: es\n"
    "Plural-Forms: nplurals=2; plural=(n != 1);\n"
)


def _po_quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def write_po(path, catalog):
    lines = ['msgid ""', 'msgstr ""']
    lines += [_po_quote(line + "\n") for line in HEADER.rstrip("\n").split("\n")]
    for msgid, msgstr in catalog.items():
        lines += ["", f"msgid {_po_quote(msgid)}", f"msgstr {_po_quote(msgstr)}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mo(path, catalog):
    """Write a GNU gettext .mo file (same layout as CPython's Tools/i18n/msgfmt.py)."""
    entries = {"": HEADER, **catalog}
    keys = sorted(entries)
    ids = strs = b""
    offsets = []
    for k in keys:
        kb, vb = k.encode("utf-8"), entries[k].encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\0"
        strs += vb + b"\0"
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)
    koffsets, voffsets = [], []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    output = array.array("I", [0x950412DE, 0, len(keys), 7 * 4, 7 * 4 + len(keys) * 8, 0, 0])
    output.fromlist(koffsets + voffsets)
    path.write_bytes(output.tobytes() + ids + strs)


class Command(BaseCommand):
    help = "Build locale/es/LC_MESSAGES/django.po and .mo for the admin from core/locale_es.py"

    def handle(self, *args, **options):
        out_dir = Path(settings.BASE_DIR) / "locale" / "es" / "LC_MESSAGES"
        out_dir.mkdir(parents=True, exist_ok=True)
        write_po(out_dir / "django.po", ES)
        write_mo(out_dir / "django.mo", ES)
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(ES)} Spanish strings to {out_dir}"))
