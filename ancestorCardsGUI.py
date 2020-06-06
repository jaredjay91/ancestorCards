#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# global import
from tkinter import Tk, StringVar, IntVar, filedialog, messagebox, Menu, TclError, PhotoImage, Canvas, Scrollbar
#from tkinter import *
from tkinter.ttk import Frame, Label, Entry, Button, Checkbutton, Treeview, Notebook
from threading import Thread
from diskcache import Cache
import time
import tempfile
import asyncio
import re
import os
import sys

# local import
from makeCardsHeader import *
from makeBlankCard import *
from myImages import *


try:
    import requests
except ImportError:
    sys.stderr.write('You need to install the requests module first\n')
    sys.stderr.write('(run this in your terminal: "python3 -m pip install requests" or "python3 -m pip install --user requests")\n')
    exit(2)

MAX_PERSONS = 200  # is subject to change: see https://www.familysearch.org/developers/docs/api/tree/Persons_resource

FACT_TAGS = {
    'http://gedcomx.org/Birth': 'BIRT',
    'http://gedcomx.org/Death': 'DEAT',
}


tmp_dir = os.path.join(tempfile.gettempdir(), 'getAncestorDataGUI')
global cache
cache = Cache(tmp_dir)
lang = cache.get('lang')


def _(string):
    return string

def cont(string):
    level = int(string[:1]) + 1
    lines = string.splitlines()
    res = list()
    max_len = 255
    for line in lines:
        c_line = line
        to_conc = list()
        while len(c_line.encode('utf-8')) > max_len:
            index = min(max_len, len(c_line) - 2)
            while (len(c_line[:index].encode('utf-8')) > max_len or re.search(r'[ \t\v]', c_line[index - 1:index + 1])) and index > 1:
                index -= 1
            to_conc.append(c_line[:index])
            c_line = c_line[index:]
            max_len = 248
        to_conc.append(c_line)
        res.append(('\n%s CONC ' % level).join(to_conc))
        max_len = 248
    return ('\n%s CONT ' % level).join(res)


# FamilySearch session class
class Session:
    def __init__(self, username, password, verbose=False, logfile=sys.stderr, timeout=60):
        self.username = username
        self.password = password
        self.verbose = verbose
        self.logfile = logfile
        self.timeout = timeout
        self.fid = self.lang = None
        self.counter = 0
        self.logged = self.login()

    # Write in logfile if verbose enabled
    def write_log(self, text):
        if self.verbose:
            self.logfile.write('[%s]: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), text))

    # retrieve FamilySearch session ID (https://familysearch.org/developers/docs/guides/oauth2)
    def login(self):
        while True:
            try:
                url = 'https://www.familysearch.org/auth/familysearch/login'
                self.write_log('Downloading: ' + url)
                r = requests.get(url, params={'ldsauth': False}, allow_redirects=False)
                url = r.headers['Location']
                self.write_log('Downloading: ' + url)
                r = requests.get(url, allow_redirects=False)
                idx = r.text.index('name="params" value="')
                span = r.text[idx + 21:].index('"')
                params = r.text[idx + 21:idx + 21 + span]

                url = 'https://ident.familysearch.org/cis-web/oauth2/v3/authorization'
                self.write_log('Downloading: ' + url)
                r = requests.post(url, data={'params': params, 'userName': self.username, 'password': self.password}, allow_redirects=False)

                if 'The username or password was incorrect' in r.text:
                    self.write_log('The username or password was incorrect')
                    return False

                if 'Invalid Oauth2 Request' in r.text:
                    self.write_log('Invalid Oauth2 Request')
                    time.sleep(self.timeout)
                    continue

                url = r.headers['Location']
                self.write_log('Downloading: ' + url)
                r = requests.get(url, allow_redirects=False)
                self.fssessionid = r.cookies['fssessionid']
            except requests.exceptions.ReadTimeout:
                self.write_log('Read timed out')
                continue
            except requests.exceptions.ConnectionError:
                self.write_log('Connection aborted')
                time.sleep(self.timeout)
                continue
            except requests.exceptions.HTTPError:
                self.write_log('HTTPError')
                time.sleep(self.timeout)
                continue
            except KeyError:
                self.write_log('KeyError')
                time.sleep(self.timeout)
                continue
            except ValueError:
                self.write_log('ValueError')
                time.sleep(self.timeout)
                continue
            self.write_log('FamilySearch session id: ' + self.fssessionid)
            return True

    # retrieve JSON structure from FamilySearch URL
    def get_url(self, url):
        self.counter += 1
        while True:
            try:
                self.write_log('Downloading: ' + url)
                # r = requests.get(url, cookies = { 's_vi': self.s_vi, 'fssessionid' : self.fssessionid }, timeout = self.timeout)
                r = requests.get('https://familysearch.org' + url, cookies={'fssessionid': self.fssessionid}, timeout=self.timeout)
            except requests.exceptions.ReadTimeout:
                self.write_log('Read timed out')
                continue
            except requests.exceptions.ConnectionError:
                self.write_log('Connection aborted')
                time.sleep(self.timeout)
                continue
            self.write_log('Status code: ' + str(r.status_code))
            if r.status_code == 204:
                return None
            if r.status_code in {404, 405, 410, 500}:
                self.write_log('WARNING: ' + url)
                return None
            if r.status_code == 401:
                self.login()
                continue
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                self.write_log('HTTPError')

                time.sleep(self.timeout)
                continue
            try:
                return r.json()
            except:
                self.write_log('WARNING: corrupted file from ' + url)
                return None

    # retrieve FamilySearch current user ID
    def set_current(self):
        url = '/platform/users/current.json'
        data = self.get_url(url)
        if data:
            self.fid = data['users'][0]['personId']
            self.lang = data['users'][0]['preferredLanguage']

    def get_userid(self):
        if not self.fid:
            self.set_current()
        return self.fid

    def _(self, string):
        if not self.lang:
            self.set_current()
        return string


# some GEDCOM objects
class Fact:

    def __init__(self, data=None, tree=None):
        self.value = self.type = self.date = self.place = None
        if data:
            if 'value' in data:
                self.value = data['value']
            if 'type' in data:
                self.type = data['type']
                if self.type[:6] == u'data:,':
                    self.type = self.type[6:]
                elif self.type not in FACT_TAGS:
                    self.type = None
            if 'date' in data:
                self.date = data['date']['original']
            if 'place' in data:
                place = data['place']
                self.place = place['original']

            if self.type == 'http://gedcomx.org/Death' and not (self.date or self.place):
                self.value = 'Y'

    def print(self, file=sys.stdout, key=None):
        if self.type in FACT_TAGS:
            tmp = '1 ' + FACT_TAGS[self.type]
            if self.value:
                tmp += ' ' + self.value
            file.write(cont(tmp))
        else:
            return
        file.write('\n')
        if self.date:
            file.write(cont('2 DATE ' + self.date) + '\n')
        if self.place:
            file.write(cont('2 PLAC ' + self.place) + '\n')


class Name:

    def __init__(self, data=None, tree=None):
        self.given = ''
        self.surname = ''
        self.prefix = None
        self.suffix = None
        if data:
            if 'parts' in data['nameForms'][0]:
                for z in data['nameForms'][0]['parts']:
                    if z['type'] == u'http://gedcomx.org/Given':
                        self.given = z['value']
                    if z['type'] == u'http://gedcomx.org/Surname':
                        self.surname = z['value']
                    if z['type'] == u'http://gedcomx.org/Prefix':
                        self.prefix = z['value']
                    if z['type'] == u'http://gedcomx.org/Suffix':
                        self.suffix = z['value']

    def print(self, file=sys.stdout, typ=None):
        tmp = '1 NAME ' + self.given + ' /' + self.surname + '/'
        if self.suffix:
            tmp += ' ' + self.suffix
        file.write(cont(tmp) + '\n')
        if typ:
            file.write('2 TYPE ' + typ + '\n')
        if self.prefix:
            file.write('2 NPFX ' + self.prefix + '\n')


# GEDCOM individual class
class Indi:

    counter = 0

    # initialize individual
    def __init__(self, fid=None, tree=None, num=None):
        if num:
            self.num = num
        else:
            Indi.counter += 1
            self.num = Indi.counter
        self.fid = fid
        self.tree = tree
        self.famc_fid = set()
        self.fams_fid = set()
        self.famc_num = set()
        self.fams_num = set()
        self.name = None
        self.gender = None
        self.parents = set()
        self.spouses = set()
        self.children = set()

        self.nicknames = set()
        self.facts = set()
        self.birthnames = set()
        self.married = set()
        self.aka = set()

    def add_data(self, data):
        if data:
            if data['names']:
                for x in data['names']:
                    if x['preferred']:
                        self.name = Name(x, self.tree)
                    else:
                        if x['type'] == u'http://gedcomx.org/Nickname':
                            self.nicknames.add(Name(x, self.tree))
                        if x['type'] == u'http://gedcomx.org/BirthName':
                            self.birthnames.add(Name(x, self.tree))
                        if x['type'] == u'http://gedcomx.org/AlsoKnownAs':
                            self.aka.add(Name(x, self.tree))
                        if x['type'] == u'http://gedcomx.org/MarriedName':
                            self.married.add(Name(x, self.tree))
            if 'gender' in data:
                if data['gender']['type'] == 'http://gedcomx.org/Male':
                    self.gender = 'M'
                elif data['gender']['type'] == 'http://gedcomx.org/Female':
                    self.gender = 'F'
                elif data['gender']['type'] == 'http://gedcomx.org/Unknown':
                    self.gender = 'U'
            if 'facts' in data:
                for x in data['facts']:
                    self.facts.add(Fact(x, self.tree))


    # add a fams to the individual
    def add_fams(self, fams):
        self.fams_fid.add(fams)

    # add a famc to the individual
    def add_famc(self, famc):
        self.famc_fid.add(famc)

    # print individual information in GEDCOM format
    def print(self, file=sys.stdout):
        file.write('\n' + str(self.num) + '\n')
        if self.name:
            self.name.print(file)
        if self.gender:
            file.write('GENDER ' + self.gender + '\n')
        for o in self.facts:
            o.print(file)
        for num in self.fams_num:
            file.write('FAMS @F' + str(num) + '@\n')
        for num in self.famc_num:
            file.write('FAMC @F' + str(num) + '@\n')
        file.write('_FSFTID ' + self.fid + '\n')


# GEDCOM family class
class Fam:
    counter = 0

    # initialize family
    def __init__(self, husb=None, wife=None, tree=None, num=None):
        if num:
            self.num = num
        else:
            Fam.counter += 1
            self.num = Fam.counter
        self.husb_fid = husb if husb else None
        self.wife_fid = wife if wife else None
        self.tree = tree
        self.husb_num = self.wife_num = self.fid = None
        self.facts = set()
        self.chil_fid = set()
        self.chil_num = set()

    # add a child to the family
    def add_child(self, child):
        if child not in self.chil_fid:
            self.chil_fid.add(child)

    # retrieve and add marriage information
    def add_marriage(self, fid):
        if not self.fid:
            self.fid = fid
            url = '/platform/tree/couple-relationships/%s.json' % self.fid
            data = self.tree.fs.get_url(url)
            if data:
                if 'facts' in data['relationships'][0]:
                    for x in data['relationships'][0]['facts']:
                        self.facts.add(Fact(x, self.tree))

    # print family information in GEDCOM format
    def print(self, file=sys.stdout):
        file.write('\n@F' + str(self.num) + '@ FAM\n')
        if self.husb_num:
            file.write('HUSB @I' + str(self.husb_num) + '@\n')
        if self.wife_num:
            file.write('WIFE @I' + str(self.wife_num) + '@\n')
        for num in self.chil_num:
            file.write('CHIL @I' + str(num) + '@\n')
        if self.fid:
            file.write('_FSFTID ' + self.fid + '\n')


# family tree class
class Tree:
    def __init__(self, fs=None):
        self.fs = fs
        self.indi = dict()
        self.fam = dict()
        self.places = dict()

    # add individuals to the family tree
    def add_indis(self, fids):
        async def add_datas(loop, data):
            futures = set()
            for person in data['persons']:
                self.indi[person['id']] = Indi(person['id'], self)
                futures.add(loop.run_in_executor(None, self.indi[person['id']].add_data, person))
            for future in futures:
                await future

        new_fids = [fid for fid in fids if fid and fid not in self.indi]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # loop = asyncio.get_event_loop()
        while len(new_fids):
            data = self.fs.get_url('/platform/tree/persons.json?pids=' + ','.join(new_fids[:MAX_PERSONS]))
            if data:
                if 'places' in data:
                    for place in data['places']:
                        if place['id'] not in self.places:
                            self.places[place['id']] = (str(place['latitude']), str(place['longitude']))
                loop.run_until_complete(add_datas(loop, data))
                if 'childAndParentsRelationships' in data:
                    for rel in data['childAndParentsRelationships']:
                        father = rel['father']['resourceId'] if 'father' in rel else None
                        mother = rel['mother']['resourceId'] if 'mother' in rel else None
                        child = rel['child']['resourceId'] if 'child' in rel else None
                        if child in self.indi:
                            self.indi[child].parents.add((father, mother))
                        if father in self.indi:
                            self.indi[father].children.add((father, mother, child))
                        if mother in self.indi:
                            self.indi[mother].children.add((father, mother, child))
                if 'relationships' in data:
                    for rel in data['relationships']:
                        if rel['type'] == u'http://gedcomx.org/Couple':
                            person1 = rel['person1']['resourceId']
                            person2 = rel['person2']['resourceId']
                            relfid = rel['id']
                            if person1 in self.indi:
                                self.indi[person1].spouses.add((person1, person2, relfid))
                            if person2 in self.indi:
                                self.indi[person2].spouses.add((person1, person2, relfid))
            new_fids = new_fids[MAX_PERSONS:]

    # add family to the family tree
    def add_fam(self, father, mother):
        if not (father, mother) in self.fam:
            self.fam[(father, mother)] = Fam(father, mother, self)

    # add a children relationship (possibly incomplete) to the family tree
    def add_trio(self, father, mother, child):
        if father in self.indi:
            self.indi[father].add_fams((father, mother))
        if mother in self.indi:
            self.indi[mother].add_fams((father, mother))
        if child in self.indi and (father in self.indi or mother in self.indi):
            self.indi[child].add_famc((father, mother))
            self.add_fam(father, mother)
            self.fam[(father, mother)].add_child(child)

    # add parents relationships
    def add_parents(self, fids):
        parents = set()
        for fid in (fids & self.indi.keys()):
            for couple in self.indi[fid].parents:
                parents |= set(couple)
        if parents:
            self.add_indis(parents)
        for fid in (fids & self.indi.keys()):
            for father, mother in self.indi[fid].parents:
                if mother in self.indi and father in self.indi or not father and mother in self.indi or not mother and father in self.indi:
                    self.add_trio(father, mother, fid)
        return set(filter(None, parents))

    # add spouse relationships
    def add_spouses(self, fids):
        async def add(loop, rels):
            futures = set()
            for father, mother, relfid in rels:
                if (father, mother) in self.fam:
                    futures.add(loop.run_in_executor(None, self.fam[(father, mother)].add_marriage, relfid))
            for future in futures:
                await future

        rels = set()
        for fid in (fids & self.indi.keys()):
            rels |= self.indi[fid].spouses
        loop = asyncio.get_event_loop()
        if rels:
            self.add_indis(set.union(*({father, mother} for father, mother, relfid in rels)))
            for father, mother, relfid in rels:
                if father in self.indi and mother in self.indi:
                    self.indi[father].add_fams((father, mother))
                    self.indi[mother].add_fams((father, mother))
                    self.add_fam(father, mother)
            loop.run_until_complete(add(loop, rels))

    # add children relationships
    def add_children(self, fids):
        rels = set()
        for fid in (fids & self.indi.keys()):
            rels |= self.indi[fid].children if fid in self.indi else set()
        children = set()
        if rels:
            self.add_indis(set.union(*(set(rel) for rel in rels)))
            for father, mother, child in rels:
                if child in self.indi and (mother in self.indi and father in self.indi or not father and mother in self.indi or not mother and father in self.indi):
                    self.add_trio(father, mother, child)
                    children.add(child)
        return children


    def reset_num(self):
        for husb, wife in self.fam:
            self.fam[(husb, wife)].husb_num = self.indi[husb].num if husb else None
            self.fam[(husb, wife)].wife_num = self.indi[wife].num if wife else None
            self.fam[(husb, wife)].chil_num = set([self.indi[chil].num for chil in self.fam[(husb, wife)].chil_fid])
        for fid in self.indi:
            self.indi[fid].famc_num = set([self.fam[(husb, wife)].num for husb, wife in self.indi[fid].famc_fid])
            self.indi[fid].fams_num = set([self.fam[(husb, wife)].num for husb, wife in self.indi[fid].fams_fid])

    # print GEDCOM file
    def print(self, file=sys.stdout):
        file.write('0 HEAD\n')
        file.write('1 CHAR UTF-8\n')
        file.write('1 GEDC\n')
        file.write('2 VERS 5.5\n')
        file.write('2 FORM LINEAGE-LINKED\n')
        for fid in sorted(self.indi, key=lambda x: self.indi.__getitem__(x).num):
            self.indi[fid].print(file)
        for husb, wife in sorted(self.fam, key=lambda x: self.fam.__getitem__(x).num):
            self.fam[(husb, wife)].print(file)
        file.write('0 TRLR\n')


# Entry widget with right-clic menu to copy/cut/paste
class EntryWithMenu(Entry):
    def __init__(self, master, **kw):
        super(EntryWithMenu, self).__init__(master, **kw)
        self.bind('<Button-3>', self.click_right)

    def click_right(self, event):
        menu = Menu(self, tearoff=0)
        try:
            self.selection_get()
            state = 'normal'
        except TclError:
            state = 'disabled'
        menu.add_command(label=_('Copy'), command=self.copy, state=state)
        menu.add_command(label=_('Cut'), command=self.cut, state=state)
        menu.add_command(label=_('Paste'), command=self.paste)
        menu.post(event.x_root, event.y_root)

    def copy(self):
        self.clipboard_clear()
        text = self.selection_get()
        self.clipboard_append(text)

    def cut(self):
        self.copy()
        self.delete('sel.first', 'sel.last')

    def paste(self):
        try:
            text = self.selection_get(selection='CLIPBOARD')
            self.insert('insert', text)
        except TclError:
            pass


# List of files to make
class FilesToMake(Treeview):
    def __init__(self, master, **kwargs):
        super(FilesToMake, self).__init__(master, selectmode='extended', height=5, **kwargs)
        self.heading('#0', text=_('Files'))
        self.column('#0', width=300)
        self.files = dict()
        self.bind('<Button-3>', self.popup)

    def add_file(self, filename):
        if any(f.name == filename for f in self.files.values()):
            messagebox.showinfo(_('Error'), message=_('File already exist: ') + os.path.basename(filename))
            return
        if not os.path.exists(filename):
            messagebox.showinfo(_('Error'), message=_('File not found: ') + os.path.basename(filename))
            return
        file = open(filename, 'r', encoding='utf-8')
        new_id = self.insert('', 0, text=os.path.basename(filename))
        self.files[new_id] = file

    def popup(self, event):
        item = self.identify_row(event.y)
        if item:
            menu = Menu(self, tearoff=0)
            menu.add_command(label=_('Remove'), command=self.delete_item(item))
            menu.post(event.x_root, event.y_root)

    def delete_item(self, item):
        def delete():
            self.files[item].close()
            self.files.pop(item)
            self.delete(item)
        return delete

# Make Cards widget
class Make(Frame):

    def __init__(self, master, **kwargs):
        super(Make, self).__init__(master, **kwargs)
        warning = Label(self, font=('a', 7), wraplength=300, justify='center', text=_('Select the files containing the information on your ancestors. The files must be in *.csv format, with values separated by semicolons.'))
        self.files_to_make = FilesToMake(self)
        self.btn_add_file = Button(self, text=_('Add files'), command=self.add_files)
        buttons = Frame(self, borderwidth=20)
        self.btn_quit = Button(buttons, text=_('Quit'), command=self.quit)
        self.btn_save = Button(buttons, text=_('Make'), command=self.save)
        warning.pack()
        self.files_to_make.pack()
        self.btn_add_file.pack()
        self.btn_quit.pack(side='left', padx=(0, 40))
        self.btn_save.pack(side='right', padx=(40, 0))
        buttons.pack(side='bottom')

    def add_files(self):
        for filename in filedialog.askopenfilenames(title=_('Open'), defaultextension='.csv', filetypes=(('CSV', '.csv'), (_('All files'), '*.*'))):
            self.files_to_make.add_file(filename)

    def save(self):
        if not self.files_to_make.files:
            messagebox.showinfo(_('Error'), message=_('Please add files'))
            return

        #read the file and make the cards
        for file in self.files_to_make.files.values():
             makeCards(file)

        #write message when finished
        messagebox.showinfo(_('Info'), message=_('Cards generated successfully'))

    # prevent exception on quit during download
    def quit(self):
        super(Make, self).quit()
        os._exit(1)


# Instructions widget
class Instructions(Frame):

    def __init__(self, master, **kwargs):
        super(Instructions, self).__init__(master, **kwargs)

        def myfunction(event):
            canvas.configure(scrollregion=canvas.bbox("all"), width=360, height=220)

        canvas=Canvas(self)
        frame=Frame(canvas)
        myscrollbar=Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=myscrollbar.set)

        myscrollbar.pack(side="right",fill="y")
        canvas.pack(side="left")
        canvas.create_window((0,0),window=frame,anchor='nw')
        frame.bind("<Configure>",myfunction)
        #Label(frame, font=('a', 11), wraplength=350, justify='left', text=_('Step 1: Download information on your ancestors from familysearch.org using the \"Download Ancestor Data\" tab.')).grid(row=0,column=0)
        #Label(frame, font=('a', 11), wraplength=350, justify='left', text='Step 2: Edit the *.csv file that you downloaded in step 1 (it will open in excel or any other spreadsheet program). Fill in any missing information and write a short life summary for each person.').grid(row=2,column=0)
        #Label(frame, font=('a', 11), wraplength=350, justify='left', text='Step 3: Collect photos of your ancestors to put on the cards.').grid(row=4,column=0)
        #Label(frame, font=('a', 11), wraplength=350, justify='left', text='Step 4: Open the \"Make Cards\" tab. Select your *.csv file to make the cards from. Click \"Make\", and then select a photo for each person. If you don\'t have a photo for someone, just click \"Cancel\" when prompted. The cards will be generated in a folder called \"cards\".').grid(row=6,column=0)
        #Label(frame, font=('a', 11), wraplength=350, justify='left', text='Step 5: Pages of 6 cards each will be generated in a PDF called \"PrintableCards.pdf\" in the same directory as the app. Print the cards images and cut them out.').grid(row=8,column=0)
        Label(frame, font=('a', 11), wraplength=350, justify='left', text='Step 1: Download information on your ancestors from familysearch.org using the \"Download Ancestor Data\" tab.\n\nStep 2: Edit the *.csv file that you downloaded in step 1 (it will open in Excel or any other spreadsheet program). Fill in any missing information and write a short life summary (no more than 160 words) for each person. The cards can still be generated even if you are missing some information. Anything left blank in the spreadsheet will be blank on the cards.\n\nStep 3: Collect photos of your ancestors to put on the cards. This program will not crop or edit your photos in any way. Whatever you give to this program will be pasted to the cards, unedited.\n\nStep 4: Open the \"Make Cards\" tab. Select your *.csv file that contains all the data on your ancestors. Click \"Make\". You will then be prompted to select a photo for each person, one by one. If you don\'t have a photo for someone, just click \"Cancel\" when prompted. Individual cards will be generated in a folder called \"cards\". Printable pages of cards will be generated in a PDF called \"PrintableCards.pdf\" in the same directory where you placed this app.\n\nStep 5: Print the cards, cut them out, and fold them. The quality of the final product depends very much on how it is printed.').grid(row=0,column=0)
    # prevent exception on quit during download
    def quit(self):
        super(Instructions, self).quit()
        os._exit(1)


# Sign In widget
class SignIn(Frame):

    def __init__(self, master, **kwargs):
        super(SignIn, self).__init__(master, **kwargs)
        self.username = StringVar()
        self.password = StringVar()
        label_username = Label(self, text=_('Username:'))
        entry_username = EntryWithMenu(self, textvariable=self.username, width=30)
        label_password = Label(self, text=_('Password:'))
        entry_password = EntryWithMenu(self, show='●', textvariable=self.password, width=30)
        label_username.grid(row=0, column=0, pady=15, padx=(0, 5))
        entry_username.grid(row=0, column=1)
        label_password.grid(row=1, column=0, padx=(0, 5))
        entry_password.grid(row=1, column=1)
        entry_username.focus_set()
        entry_username.bind('<Key>', self.enter)
        entry_password.bind('<Key>', self.enter)

    def enter(self, evt):
        if evt.keysym in {'Return', 'KP_Enter'}:
            self.master.master.command_in_thread(self.master.master.login)()


# List of starting individuals
class StartIndis(Treeview):
    def __init__(self, master, **kwargs):
        super(StartIndis, self).__init__(master, selectmode='extended', height=5, columns=('fid',), **kwargs)
        self.heading('#0', text=_('Name'))
        self.column('#0', width=250)
        self.column('fid', width=80)
        self.indis = dict()
        self.heading('fid', text='Id')
        self.bind('<Button-3>', self.popup)

    def add_indi(self, fid):
        if not fid:
            return
        if fid in self.indis.values():
            messagebox.showinfo(_('Error'), message=_('ID already exist'))
            return
        if not re.match(r'[A-Z0-9]{4}-[A-Z0-9]{3}', fid):
            messagebox.showinfo(_('Error'), message=_('Invalid FamilySearch ID: ') + fid)
            return
        fs = self.master.master.master.fs
        data = fs.get_url('/platform/tree/persons/%s.json' % fid)
        if data and 'persons' in data:
            if 'names' in data['persons'][0]:
                for name in data['persons'][0]['names']:
                    if name['preferred']:
                        self.indis[self.insert('', 0, text=name['nameForms'][0]['fullText'], values=fid)] = fid
                        return True
        messagebox.showinfo(_('Error'), message=_('Individual not found'))

    def popup(self, event):
        item = self.identify_row(event.y)
        if item:
            menu = Menu(self, tearoff=0)
            menu.add_command(label=_('Remove'), command=self.delete_item(item))
            menu.post(event.x_root, event.y_root)

    def delete_item(self, item):
        def delete():
            self.indis.pop(item)
            self.delete(item)
        return delete


# Options form
class Options(Frame):
    def __init__(self, master, ordinances=False, **kwargs):
        super(Options, self).__init__(master, **kwargs)
        self.ancestors = IntVar()
        self.ancestors.set(4)
        self.descendants = IntVar()
        self.spouses = IntVar()
        self.ordinances = IntVar()
        self.contributors = IntVar()
        self.start_indis = StartIndis(self)
        self.fid = StringVar()
        btn = Frame(self)
        entry_fid = EntryWithMenu(btn, textvariable=self.fid, width=16)
        entry_fid.bind('<Key>', self.enter)
        label_ancestors = Label(self, text=_('Number of generations to ascend'))
        entry_ancestors = EntryWithMenu(self, textvariable=self.ancestors, width=5)
        #label_descendants = Label(self, text=_('Number of generations to descend'))
        #entry_descendants = EntryWithMenu(self, textvariable=self.descendants, width=5)
        btn_add_indi = Button(btn, text=_('Add a FamilySearch ID'), command=self.add_indi)
        self.start_indis.grid(row=0, column=0, columnspan=3)
        entry_fid.grid(row=0, column=0, sticky='w')
        btn_add_indi.grid(row=0, column=1, sticky='w')
        btn.grid(row=1, column=0, columnspan=2, sticky='w')
        entry_ancestors.grid(row=2, column=0, sticky='w')
        label_ancestors.grid(row=2, column=1, sticky='w')
        #entry_descendants.grid(row=3, column=0, sticky='w')
        #label_descendants.grid(row=3, column=1, sticky='w')
        #btn_spouses.grid(row=4, column=0, columnspan=2, sticky='w')
        #if ordinances:
        #    btn_ordinances.grid(row=5, column=0, columnspan=3, sticky='w')
        #btn_contributors.grid(row=6, column=0, columnspan=3, sticky='w')
        entry_ancestors.focus_set()

    def add_indi(self):
        if self.start_indis.add_indi(self.fid.get()):
            self.fid.set('')

    def enter(self, evt):
        if evt.keysym in {'Return', 'KP_Enter'}:
            self.add_indi()


# Main widget
class Download(Frame):
    def __init__(self, master, **kwargs):
        super(Download, self).__init__(master, borderwidth=20, **kwargs)
        self.fs = None
        self.tree = None
        self.logfile = None

        # User informations
        self.info_tree = False
        self.start_time = None
        info = Frame(self, borderwidth=10)
        self.info_label = Label(info, wraplength=350, borderwidth=20, justify='center', font=('a', 10, 'bold'))
        self.info_indis = Label(info)
        self.info_fams = Label(info)
        self.time = Label(info)
        self.info_label.grid(row=0, column=0, columnspan=2)
        self.info_indis.grid(row=1, column=0)
        self.info_fams.grid(row=1, column=1)
        self.time.grid(row=3, column=0, columnspan=2)

        self.form = Frame(self)
        self.sign_in = SignIn(self.form)
        self.options = None
        self.title = Label(self, text=_('Sign In to FamilySearch'), font=('a', 12, 'bold'))
        buttons = Frame(self)
        self.btn_quit = Button(buttons, text=_('Quit'), command=Thread(target=self.quit).start)
        self.btn_valid = Button(buttons, text=_('Sign In'), command=self.command_in_thread(self.login))
        self.title.pack()
        self.sign_in.pack()
        self.form.pack()
        self.btn_quit.pack(side='left', padx=(0, 40))
        self.btn_valid.pack(side='right', padx=(40, 0))
        info.pack()
        buttons.pack(side='bottom')
        self.pack()
        self.update_needed = False

    def info(self, text):
        self.info_label.config(text=text)

    def save(self):
        filename = filedialog.asksaveasfilename(title=_('Save as'), defaultextension='.csv', filetypes=(('CSV', '.csv'), (_('All files'), '*.*')))
        if not filename:
            return
        #with open(filename, 'w', encoding='utf-8') as file:
            #self.tree.print(file)
        fh = open(filename, "w")
        fh.write('personnum')
        fh.write(';')
        fh.write('given names')
        fh.write(';')
        fh.write('surname')
        fh.write(';')
        fh.write('gender')
        fh.write(';')
        fh.write('birthdate')
        fh.write(';')
        fh.write('birthplace')
        fh.write(';')
        fh.write('deathdate')
        fh.write(';')
        fh.write('deathplace')
        fh.write(';')
        fh.write('fathernum')
        fh.write(';')
        fh.write('mothernum')
        fh.write(';')
        fh.write('spousenum')
        fh.write(';')
        fh.write('childnum')
        fh.write(';')
        fh.write('Life Summary')
        fh.write('\n')
        for fid in sorted(self.tree.indi, key=lambda x: self.tree.indi.__getitem__(x).num):
            #person number
            personnum = self.tree.indi[fid].fid
            #name
            givennames = self.tree.indi[fid].name.given
            #surname, all caps
            surname = self.tree.indi[fid].name.surname
            #gender
            gender = self.tree.indi[fid].gender
            #birth and death
            birthstring = 'b. '
            deathstring = 'd. '
            birthdate = ''
            birthplace = ''
            deathdate = ''
            deathplace = ''
            for o in self.tree.indi[fid].facts:
                if o.type == 'http://gedcomx.org/Birth':
                    if o.date:
                        birthdate = o.date
                        birthstring = birthstring + o.date
                    if o.place:
                        birthplace = o.place
                        birthstring = birthstring + ' in ' + o.place
                if o.type == 'http://gedcomx.org/Death':
                    if o.date:
                        deathdate = o.date
                        deathstring = deathstring + o.date
                    if o.place:
                        deathplace = o.place
                        deathstring = deathstring + ' in ' + o.place
            fathernum = ''
            mothernum = ''
            for p in self.tree.indi[fid].parents:
            #father number
                fathernum = p[0]
            #mother number
                mothernum = p[1]
            spousenum = ''
            childnum = ''
            childset = ''
            for husb, wife in sorted(self.tree.fam, key=lambda x: self.tree.fam.__getitem__(x).num):
                if self.tree.fam[(husb, wife)].husb_fid == fid:
                    childnum = self.tree.fam[(husb, wife)].chil_fid.pop()
                    self.tree.fam[(husb, wife)].chil_fid.add(childnum)
                    spousenum = self.tree.fam[(husb, wife)].wife_fid
                elif self.tree.fam[(husb, wife)].wife_fid == fid:
                    childnum = self.tree.fam[(husb, wife)].chil_fid.pop()
                    self.tree.fam[(husb, wife)].chil_fid.add(childnum)
                    spousenum = self.tree.fam[(husb, wife)].husb_fid
                else:
                    continue

            #print('')
            #print(personnum)
            #print(givennames + ' ' + surname)
            #print(surname.upper())
            #print(birthstring)
            #print(deathstring)
            #print(fathernum)
            #print(mothernum)
            #print(spousenum)
            #print(childnum)
            #print('Life Summary ...')

            #Print out in semicolon-csv format
            if personnum:
                fh.write(personnum)
            fh.write(';')
            if givennames:
                fh.write(givennames)
            fh.write(';')
            if surname:
                fh.write(surname)
            fh.write(';')
            if gender:
                fh.write(gender)
            fh.write(';')
            if birthdate:
                fh.write(birthdate)
            fh.write(';')
            if birthplace:
                fh.write(birthplace)
            fh.write(';')
            if deathdate:
                fh.write(deathdate)
            fh.write(';')
            if deathplace:
                fh.write(deathplace)
            fh.write(';')
            if fathernum:
                fh.write(fathernum)
            fh.write(';')
            if mothernum:
                fh.write(mothernum)
            fh.write(';')
            if spousenum:
                fh.write(spousenum)
            fh.write(';')
            if childnum:
                fh.write(childnum)
            fh.write(';')
            fh.write('')
            fh.write('\n')

        fh.close()

    def login(self):
        global _
        username = self.sign_in.username.get()
        password = self.sign_in.password.get()
        if not (username and password):
            messagebox.showinfo(message=_('Please enter your FamilySearch username and password.'))
            return
        self.btn_valid.config(state='disabled')
        self.info(_('Login to FamilySearch...'))
        self.logfile = open('download.log', 'w', encoding='utf-8')
        self.fs = Session(self.sign_in.username.get(), self.sign_in.password.get(), verbose=True, logfile=self.logfile, timeout=1)
        if not self.fs.logged:
            messagebox.showinfo(_('Error'), message=_('The username or password was incorrect'))
            self.btn_valid.config(state='normal')
            self.info('')
            return
        self.tree = Tree(self.fs)
        _ = self.fs._
        self.title.config(text=_('Options'))
        cache.delete('lang')
        cache.add('lang', self.fs.lang)
        lds_account = self.fs.get_url('/platform/tree/persons/%s/ordinances.json' % self.fs.get_userid()) != 'error'
        self.options = Options(self.form, lds_account)
        self.info('')
        self.sign_in.destroy()
        self.options.pack()
        self.master.change_lang()
        self.btn_valid.config(command=self.command_in_thread(self.download), state='normal', text=_('Download'))
        self.options.start_indis.add_indi(self.fs.get_userid())
        self.update_needed = False

    def quit(self):
        self.update_needed = False
        if self.logfile:
            self.logfile.close()
        super(Download, self).quit()
        # prevent exception during download
        os._exit(1)

    def download(self):
        todo = [self.options.start_indis.indis[key] for key in sorted(self.options.start_indis.indis)]
        for fid in todo:
            if not re.match(r'[A-Z0-9]{4}-[A-Z0-9]{3}', fid):
                messagebox.showinfo(_('Error'), message=_('Invalid FamilySearch ID: ') + fid)
                return
        self.start_time = time.time()
        self.options.destroy()
        self.form.destroy()
        self.title.config(text='Ancestor Cards')
        self.btn_valid.config(state='disabled')
        self.info(_('Download starting individuals...'))
        self.info_tree = True
        self.tree.add_indis(todo)
        todo = set(todo)
        done = set()
        for i in range(self.options.ancestors.get()):
            if not todo:
                break
            done |= todo
            self.info(_('Download ') + str(i + 1) + _('th generation of ancestors...'))
            todo = self.tree.add_parents(todo) - done

        todo = set(self.tree.indi.keys())
        done = set()
        for i in range(self.options.descendants.get()):
            if not todo:
                break
            done |= todo
            self.info(_('Download ') + str(i + 1) + _('th generation of descendants...'))
            todo = self.tree.add_children(todo) - done

        if self.options.spouses.get():
            self.info(_('Download spouses and marriage information...'))
            todo = set(self.tree.indi.keys())
            self.tree.add_spouses(todo)

        self.tree.reset_num()
        self.btn_valid.config(command=self.save, state='normal', text=_('Save'))
        self.info(text=_('Success ! Click below to save your CSV file'))
        self.update_info_tree()
        self.update_needed = False

    def command_in_thread(self, func):
        def res():
            self.update_needed = True
            Thread(target=self.update_gui).start()
            Thread(target=func).start()
        return res

    def update_info_tree(self):
        if self.info_tree and self.start_time and self.tree:
            self.info_indis.config(text=_('Individuals: %s') % len(self.tree.indi))
            self.info_fams.config(text=_('Families: %s') % len(self.tree.fam))
            t = round(time.time() - self.start_time)
            minutes = t // 60
            seconds = t % 60
            self.time.config(text=_('Elapsed time: %s:%s') % (minutes, '00%s'[len(str(seconds)):] % seconds))

    def update_gui(self):
        while self.update_needed:
            self.update_info_tree()
            self.master.update()
            time.sleep(0.1)


class FStoGEDCOM(Notebook):
    def __init__(self, master, **kwargs):
        super(FStoGEDCOM, self).__init__(master, width=400, **kwargs)
        self.instructions = Instructions(self)
        self.download = Download(self)
        self.make = Make(self)
        self.add(self.instructions, text=_('Instructions'))
        self.add(self.download, text=_('Download Ancestor Data'))
        self.add(self.make, text=_('Make Cards'))
        self.pack()

    def change_lang(self):
        self.tab(self.index(self.instructions), text=_('Instructions'))
        self.tab(self.index(self.download), text=_('Download Ancestor Data'))
        self.tab(self.index(self.make), text=_('Make Cards'))
        self.download.btn_quit.config(text=_('Quit'))
        self.make.btn_quit.config(text=_('Quit'))
        self.make.btn_save.config(text=_('Make'))
        self.make.btn_add_file.config(text=_('Add files'))


if __name__ == '__main__':
    root = Tk()
    root.title('Ancestor Cards')
    if sys.platform != 'darwin':
        #root.iconphoto(True, PhotoImage(file=resource_path('littleTreePic.png')))
        littleTreePic=littleTreePic2String#GIF decoded to string. imageString from myimages.py
        render = PhotoImage(data=littleTreePic)
        #myLabel.config(image=render)
        root.iconphoto(True, render)
    makeBlankCard("male")
    makeBlankCard("female")
    makeBlankInside()
    fstogedcom = FStoGEDCOM(root)
    fstogedcom.mainloop()
