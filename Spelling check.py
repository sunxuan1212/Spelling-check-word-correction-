import json
from pathlib import Path
import re
import nltk
import sys
import collections
from PyQt5.QtWidgets import QWidget, QComboBox, QPlainTextEdit, QPushButton, QListWidget, QLineEdit, QApplication, \
    QMenu, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtGui import QTextCursor
from operator import itemgetter
from nltk.collocations import *


# *****************************************************************
# >>>>>>>>>> Class GUI -- defining class and methods  <<<<<<<<<<<<<
class GUI(QWidget):

    def __init__(self):
        super().__init__()
        self.initialization_UI()

    def initialization_UI(self):
        self.resize(900, 500)
        self.setWindowTitle('Spell Checker')

        # Create Combobox
        self.combo_box = QComboBox(self)
        self.combo_box.move(200, 10)
        self.combo_box.addItem('All')
        self.combo_box.addItem('Real-Word')
        self.combo_box.addItem('Non-Word')

        # Create multiline textbox
        self.text_box = QPlainTextEdit(self)
        self.text_box.move(20, 50)
        self.text_box.resize(500, 400)
        self.text_box.setPlaceholderText("Text Editor (500 Words)")

        # Create a button in the window
        self.button_check = QPushButton('Check', self)
        self.button_check.move(180, 450)
        self.button_add = QPushButton('Add', self)
        self.button_add.move(280, 450)

        # create a dictionary list
        self.dic_list = QListWidget(self)
        self.dic_list.move(550, 50)
        self.dic_list.resize(300, 350)

        # create single text box
        self.search_line = QLineEdit(self)
        self.search_line.move(550, 420)
        self.search_line.resize(250, 25)

        self.button_search = QPushButton('Search', self)
        self.button_search.move(810, 420)

        # connect to clicked function
        self.button_check.clicked.connect(self.check_clicked)
        self.button_search.clicked.connect(self.search_clicked)
        self.button_add.clicked.connect(self.add_clicked)
        self.show()

    # Other methods under GUI class ==========================================
    # press the check button
    def check_clicked(self):
        global candidate_list
        if self.combo_box.currentText() == 'Non-Word':
            sentence = self.text_box.toPlainText()
            nonword_error_list = check_nonword(sentence)  # find non word errors

            # create candidate list and store to global variable
            candidate_list = create_non_candidate(nonword_error_list,
                                                  unigram_dict)  # creating candidate list for non-word
            candidate_list = select_top10(nonword_error_list, candidate_list)  # select top10
            pink_start = '<span style=\" background-color:#ffc2cd;\" >'
            self.one_highlight('Non-Word', candidate_list, pink_start)
        elif self.combo_box.currentText() == 'Real-Word':
            sentence = self.text_box.toPlainText()
            nonword_error_list = check_nonword(sentence)  # find non word errors
            candidate_list = real_word(nonword_error_list)  # find real_errors and create candidate_list

            # create candidate list and store to global variable
            yellow_start = '<span style=\" background-color:#f7dc6f;\" >'
            self.one_highlight('Real-Word', candidate_list, yellow_start)
        elif self.combo_box.currentText() == 'All':
            # === Non word part ===
            sentence = self.text_box.toPlainText()
            nonword_error_list = check_nonword(sentence)  # find non word errors

            # create non-word candidate list
            non_candidate_list = create_non_candidate(nonword_error_list,
                                                      unigram_dict)  # creating candidate list for non-word
            non_candidate_list = select_top10(nonword_error_list, non_candidate_list)  # select top10

            # === Real word part ===
            # find real_errors and create candidate_list
            real_candidate_list = real_word(nonword_error_list)  # find real word errors

            # === both ===
            # create merged candidate_list
            candidate_list = non_candidate_list + real_candidate_list
            # set highlight for both non-word and real-word
            self.both_highlight(nonword_error_list, real_candidate_list)

    # get the whole textbox contents
    def get_main_text(self):
        contents = self.text_box.toPlainText()
        # return the contents in the main text box
        return contents

    # get a search word from search text box
    def get_searching_word(self):
        search_word = self.search_line.text()
        return search_word

    # updating words in dictionary list box
    def update_dictionary_list(self, dic_words):
        i = 0
        for element in dic_words:
            self.dic_list.insertItem(i, element)
            i = i + 1

    # highlight words for one type of error (real-word or non-word)
    def one_highlight(self, RN, highlight_words, col_start):
        fmt_end = '</span>'
        white_start = '<span style=\" background-color:#ffffff; \" >'
        space = '<span style=\" background-color:#ffffff; \" > </span>'
        input_texts = self.text_box.toPlainText().split()
        self.text_box.clear()

        text = ''
        put = False
        # creating the html string
        for index, (previous, current) in enumerate(zip(input_texts, input_texts[1:])):
            pre_temp = re.sub(r'[.,]', '', previous)  # removing .and, for comparison
            cur_temp = re.sub(r'[.,]', '', current)
            found = False

            if RN == 'Non-Word':
                # treat the first word in highlight_words
                if index == 0 and pre_temp not in [data.word for data in highlight_words]:
                    text = text + white_start + previous + fmt_end + space
                    put = True
                elif index == 0 and pre_temp in [data.word for data in highlight_words]:
                    text = text + col_start + previous + fmt_end + space
                    put = True

                # highlight the other words
                if cur_temp in [data.word for data in highlight_words]:
                    found = True
                    text = text + col_start + current + fmt_end + space

            elif RN == 'Real-Word':
                # treat the first word in highlight_words
                if index == 0 and not put:  # for the first word
                    text = text + white_start + previous + fmt_end + space

                # highlight the other words
                for set in highlight_words:
                    if set.error == (pre_temp, cur_temp):  # check the tuple combination
                        found = True
                        text = text + col_start + current + fmt_end + space
                        break

            if not found:  # False
                text = text + white_start + current + fmt_end + space

        self.text_box.appendHtml(text)
        self.text_box.repaint()

    # highlight for both non and real words
    def both_highlight(self, highlight_non, highlight_real):
        # setting color values for real and call highlight function
        yellow_start = '<span style=\" background-color:#f7dc6f;\" >'
        pink_start = '<span style=\" background-color:#ffc2cd;\" >'
        white_start = '<span style=\" background-color:#ffffff; \" >'
        fmt_end = '</span>'
        space = '<span style=\" background-color:#ffffff; \" > </span>'

        # getting the input and clearing the text_box
        input_texts = self.text_box.toPlainText().split()
        self.text_box.clear()

        hi_non = highlight_non.copy()
        hi_real = highlight_real.copy()
        text = ''
        # creating the html string
        for index, (previous, current) in enumerate(zip(input_texts, input_texts[1:])):
            pre_temp = re.sub(r'[.,]', '', previous)  # removing .and, for comparison
            cur_temp = re.sub(r'[.,]', '', current)
            found = False

            if cur_temp in hi_non:  # if the current word found in nonword highlight list
                found = True
                text = text + pink_start + current + fmt_end + space
            else:  # if the current word found in real-word highlight list
                if index == 0:  # for the first word
                    text = text + white_start + previous + fmt_end + space
                else:
                    for set in hi_real:
                        if set.error == (pre_temp, cur_temp):
                            found = True
                            text = text + yellow_start + current + fmt_end + space
                            break

            if not found:  # False
                text = text + white_start + current + fmt_end + space

        self.text_box.appendHtml(text)
        self.text_box.repaint()

    # when search button being clicked, search the word and update GUI
    def search_clicked(self):
        search_word = self.search_line.text()
        if search_word in unigram_dict:
            item = self.dic_list.findItems(search_word, Qt.MatchExactly)[0]
            row_num = self.dic_list.row(item)
            self.dic_list.scrollToItem(item, QAbstractItemView.PositionAtCenter)
            self.dic_list.setCurrentRow(row_num)
            self.dic_list.repaint()
        else:
            self.showMessagebox("The searched word is not in the dictionary.")

    # show the messagebox when it's called
    def showMessagebox(self, word):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(word)
        msgBox.setWindowTitle("Alert")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()

    # Add unigram to unigram dictionary, or bigram tuples to bigram dictionary
    def add_clicked(self):
        if self.combo_box.currentText() == 'Non-Word':  # update unigram dicrtionary
            selected_word = self.get_word_under_cursor(win.text_box.textCursor())

            if selected_word not in unigram_dict.keys():
                unigram_dict[selected_word] = 1

            elif selected_word in unigram_dict.keys():
                print('word frequency', unigram_dict[selected_word])
                unigram_dict[selected_word] += 1

            win.update_dictionary_list(collections.OrderedDict(sorted(unigram_dict.items())))
            self.showMessagebox(selected_word + ' is added into the unigram dictionary')
            return unigram_dict
        elif self.combo_box.currentText() == 'Real-Word':  # update bigram dictionary
            selected_word = self.get_word_under_cursor(win.text_box.textCursor())  # get the text

            # get the previous word
            pre_cursor = win.text_box.textCursor()
            pre_cursor.movePosition(QTextCursor.PreviousWord)
            pre_cursor.movePosition(QTextCursor.PreviousWord)
            previous_word = self.get_word_under_cursor(pre_cursor)  # get the text of the previous word

            # get the next word
            next_cursor = win.text_box.textCursor()
            next_cursor.movePosition(QTextCursor.NextWord)
            next_word = self.get_word_under_cursor(next_cursor)  # get the text of the next word

            # create tuples to store in bigram dictionary
            first_tuple = (previous_word, selected_word)
            second_tuple = (selected_word, next_word)

            first_found = False
            second_found = False
            # check the tuple exist in bigram_scored_list
            for pair, score in bigram_scored_list:
                if first_tuple == pair:
                    first_found = True
                    if second_found:
                        break
                elif second_tuple == pair:
                    second_found = True
                    if first_found:
                        break

            # if it doesn't exist, add the word to the bigram dictionary
            if not first_found:
                bigram_scored_list.append([first_tuple, 0])  # score is set to 0
            if not second_found:
                bigram_scored_list.append([second_tuple, 0])

            self.showMessagebox(
                str(first_tuple) + " and " + str(second_tuple) + ' are added into the bigram dictionary')
            return bigram_scored_list
        elif self.combo_box.currentText() == 'All':
            self.showMessagebox("Please select 'Non-word' or 'Real-word' from menu bar")

    # get the word under cursor for right click
    def get_word_under_cursor(self, text_cursor):
        # set a first cursor
        text_cursor1 = text_cursor  # set cursor
        text_cursor1.select(QTextCursor.WordUnderCursor)  # select the word under the cursor
        selected_word = text_cursor1.selectedText()  # get the text

        # WordUnderCursor cannot get a word with apostrophe, so check previous/next word and create a word with apostrophe
        # set the second cursor to check after the word
        text_cursor2 = text_cursor
        text_cursor2.movePosition(QTextCursor.WordRight)
        text_cursor2.select(QTextCursor.WordUnderCursor)  # select the word under the cursor
        selected_word2 = text_cursor2.selectedText()  # get the text

        # set the third cursor to check one previous word
        text_cursor3 = text_cursor
        text_cursor3.movePosition(QTextCursor.WordLeft)
        text_cursor3.movePosition(QTextCursor.WordLeft)
        text_cursor3.select(QTextCursor.WordUnderCursor)  # select the word under the cursor
        selected_word3 = text_cursor3.selectedText()  # get the text

        # set the fourth cursor to check two previous word
        text_cursor4 = text_cursor
        text_cursor4.movePosition(QTextCursor.WordLeft)
        text_cursor4.movePosition(QTextCursor.WordLeft)
        text_cursor4.select(QTextCursor.WordUnderCursor)  # select the word under the cursor
        selected_word4 = text_cursor4.selectedText()  # get the text

        if selected_word == "'":  # if cursor is just before the apostrophe
            text_cursor2.movePosition(QTextCursor.WordLeft)
            text_cursor2.movePosition(QTextCursor.WordLeft)
            text_cursor2.select(QTextCursor.WordUnderCursor)
            selected_word2 = text_cursor2.selectedText()
            selected_word = selected_word2 + selected_word + selected_word3  # create a word with apostrophe
        elif selected_word3 == "'":  # if the cursor is before the word
            selected_word = selected_word + selected_word3 + selected_word2  # create a word with apostrophe
        elif selected_word4 == "'":  # if the cursor is after the apostrophe
            text_cursor2.movePosition(QTextCursor.WordLeft)
            text_cursor2.movePosition(QTextCursor.WordLeft)
            text_cursor2.select(QTextCursor.WordUnderCursor)
            selected_word2 = text_cursor2.selectedText()
            selected_word = selected_word2 + selected_word4 + selected_word  # create a word with apostrophe

        return selected_word

    # when right click is clicked, show candidates
    def mousePressEvent(self, QMouseEvent):
        win.text_box.setContextMenuPolicy(Qt.ActionsContextMenu)
        if QMouseEvent.button() == QtCore.Qt.RightButton:  # When right clicked
            selected_word = self.get_word_under_cursor(win.text_box.textCursor())

            # get the previous word for real-word error suggestion
            pre_cursor = win.text_box.textCursor()
            pre_cursor.movePosition(QTextCursor.PreviousWord)
            pre_cursor.movePosition(QTextCursor.PreviousWord)
            previous_word = self.get_word_under_cursor(pre_cursor)  # get the text of the previous word

            # get the next word for real-word error suggestion
            next_cursor = win.text_box.textCursor()
            next_cursor.movePosition(QTextCursor.NextWord)
            next_word = self.get_word_under_cursor(next_cursor)  # get the text of the next word

            first_tuple = (previous_word, selected_word)
            second_tuple = (selected_word, next_word)
            found = False
            temp_list = []

            # if the selected word has candidate, put it in a list & found = true
            for i in candidate_list:
                if i.word == selected_word:
                    if first_tuple == i.error: # real-word
                        temp_list = i.candidates
                        found = True
                        break
                    elif second_tuple == i.error: # real-word
                        temp_list = i.candidates
                        found = True
                        break
                    else: # non-word
                        temp_list = i.candidates
                        found = True
                        break

            if found == True:  # if true, call contextMenu
                win.contextMenu(QMouseEvent, temp_list)

    # creating contextMenu
    def contextMenu(self, event, show_list):
        contextMenu = QMenu(self)  # create new context menu
        for item in show_list:  # add action with the item name
            contextMenu.addAction(str(item))
        contextMenu.exec_(self.mapToGlobal(event.pos()))  # show the context menu


# ******************************************************************
# >>>>>>>>>> Candidate object class -- defining class  <<<<<<<<<<<<<
class Cand_OBJ:
    # initialization
    def __init__(self, a_word, candidate_list, error_tuple):
        self.word = a_word
        self.candidates = candidate_list
        self.error = error_tuple


# **************************************************************************
# >>>>>>>>>> Other functions not under GUI and Cand_OBJ class  <<<<<<<<<<<<<
# import files from specified directory, and create corpus
def import_files(dir_path):
    # get all file names in the 'files_dir' directory
    p = Path(dir_path)
    file_names = list(p.glob("*.txt"))

    # store the txt file contents in file_contents list
    file_contents = []
    for name in file_names:
        temp_file = open(name, "r")
        # in case of 'ascii' error
        file_contents.append(temp_file.read())
        temp_file.close()

    # remove unwanted characters
    corpus = ''
    cleaned_contents = []
    for content in file_contents:
        # remove URLs & email address & Phone numbers
        content = re.sub(r'http\S+', ' ', content)
        content = re.sub(r'www.\S+', ' ', content)
        content = re.sub(r'[\w\.-]+@[\w\.-]+', ' ', content)
        content = re.sub(r'\(?\d{1}\)?[-.\s]\d{3}?[-.\s]\d{3}[-.\s]\d{4}', ' ', content)
        content = re.sub(r'\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}', ' ', content)
        content = re.sub(r'1-877-44U-QUIT|1-800-QUITNOW|1-855-QUITVET', ' ', content)

        # remove numbers (except for noun like B12, HIV-1) & symbols (), <>, *, +, ®, ■ etc...
        content = re.sub(r'[\(\)\<\>\[\]*+®½¼%■▪~|:;?!/∕=”"“°,]', ' ', content)
        content = re.sub(r'[’]', "'", content)
        content = re.sub(r'(\s[-|−]\s)|([-|−]\s)', ' ', content)
        content = re.sub(r'(\s\d+\s)|(\s[-|−]*\d+\.\d+)|(^\d+\s)|(\s\d+/\d+)|(\s\d+[-|−]*\d+\s)|(\s\d+$)', ' ', content)
        content = re.sub(r'(\s\d+\s)|(\s[-|−]*\d+\.\d+)|(^\d+\s)|(\s\d+/\d+)', ' ',
                         content)  # delete extra numbers created after
        content = re.sub(r'(\s\d+\.)', '.', content)

        # remove numbers ending with . or , are replaced with . or , to be able to recognize the end of sentence
        content = re.sub(r'(\s\d+\.)', '.', content)

        # remove extra dots and spaces & line breaks
        content = re.sub(r'\.+', '.', content)
        content = re.sub(r'\s+', ' ', content)
        content = content.replace('\n', ' ').replace('\t', ' ')

        # store in a list
        cleaned_contents.append(content)

        # store in a list
        cleaned_contents.append(content)
        for i in range(len(cleaned_contents)):
            corpus += cleaned_contents[i]

    return corpus


# calculate minimum edit distance
def min_edit_distance(target, source):
    # Create edit distance matrix
    target = '#' + target
    source = '#' + source
    n = len(target)
    m = len(source)
    dmatrix = [[0 for i in range(m)] for j in range(n)]

    # Initialization
    for i in range(0, n):
        dmatrix[i][0] = i

    for j in range(0, m):
        dmatrix[0][j] = j

    # start calculating minimum edit distance
    for i in range(1, n):
        for j in range(1, m):
            if target[i] == source[j]:  # if both characters are the same
                minimum = min((dmatrix[i - 1][j] + 1), (dmatrix[i][j - 1] + 1), (dmatrix[i - 1][j - 1] + 0))
                dmatrix[i][j] = minimum
            elif target[i] != source[j]:  # if both characters are different
                minimum = min((dmatrix[i - 1][j] + 1), (dmatrix[i][j - 1] + 1), (dmatrix[i - 1][j - 1] + 2))
                dmatrix[i][j] = minimum

    return dmatrix[n - 1][m - 1]


# create non-word candidate list based on the minimum edit distance
def create_non_candidate(error_list, dict):
    candidate_list = []

    unigram_dict = dict.copy()
    for word1 in error_list:
        temp_candidates = []
        for word_dic in unigram_dict:
            score = unigram_dict[word_dic]
            if abs(len(word1) - len(word_dic)) <= 2:  # if the difference of length is smaller than 2
                edit_d = min_edit_distance(word1, word_dic)  # calling min_edit_distance function to calc edit distance
                if edit_d > 0 and edit_d <= 3:  # if edit distance is less than 3, put the word in a list as a candidate
                    temp_candidates.append([word_dic, edit_d, score])

        temp_candidates = sorted(temp_candidates, key=itemgetter(1))  # sort by edit distance (smaller first)
        word1_cands = Cand_OBJ(word1, temp_candidates, '')  # create an object with the temp_candidate list
        candidate_list.append(word1_cands)  # add the object to candidate_list

    return candidate_list


# detect real-word errors and create candidates for the errors
def real_word(nonword_error_list):
    # making tuples from input sentences
    input_tokens = tokens_the_word_with_period(win.get_main_text())
    input_tuples = iter(BigramCollocationFinder.from_words(input_tokens).ngram_fd)

    # Find possible real-word errors
    temp_error_list = []
    for tuple in input_tuples:
        found = False
        for pair, score in bigram_scored_list:
            if tuple == pair:  # the tuple exist in the corpus
                if score >= 0:  # and the bigram score is bigger than 0
                    found = True
                    break

        if not found:  # cannot find in bigram = maybe real word error
            temp_error_list.append(tuple)
            try:
                next(input_tuples)
            except StopIteration:
                break

    input_list = list(BigramCollocationFinder.from_words(input_tokens).ngram_fd)
    real_candidate_list = []
    # creating a candidate list by using the idea of trigram
    for index, error in enumerate(temp_error_list):
        first1 = error[1]  # error word
        found = False

        if first1 not in nonword_error_list:
            candidates_bf = []
            candidates_af = []

            try:  # check where it's located in the input tuples
                index = input_list.index(error)
            except ValueError:
                index = -1

            # search tuples in the bigram dictionary based on the idea of trigram to find possible candidates
            if index != -1 and index < len(input_list) - 1:
                bf = input_list[index][0]  # e.g. I of tuple (I, has)
                af = input_list[index + 1][1]  # e.g. a of tuple (has, a)
                for search_word in bigram_scored_list:
                    search_bf = search_word[0][0]
                    search_af = search_word[0][1]
                    # Try to find "search_bf xxx" e.g. if input: "I has a" --> try to find "I something"
                    if bf == search_bf:
                        if abs(len(first1) - len(search_af)) <= 3:  # if the difference of length is smaller than 3
                            edit_d = min_edit_distance(first1, search_af)
                            if edit_d > 0 and edit_d <= 2:  # if edit distance is less than 2, put the word in a list as a candidate
                                candidates_af.append([search_af, edit_d, round(search_word[1], 6)])
                                found = True

                    # Try to find "xxx search_af" e.g. if input: "I has a" --> try to find "something a"
                    if af == search_af:
                        if abs(len(first1) - len(search_bf)) <= 3:  # if the difference of length is smaller than 3
                            edit_d = min_edit_distance(first1, search_bf)
                            if edit_d > 0 and edit_d <= 2:  # if edit distance is less than 2, put the word in a list as a candidate
                                candidates_bf.append([search_bf, edit_d, round(search_word[1], 6)])
                                found = True

                if found:
                    # eliminate duplicated suggestions
                    for set_bf in candidates_bf:
                        for set_af in candidates_af:
                            if set_bf[0] == set_af[0]:
                                if set_bf[2] >= set_af[2]:  # delete smaller bigram score
                                    candidates_af.remove(set_af)
                                elif set_bf[2] < set_af[2]:
                                    candidates_bf.remove(set_bf)

                    # sort by edit distance (smaller first)
                    temp_candidates = sorted(candidates_bf + candidates_af,
                                             key=itemgetter(1))
                    word_cands = Cand_OBJ(first1, temp_candidates,
                                          error)  # create an object with the temp_candidate list
                    real_candidate_list.append(word_cands)  # add the object to candidate_list]

            elif index != -1 and index >= len(input_list) - 1:  # the last word in the input.
                af = '.'
                for search_word in bigram_scored_list:
                    search_bf = search_word[0][0]
                    search_af = search_word[0][1]
                    # Try to find "search_bf xxx" e.g. if input: "I has." --> try to find "I something"
                    if bf == search_bf:
                        if abs(len(first1) - len(search_af)) <= 3:  # if the difference of length is smaller than 3
                            edit_d = min_edit_distance(first1, search_af)
                            if edit_d > 0 and edit_d <= 2:  # if edit distance is less than 2, put the word in a list as a candidate
                                candidates_af.append([search_af, edit_d, round(search_word[1], 6)])
                                found = True
                    # Try to find "xxx search_af" e.g. if input: "I has." --> try to find "something ."
                    if af == search_af:
                        if abs(len(first1) - len(search_bf)) <= 3:  # if the difference of length is smaller than 3
                            edit_d = min_edit_distance(first1, search_bf)
                            if edit_d > 0 and edit_d <= 2:  # if edit distance is less than 2, put the word in a list as a candidate
                                candidates_bf.append([search_bf, edit_d, round(search_word[1], 6)])
                                found = True

                if found:
                    # eliminate duplicates
                    for set_bf in candidates_bf:
                        for set_af in candidates_af:
                            if set_bf[0] == set_af[0]:
                                if set_bf[2] > set_af[2]:  # delete smaller bigram score
                                    candidates_af.remove(set_af)
                                elif set_bf[2] < set_af[2]:
                                    candidates_bf.remove(set_bf)

                    # sort by edit distance (smaller first)
                    temp_candidates = sorted(candidates_bf + candidates_af,
                                             key=itemgetter(1))
                    word_cands = Cand_OBJ(first1, temp_candidates,
                                          error)  # create an object with the temp_candidate list
                    real_candidate_list.append(word_cands)  # add the object to candidate_list]

    for item in real_candidate_list:
        item.candidates.sort(
            key=lambda element: (element[1], -element[2]))  # sort by editdictance, and then probability (in reverse)
        if len(item.candidates) > 10:  # if the candidates are more than 10, chose the first 10.
            item.candidates = item.candidates[:10]

    return real_candidate_list


# check non-word
def check_nonword(sentance):
    tok_sentance = tokens_the_word_without_period(sentance)
    non_word = []
    for word in tok_sentance:
        if word not in unigram_dict:
            non_word.append(word)
    return non_word


# opem unigram file, remember to put the directory path
def open_unigram_file(path2):
    with open(path2, 'rb') as files2:
        unigram_dictionary = json.load(files2)
        sorted_unigram_dictionary = collections.OrderedDict(sorted(unigram_dictionary.items()))

    return sorted_unigram_dictionary


# create top10 candidates based on the edit distance and frequency for non-word errors
def select_top10(error_list, candidate_list):
    for an_error in error_list:
        for item in candidate_list:
            if an_error == item.word:  # if the error has candidate in the candidate list
                item.candidates.sort(key=lambda element: (
                    element[1], -element[2]))  # sort by edit distance, and then frequency (in reverse)
                if len(item.candidates) > 10:  # if the candidates are more than 10, chose the first 10.
                    item.candidates = item.candidates[:10]

    return candidate_list


# tokenized words without any pun
def tokens_the_word_without_period(text):
    return re.findall("\w+['’]t|\w+['’]ll|\w+['’]s|'?\w[\w']*(?:-\w+)*'?", text)


# tokenized words still keep '.', '-', ''s',''ll'
def tokens_the_word_with_period(text):
    return re.findall("\w+['’]t|\w+['’]ll|\w+['’]s|'?\w[\w']*(?:-\w+)*'?|[.]", text)


# count the words
def wordcount(value):
    list = re.findall("\w+['’]t|\w+['’]ll|\w+['’]s|'?\w[\w']*(?:-\w+)*'?", value)
    return len(list)


# this will put the splitted sentence into string
def put_sentence_back_to_string(list):
    text = ''
    for i in range(len(list)):
        text += list[i] + ' '
    return text


# write the string into the text file
def write_the_string_into_file(path, dataset):
    text_file = open(path, "w")
    text_file.write(dataset)
    text_file.close()


# this will put the tokenized word back to a sentence
def put_words_together(dataset):
    data_file = ''
    for i in range(len(dataset)):
        data_file = data_file + dataset[i] + " "
    return data_file


# ******************************************************
# >>>>>>>>>> Main -- Code runs from here  <<<<<<<<<<<<<
if __name__ == '__main__':
    # global candidate_list
    candidate_list = []


    # >>>>>>>>>> Step 1. import all 26 corpuses to python <<<<<<<<<<<<<
    # all 26 corpus have being cleaned and assign to newcontents
    # newcontents = import_file(file_path)

    # tokenize the newcontents with sent_tokenize which will split the string into sentence
    # tok_sentence = sent_tokenize(newcontents)

    # >>>>>>>>>> Step 2. dividing the dataset into three parts <<<<<<<<<<<<<
    # divide the data(sentence) into 60% and 40%
    # train_dataset_sentence, the_rest_of_train_dataset = train_test_split(tok_sentence, train_size=0.6, random_state=1, shuffle=True)
    #  divide the 40%(sentence) into half and half
    # validate_dataset_sentence, test_dataset_sentence = train_test_split(the_rest_of_train_dataset, test_size=0.5, random_state=1, shuffle=True)

    # train_dataset, validate_dataset, and test_dataset are the dataset used to do our research
    # the train_dataset will be tokenized based on words
    # the validate_dataset and test_dataset will be used to write into the text file
    # train dataset word count 695259
    # validate dataset word count 244645
    # test_dataset word count 238785
    # total is about 1178689
    # train_dataset = put_sentence_back_to_string(train_dataset_sentence)
    # validate_dataset = put_sentence_back_to_string(validate_dataset_sentence)
    # test_dataset = put_sentence_back_to_string(test_dataset_sentence)

    # >>>>>>>>>> Step 3. write the data to a text file <<<<<<<<<<<<<
    # write dataset into text files
    # write_the_string_into_file(train_data_path, train_dataset)
    # write_the_string_into_file(validate_data_path, validate_dataset)
    # write_the_string_into_file(test_data_path, test_dataset)

    # >>>>>>>>>> Step 4. construct the dictionary based on the train_dataset <<<<<<<<<<<<<
    # tokenize the train_dataset withoout period for building the dictionary
    # tok_train_dataset = tokens_the_word_without_period(train_dataset)
    # in the train dataset, Counter will calculate the frequency of the words
    # dictionary = Counter(tok_train_dataset)
    # write the dictrionary into text file
    # write_the_string_into_file(unigram_dic_path,str(dictionary))

    # >>>>>>>>>> Step 5. To make it faster, it imports corpus and dictionaries from txt files created above <<<<<<<<<<<<<
    # read training corpus
    path = '/train_data.txt'
    training_corpus = open(path, "r").read()

    # create bigram dictionary
    corpus = tokens_the_word_with_period(training_corpus)
    finder = BigramCollocationFinder.from_words(corpus)
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    bigram_scored_list = finder.score_ngrams(bigram_measures.raw_freq)
    bigram_scored_list.sort()

    # create GUI app
    app = QApplication(sys.argv)
    win = GUI()
    win.show()

    # set unigram dictionary & update dictionary list
    unigram_path = '/unigram_dict_validate_train.txt'
    unigram_dict = open_unigram_file(unigram_path)
    win.update_dictionary_list(unigram_dict)

    sys.exit(app.exec_())
