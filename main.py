# -*- coding: utf-8 -*-
import os
os.environ['KIVY_NO_CONSOLELOG'] = '1'

from kivy.config import Config
Config.set('kivy', 'window_icon', '')
Config.set('kivy', 'log_level', 'error')

import sqlite3
import threading
import requests
import re
from bs4 import BeautifulSoup

from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp

DB_NAME = 'justiz_voll.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cache
                 (kuerzel TEXT, paragraph TEXT, inhalt TEXT, PRIMARY KEY (kuerzel, paragraph))''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks
                 (kuerzel TEXT, paragraph TEXT, PRIMARY KEY (kuerzel, paragraph))''')
    c.execute('''CREATE TABLE IF NOT EXISTS gesetze_liste
                 (kuerzel TEXT PRIMARY KEY, name TEXT, kategorie TEXT)''')
    
    c.execute('SELECT COUNT(*) FROM gesetze_liste')
    if c.fetchone()[0] == 0:
        gesetze = [
            ('GG', 'Grundgesetz', 'Deutschland'),
            ('BGB', 'Bürgerliches Gesetzbuch', 'Deutschland'),
            ('StGB', 'Strafgesetzbuch', 'Deutschland'),
            ('HGB', 'Handelsgesetzbuch', 'Deutschland'),
            ('ZPO', 'Zivilprozessordnung', 'Deutschland'),
            ('StPO', 'Strafprozessordnung', 'Deutschland'),
            ('VwGO', 'Verwaltungsgerichtsordnung', 'Deutschland'),
            ('VwVfG', 'Verwaltungsverfahrensgesetz', 'Deutschland'),
            ('AO', 'Abgabenordnung', 'Deutschland'),
            ('EStG', 'Einkommensteuergesetz', 'Deutschland'),
            ('UStG', 'Umsatzsteuergesetz', 'Deutschland'),
            ('GewStG', 'Gewerbesteuergesetz', 'Deutschland'),
            ('KStG', 'Körperschaftsteuergesetz', 'Deutschland'),
            ('ArbGG', 'Arbeitsgerichtsgesetz', 'Deutschland'),
            ('BetrVG', 'Betriebsverfassungsgesetz', 'Deutschland'),
            ('TzBfG', 'Teilzeit- und Befristungsgesetz', 'Deutschland'),
            ('KSchG', 'Kündigungsschutzgesetz', 'Deutschland'),
            ('BUrlG', 'Bundesurlaubsgesetz', 'Deutschland'),
            ('SGB_1', 'Sozialgesetzbuch I', 'Deutschland'),
            ('SGB_2', 'Sozialgesetzbuch II', 'Deutschland'),
            ('SGB_3', 'Sozialgesetzbuch III', 'Deutschland'),
            ('SGB_4', 'Sozialgesetzbuch IV', 'Deutschland'),
            ('SGB_5', 'Sozialgesetzbuch V', 'Deutschland'),
            ('SGB_6', 'Sozialgesetzbuch VI', 'Deutschland'),
            ('SGB_7', 'Sozialgesetzbuch VII', 'Deutschland'),
            ('SGB_8', 'Sozialgesetzbuch VIII', 'Deutschland'),
            ('SGB_9', 'Sozialgesetzbuch IX', 'Deutschland'),
            ('SGB_10', 'Sozialgesetzbuch X', 'Deutschland'),
            ('SGB_11', 'Sozialgesetzbuch XI', 'Deutschland'),
            ('SGB_12', 'Sozialgesetzbuch XII', 'Deutschland'),
            ('GmbHG', 'GmbH-Gesetz', 'Deutschland'),
            ('AktG', 'Aktiengesetz', 'Deutschland'),
            ('GenG', 'Genossenschaftsgesetz', 'Deutschland'),
            ('UmwG', 'Umwandlungsgesetz', 'Deutschland'),
            ('InsO', 'Insolvenzordnung', 'Deutschland'),
            ('PatG', 'Patentgesetz', 'Deutschland'),
            ('MarkenG', 'Markengesetz', 'Deutschland'),
            ('UrhG', 'Urheberrechtsgesetz', 'Deutschland'),
            ('BauGB', 'Baugesetzbuch', 'Deutschland'),
            ('BImSchG', 'Bundes-Immissionsschutzgesetz', 'Deutschland'),
            ('DSGVO', 'Datenschutz-Grundverordnung', 'EU'),
            ('AEUV', 'Vertrag über die Arbeitsweise der EU', 'EU'),
            ('EUV', 'Vertrag über die Europäische Union', 'EU'),
        ]
        c.executemany('INSERT INTO gesetze_liste VALUES (?, ?, ?)', gesetze)
    conn.commit()
    conn.close()

def get_all_gesetze():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT kuerzel, name, kategorie FROM gesetze_liste ORDER BY kategorie, name')
    gesetze = c.fetchall()
    conn.close()
    return gesetze

def search_gesetze(query):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT kuerzel, name, kategorie FROM gesetze_liste 
                 WHERE kuerzel LIKE ? OR name LIKE ? 
                 ORDER BY kategorie, name''', 
              (f'%{query}%', f'%{query}%'))
    gesetze = c.fetchall()
    conn.close()
    return gesetze

class JustizWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        self.current_gesetz = ''
        self.current_para = ''
        self.all_gesetze = get_all_gesetze()
        self.gesetz_dict = {f"{k} - {n}": k for k, n, _ in self.all_gesetze}
        
        self.gesetz_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(50), spacing=dp(5))
        self.spinner = Spinner(text='BGB - Bürgerliches Gesetzbuch', values=list(self.gesetz_dict.keys()), size_hint=(0.8, 1), font_size='12sp')
        self.gesetz_box.add_widget(self.spinner)
        btn_suche_gesetz = Button(text='🔍', size_hint=(0.2, 1), font_size='16sp')
        btn_suche_gesetz.bind(on_press=self.show_gesetz_search)
        self.gesetz_box.add_widget(btn_suche_gesetz)
        self.add_widget(self.gesetz_box)
        
        self.para_input = TextInput(hint_text='Paragraph (z.B. 433)', multiline=False, size_hint=(1, None), height=dp(50), font_size='14sp')
        self.add_widget(self.para_input)
        
        btn_search = Button(text='Suchen', size_hint=(1, None), height=dp(50), font_size='16sp')
        btn_search.bind(on_press=self.search)
        self.add_widget(btn_search)
        
        self.scroll = ScrollView(size_hint=(1, 1))
        self.result_label = Label(text='Ergebnis erscheint hier...', size_hint=(1, None), text_size=(Window.width - dp(20), None), halign='left', valign='top', padding=(dp(10), dp(10)), font_size='14sp')
        self.result_label.bind(texture_size=self._update_height)
        self.scroll.add_widget(self.result_label)
        self.add_widget(self.scroll)
        
        btn_box = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(5))
        self.bookmark_btn = Button(text='Merken', font_size='14sp')
        self.bookmark_btn.bind(on_press=self.toggle_bookmark)
        btn_box.add_widget(self.bookmark_btn)
        btn_list = Button(text='Lesezeichen', font_size='14sp')
        btn_list.bind(on_press=self.show_bookmarks)
        btn_box.add_widget(btn_list)
        btn_clear = Button(text='Cache', font_size='14sp')
        btn_clear.bind(on_press=self.clear_cache)
        btn_box.add_widget(btn_clear)
        self.add_widget(btn_box)
        
        self._update_text_size()
        Window.bind(on_resize=self._on_window_resize)
    
    def _on_window_resize(self, window, width, height):
        self._update_text_size()
    
    def _update_text_size(self):
        self.result_label.text_size = (Window.width - dp(20), None)
    
    def _update_height(self, instance, size):
        instance.height = size[1]
    
    def show_gesetz_search(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        search_input = TextInput(hint_text='Gesetz suchen', multiline=False, size_hint_y=None, height=dp(45), font_size='14sp')
        content.add_widget(search_input)
        scroll = ScrollView()
        self.search_result_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        self.search_result_box.bind(minimum_height=self.search_result_box.setter('height'))
        scroll.add_widget(self.search_result_box)
        content.add_widget(scroll)
        btn_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        btn_search = Button(text='Suchen', font_size='14sp')
        btn_search.bind(on_press=lambda x: self.do_gesetz_search(search_input.text))
        btn_box.add_widget(btn_search)
        btn_close = Button(text='Schließen', font_size='14sp')
        btn_box.add_widget(btn_close)
        content.add_widget(btn_box)
        self.gesetz_popup = Popup(title='Gesetz auswählen', content=content, size_hint=(0.95, 0.8), title_size='16sp')
        btn_close.bind(on_press=self.gesetz_popup.dismiss)
        self.do_gesetz_search('')
        self.gesetz_popup.open()
    
    def do_gesetz_search(self, query):
        self.search_result_box.clear_widgets()
        results = search_gesetze(query.strip()) if query.strip() else self.all_gesetze
        kategorien = {}
        for k, n, kat in results:
            if kat not in kategorien:
                kategorien[kat] = []
            kategorien[kat].append((k, n))
        for kat in ['Deutschland', 'EU']:
            if kat in kategorien:
                header = Label(text=f'[b]{kat}[/b]', markup=True, size_hint_y=None, height=dp(35), font_size='15sp', color=(0.2, 0.5, 0.8, 1) if kat == 'Deutschland' else (0.2, 0.3, 0.8, 1))
                self.search_result_box.add_widget(header)
                for kuerzel, name in sorted(kategorien[kat], key=lambda x: x[1]):
                    btn = Button(text=f'{kuerzel} - {name}', size_hint_y=None, height=dp(40), font_size='12sp', halign='left')
                    btn.bind(on_press=lambda x, k=kuerzel, n=name: self.select_gesetz(k, n))
                    self.search_result_box.add_widget(btn)
    
    def select_gesetz(self, kuerzel, name):
        self.spinner.text = f'{kuerzel} - {name}'
        self.gesetz_popup.dismiss()
    
    def search(self, instance):
        gesetz_display = self.spinner.text
        gesetz = self.gesetz_dict.get(gesetz_display, gesetz_display.split(' - ')[0])
        para = self.para_input.text.strip()
        if not para:
            self.show_message('Bitte Paragraphen eingeben')
            return
        self.current_gesetz = gesetz
        self.current_para = para
        self.result_label.text = f'Lade §{para} {gesetz}...'
        self.update_bookmark_button()
        threading.Thread(target=self._fetch, args=(gesetz, para), daemon=True).start()
    
    def _fetch(self, gesetz, para):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT inhalt FROM cache WHERE kuerzel=? AND paragraph=?', (gesetz.lower(), para))
        row = c.fetchone()
        if row:
            conn.close()
            self._show_result(row[0])
            return
        para_clean = re.sub(r'[§\s]', '', para)
        url = f"https://www.gesetze-im-internet.de/{gesetz.lower()}/__{para_clean}.html"
        try:
            resp = requests.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            absaetze = [absatz.get_text(separator=' ', strip=True) for absatz in soup.find_all('div', class_='jurAbsatz') if absatz.get_text(strip=True)]
            inhalt = '\n\n'.join(absaetze) if absaetze else "Kein Text gefunden."
            c.execute('INSERT OR REPLACE INTO cache VALUES (?, ?, ?)', (gesetz.lower(), para, inhalt))
            conn.commit()
            conn.close()
            self._show_result(inhalt)
        except Exception as e:
            conn.close()
            self._show_result(f"Fehler: {str(e)}")
    
    @mainthread
    def _show_result(self, text):
        self.result_label.text = f'§{self.current_para} {self.current_gesetz}\n\n{text}'
        self._update_text_size()
    
    def toggle_bookmark(self, instance):
        if not self.current_gesetz:
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT * FROM bookmarks WHERE kuerzel=? AND paragraph=?', (self.current_gesetz.lower(), self.current_para))
        if c.fetchone():
            c.execute('DELETE FROM bookmarks WHERE kuerzel=? AND paragraph=?', (self.current_gesetz.lower(), self.current_para))
        else:
            c.execute('INSERT INTO bookmarks VALUES (?, ?)', (self.current_gesetz.lower(), self.current_para))
        conn.commit()
        conn.close()
        self.update_bookmark_button()
    
    def update_bookmark_button(self):
        if not self.current_gesetz:
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT * FROM bookmarks WHERE kuerzel=? AND paragraph=?', (self.current_gesetz.lower(), self.current_para))
        exists = c.fetchone()
        conn.close()
        self.bookmark_btn.text = '★ Gemerkt' if exists else 'Merken'
    
    def show_bookmarks(self, instance):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT kuerzel, paragraph FROM bookmarks ORDER BY kuerzel, paragraph')
        bookmarks = c.fetchall()
        conn.close()
        if not bookmarks:
            self.show_message('Keine Lesezeichen')
            return
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        scroll = ScrollView()
        item_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        item_box.bind(minimum_height=item_box.setter('height'))
        for kuerzel, para in bookmarks:
            btn = Button(text=f'{kuerzel.upper()} §{para}', size_hint_y=None, height=dp(45))
            btn.bind(on_press=lambda x, k=kuerzel, p=para: self.load_bookmark(k, p))
            item_box.add_widget(btn)
        scroll.add_widget(item_box)
        content.add_widget(scroll)
        btn_close = Button(text='Schließen', size_hint_y=None, height=dp(45))
        content.add_widget(btn_close)
        popup = Popup(title='Lesezeichen', content=content, size_hint=(0.9, 0.7))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()
    
    def load_bookmark(self, kuerzel, para):
        for window in list(Popup._queue):
            if hasattr(window, 'dismiss'):
                window.dismiss()
        for display, k in self.gesetz_dict.items():
            if k == kuerzel.upper():
                self.spinner.text = display
                break
        self.para_input.text = para
        self.search(None)
    
    def clear_cache(self, instance):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM cache')
        count = c.fetchone()[0]
        c.execute('DELETE FROM cache')
        conn.commit()
        conn.close()
        self.show_message(f'{count} Einträge gelöscht')
    
    def show_message(self, text):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text=text, font_size='14sp'))
        btn = Button(text='OK', size_hint_y=None, height=dp(40))
        content.add_widget(btn)
        popup = Popup(title='Info', content=content, size_hint=(0.8, 0.25))
        btn.bind(on_press=popup.dismiss)
        popup.open()

class JustizApp(App):
    def build(self):
        init_db()
        return JustizWidget()

if __name__ == '__main__':
    JustizApp().run()
