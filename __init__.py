import re
from bs4 import BeautifulSoup
from aqt import gui_hooks
from anki import hooks
from pprint import pprint

def prepare(html, card, context):

    pattern = r'([\u0F00-\u0FFF]+)'

    replacement = r'<span class="tibetan">\1</span>'
    new_html = re.sub(pattern, replacement, html)

    return new_html

def displaymatch(match):
    if match is None:
        return None
    return '<Match: %r, groups=%r>' % (match.group(), match.groups())

def prepare2(html, card, context):

    pattern = r"\"[^\"]+\"|([\u0F00-\u0FFF]+)"
    def replace_func(match):
        print("match="+displaymatch(match))
        if match.group(1) is None:
            return match.group()
        return r'<span class="tibetan">'+match.group()+'</span>'

    new_html = re.sub(pattern, replace_func, html)
    return new_html

gui_hooks.card_will_show.append(prepare2)

from io import StringIO
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

import csv

from anki.exporting import Exporter
from anki.hooks import addHook
from anki.lang import _
from anki.utils import  ids2str, splitFields
from anki.collection import Collection
from anki.collection import DeckIdLimit, NoteIdsLimit
from io import BufferedWriter

from aqt.import_export.exporting import Exporter as ExporterGui

class CSVNoteExporterGui(ExporterGui):

    extension = "csv"
    show_deck_list = True
    show_include_html = False
    show_include_tags = False
    show_include_deck = False
    show_include_notetype = False
    show_include_guid = False

    @staticmethod
    def name() -> str:
        return "Export Notes to CSV"

    def export(self, mw, options) -> None:
        options = gui_hooks.exporter_will_export(options, self)

        def on_success(count: int) -> None:
            gui_hooks.exporter_did_export(options, self)
            tooltip(tr.exporting_note_exported(count=count), parent=mw)

        print("options="+str(options))
        print("options.limit="+str(options.limit))

        if (type(options.limit) is DeckIdLimit):
            deckId = str(options.limit.deck_id)
            print("deckId="+deckId)
            deck = mw.col.decks.get(deckId)
            print(str(deck))
            deckName = deck['name']
            notes = mw.col.find_notes("deck:"+deckName)
        else:
            noteIds = options.limit.note_ids
            print("noteIds="+str(noteIds))
            notes = noteIds

        print("notes="+str(notes))

        def clean(str):
            if str:
                return strip_tags(str).replace('&nbsp;', '').replace('\n', ' ').strip()
            else:
                return str

        def getIf(obj, key) -> str:
            if key in obj:
                return obj[key]
            else:
                return ""

        with open(options.out_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for note in notes:
                note_obj = mw.col.get_note(note)

                front = False
                if 'Front' in note_obj:
                    front = clean(note_obj['Front'])
                elif 'Tibetan' in note_obj:
                    front = clean(note_obj['Tibetan'])
                elif 'བོད་སྐད།' in note_obj:
                    front = clean(note_obj['བོད་སྐད།'])

                if (front):
                    frontAlt = False
                    if 'Front_alt' in note_obj:
                        frontAlt = clean(note_obj['Front_alt'])

                    back = False
                    if 'Front' in note_obj:
                        back = note_obj['Back']
                    elif 'English' in note_obj:
                        back = note_obj['English']
                    else:
                        back = ""
                    back = clean(back)

                    partOfSpeech = clean(getIf(note_obj, 'Part of Speech'))

                    if frontAlt:
                        back = " // ".join([back, frontAlt])
                    print(str([front, back, partOfSpeech]))
                    #pprint(vars(note_obj))
                    writer.writerow([front, back, partOfSpeech])

def update_exporters_list_gui(exps):
    exps.append(CSVNoteExporterGui)

gui_hooks.exporters_list_did_initialize.append(update_exporters_list_gui)
