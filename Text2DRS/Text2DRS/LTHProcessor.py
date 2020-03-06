from config import LTH_HOST
import FilePaths
import logging
from nltk import corpus
from nltk import tokenize
import os
from queue import Queue
import requests
import sys
from time import time
from threading import Thread
import xml.etree.ElementTree as eT

v3 = corpus.util.LazyCorpusLoader(
    'verbnet3', corpus.reader.verbnet.VerbnetCorpusReader,
    r'(?!\.).*\.xml')

module_logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS')
module_logger.setLevel(level=logging.WARNING)

NOUN_POS_TAGS = ['NNP', 'NN', 'PRP', 'NNS']
PROPOSITION_POS_TAGS = ['IN', 'TO']
VERB_POS_TAGS = ['VBD', 'VB', 'VBN', 'VBG', 'VBP']
PB_TREE = eT.parse(FilePaths.VNPB_MAPPINGS)


class LTHProcessor:
    def __init__(self, input_text: str, input_name: str):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of LTHProcessor.')

        self.input_text = input_text
        self.input_name = input_name
        self.output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / self.input_name
        self.file_generator_verbnet_srl = FileGeneratorVerbNetSRL()
        self.LTH_Text = LTHTextData()

    def process_lth(self):
        """
        To generate LTH processing:
        1) Run LTH Preprocessing.
        2) Run LTH Processing.
        3) Read LTH Output.
        4) Form LTH Text Data from output.
        5) Write LTH Text Dat to file.
        :return:
        """
        self.logger.info(f'Generating LTH Data.')
        ts = time()
        lth_output = self._get_existing_lth_output()
        if not lth_output:
            sentences = self._get_tokenized_sentences()
            lth_output = self._execute_lth_processing(sentences)
        lth_sentences_list = self._generate_lth_sentence_list(lth_output)
        self._form_lth_text_data(lth_sentences_list)
        self.file_generator_verbnet_srl.write_srl_output(self.input_name, self.LTH_Text.lth_text_data)
        te = time()
        self.logger.debug(f'LTH Text is {self.LTH_Text}.')
        self.logger.warning(f'Processing LTH took {te-ts}')

    def _get_lth_output_file_path(self):
        lth_output_file_name = f'lth_{self.input_name}.txt'
        return self.output_dir / lth_output_file_name

    def _get_existing_lth_output(self):
        lth_output_file = self._get_lth_output_file_path()
        output = None
        if lth_output_file.exists() and os.path.getsize(lth_output_file.__str__()) > 0:
            with open(lth_output_file, 'r') as lth_file:
                lth_file_content = lth_file.read()
                output = lth_file_content.split('\n\n')
        return output

    def _get_tokenized_sentences(self):
        sentences = tokenize.sent_tokenize(self.input_text)
        return sentences

    def _execute_lth_processing(self, sentences):
        """
        This method calls and runs the process function in the lth tool with a given
        input file from the lth tool's directory.
        :return:
        """
        self.logger.info(f'Executing LTH Processing.')

        lth_output = [str() for s in sentences]

        q = Queue(maxsize=0)  # Create thread queue
        self._populate_request_queue(q, sentences)

        num_threads = min(10, len(sentences))  # Cap threads at 10.
        for i in range(num_threads):
            self.logger.info(f'Starting thread {i}')
            worker = Thread(target=self._lth_request, args=(q, lth_output))
            worker.setDaemon(True)
            worker.start()
        q.join()

        self._write_lth_output(lth_output)
        return lth_output

    def _lth_request(self, q, result):
        self.logger.info(f'LTH Request.')
        while not q.empty():
            work = q.get()
            try:
                lth_response = requests.post(LTH_HOST, work[1])
                result[work[0]] = lth_response.text
            except:
                self.logger.error("Error with URL check.")
                result[work[0]] = str()
            q.task_done()
        return True

    def _populate_request_queue(self, q: Queue, sentences: list):
        self.logger.info(f'Populate Request Queue')
        for i in range(len(sentences)):  # Add index and post data in each queue item
            q.put((i, {
                "sentence": sentences[i],
                "returnType": "text"
                }))

    def _write_lth_output(self, lth_output):
        self.logger.info(f'Write LTH Output.')
        with open(self._get_lth_output_file_path(), 'w') as output:
            output.write('\n\n'.join(lth_output))

    def _generate_lth_sentence_list(self, lth_output):
        self.logger.info(f'Generating LTH Sentence List.')
        try:
            lth_output_lines = [line.split('\n') for line in lth_output]
            sentences_lst = list()
            for sent in lth_output_lines:
                items = [line.split('\t') for line in sent]
                sentences_lst.append(items)
            self.logger.debug(f'Sentence List: {sentences_lst}.')
            return sentences_lst
        except IOError as e:
            self.logger.exception(f"I/O error({e.errno}): {e.strerror}")
            sys.exit()

    def _form_lth_text_data(self, lth_sentences_list):
        """
        A method to form each sentence's data into a dictionary.
        :param lth_sentences_list:
        :return:
        """
        self.logger.info(f'Form LTH Text Data with {lth_sentences_list}.')

        for sentence in lth_sentences_list:
            self.logger.debug(f'Sentence is {sentence}.')
            lth_sentence_data = LTHSentenceData()

            pred_list = [item[13] for item in sentence if item[13] != '_']
            self.logger.debug(f'Pred List is: {pred_list}.')

            for item in sentence:
                word_id = item[0]
                form = item[1]
                plemma = item[3]
                ppos = item[5]
                phead = item[9]
                pdeprel = item[11]
                pred = item[13]
                lth_word_data = LTHWordData(word_id, form, plemma, ppos, phead, pdeprel, pred)

                idx = 14
                for pred in pred_list:
                    self.logger.debug(f'Pred is: {pred}.')
                    lth_word_data.set_arg(pred, item[idx].strip())
                    if idx != 13 + len(pred_list):
                        self.logger.debug(f'If idx is: {idx}.')
                        idx += 1

                self.logger.debug(f'LTH Word Data: {lth_word_data}')
                lth_sentence_data.add_lth_word(lth_word_data)

            self.logger.debug(f'LTH Sentence Data: {lth_sentence_data}')
            self.LTH_Text.add_lth_sentence(lth_sentence_data)

        self._pre_check_args()
        self._deep_process()
        self._remove_not_vbclass()

    def _pre_check_args(self):
        self.logger.info(f'Pre Check Args.')
        for LTH_Sentence in self.LTH_Text.lth_text_data:
            pred_list = LTH_Sentence.get_predicates()
            self.logger.debug(f'Pre Check Args - Pred List is: {pred_list}.')
            for pred in pred_list:
                reassign_lst = list()
                for LTH_Word in LTH_Sentence.lth_sentence_data:
                    if LTH_Word.PPOS in PROPOSITION_POS_TAGS and LTH_Word.Args[pred] != '_':
                        t = (LTH_Word.ID, LTH_Word.PHead, LTH_Word.Args[pred])
                        reassign_lst.append(t)
                        LTH_Word.set_arg(pred, '_')

                for LTH_Word in LTH_Sentence.lth_sentence_data:
                    for role in reassign_lst:
                        if LTH_Word.PPOS in NOUN_POS_TAGS and \
                                LTH_Word.Args[pred] == '_' and \
                                int(LTH_Word.ID) > int(role[0]) and \
                                int(LTH_Word.PHead) > int(role[1]):
                                LTH_Word.set_arg(pred, role[2])

    def _deep_process(self):
        """
        A method to process a list of dictionary and add vn-pb's values
        :return:
        """
        self.logger.info(f'Deep Process.')
        for LTH_Sentence in self.LTH_Text.lth_text_data:
            pred_list = LTH_Sentence.get_predicates()
            for pred in pred_list:
                verbnet_themeroles = self._get_themeroles(LTH_Sentence.lth_sentence_data, pred)
                verbnet_classes = list(verbnet_themeroles.keys())
                self.logger.debug(f'VerbNet Classes: {verbnet_classes}.')
                if len(verbnet_classes) > 0:
                    for LTH_Word in LTH_Sentence.lth_sentence_data:
                        if LTH_Word.Pred == pred:
                            LTH_Word.set_vn_class(pred, verbnet_classes)
                        elif LTH_Word.Args[pred] != '_':
                            roles = list()
                            for verbnet_class in verbnet_classes:
                                self.logger.debug(f'VerbNet Class: {verbnet_class}.')
                                for verbnet_themerole in verbnet_themeroles.get(verbnet_class):
                                    self.logger.debug(f'VerbNet Theme Role: {verbnet_themerole}.')
                                    r_num = LTH_Word.Args[pred][1:]
                                    self.logger.debug(f'R Num: {r_num}.')
                                    if r_num in list(verbnet_themerole.keys()):
                                        roles.append([verbnet_class, verbnet_themerole.get(r_num)])
                                        break
                                if len(roles) == 0:
                                    roles.append([verbnet_class, 'NONE-THEMEROLE'])
                            LTH_Word.set_vn_class(pred, roles)
                        else:
                            LTH_Word.set_vn_class(pred, '_')

    def _get_themeroles(self, lth_sentence_data, pred):
        self.logger.info(f'Get Theme Roles.')
        vn_themeroles = dict()
        for LTH_Word in lth_sentence_data:
            if LTH_Word.Pred == pred and LTH_Word.PPOS in VERB_POS_TAGS:
                plemma = LTH_Word.PLemma
                vn_themeroles = self._vn_pb_parser(pred, plemma)
                break
        self.logger.debug(f'VerbNet Theme Roles: {vn_themeroles}.')
        return vn_themeroles

    def _remove_not_vbclass(self):
        self.logger.info(f'Remove not vb class.')
        for LTH_Sentence in self.LTH_Text.lth_text_data:
            predicates = LTH_Sentence.get_predicates()
            remove_lst = list()
            for LTH_Word in LTH_Sentence.lth_sentence_data:
                if LTH_Word.Pred in predicates and LTH_Word.PPOS not in VERB_POS_TAGS:
                    remove_lst.append(LTH_Word.Pred)
                    LTH_Word.Pred = '_'

            for pred in remove_lst:
                for LTH_Word in LTH_Sentence.lth_sentence_data:
                    del LTH_Word.Args[pred]

    def _vn_pb_parser(self, pred, plemma):
        """
        A method to retrieve vn class data and args role data from vn-pb element tree
        using pred and plemma to located pb parent node in the tree,
        retrieve vn-class data and pb-roleset data from parent node to children node.
        :param pred:
        :param plemma:
        :return:
        """
        self.logger.info(f'VN PB Parser with pred {pred} and plemma {plemma}.')
        dct = dict()
        root = PB_TREE.getroot()
        path = ".//*[@lemma='{}']".format(plemma)
        elem = root.find(path)
        if elem is not None:
            for argmap in elem:
                if argmap.attrib.get('pb-roleset') == pred:
                    vn_class_id = argmap.attrib.get('vn-class')
                    self.logger.debug(f'VN Class ID is: {vn_class_id}.')
                    verbnet_class = VerbNetClass(vn_class_id)
                    self.logger.debug(f'VN Thematic Role keys are: {verbnet_class.VerbNetThematicRoles.keys()}.')
                    self.logger.debug(f'VN Thematic Role values are: {verbnet_class.VerbNetThematicRoles.values()}.')
                    self.logger.debug(f'VN Class is: {verbnet_class}.')
                    lst = list()
                    for role in argmap:
                        sub_dct2 = dict()
                        pb_arg = role.attrib.get('pb-arg')
                        vn_thematic_role = role.attrib.get('vn-theta')
                        self.logger.debug(f'VN thematic role: {vn_thematic_role}.')
                        sub_dct2[pb_arg] = verbnet_class.VerbNetThematicRoles[vn_thematic_role]
                        lst.append(sub_dct2)

                    dct[verbnet_class.VerbNetName] = lst

        if len(dct.keys()) == 0:
            dct['NOT-FOUND-IN-SEMLINK'] = list()

        return dct


class LTHWordData:
    def __init__(self, word_id, form, plemma, ppos, phead, pdeprel, pred):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.LthWordData')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of LthWordData.')
        
        self.ID = word_id
        self.Form = form
        self.PLemma = plemma
        self.PPOS = ppos
        self.PHead = phead
        self.PDeprel = pdeprel
        self.Pred = pred
        self.Args = dict()
        self.VN_Class = dict()

    def set_arg(self, pred, value):
        self.Args[pred] = value

    def set_vn_class(self, pred, vn_class):
        self.VN_Class[pred] = vn_class

    def __str__(self):
        return f'ID: {self.ID}\n' + \
               f'Form: {self.Form}\n' + \
               f'PLemma: {self.PLemma}\n' + \
               f'PPOS: {self.PPOS}\n' + \
               f'PHead: {self.PHead}\n' + \
               f'PDeprel: {self.PDeprel}\n' + \
               f'Pred: {self.Pred}\n' + \
               f'Args: {self.Args}\n' + \
               f'VN Class: {self.VN_Class}\n'


class LTHSentenceData:
    def __init__(self):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.LTHSentenceData')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of LTHSentenceData.')

        self.lth_sentence_data = list()

    def add_lth_word(self, lth_word_data: LTHWordData):
        self.lth_sentence_data.append(lth_word_data)

    def get_predicates(self):
        return [lth_word_data.Pred for lth_word_data in self.lth_sentence_data if lth_word_data.Pred != '_']

    def __str__(self):
        return ' '.join([data.__str__() for data in self.lth_sentence_data])


class LTHTextData:
    def __init__(self):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.LTHTextData')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of LTHTextData.')

        self.lth_text_data = list()

    def add_lth_sentence(self, lth_sentence_data: LTHSentenceData):
        self.lth_text_data.append(lth_sentence_data)

    def __str__(self):
        return "\n".join([data.__str__() for data in self.lth_text_data])


class FileGeneratorVerbNetSRL:
    def __init__(self):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.FileGeneratorVerbNetSRL')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of FileGeneratorVerbNetSRL.')

    def write_srl_output(self, file_name, lth_text_data):
        self.logger.info(f'Writing VerbNet SRL Output for {file_name}.')
        srl_output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / file_name
        if not srl_output_dir.is_dir():
            srl_output_dir.mkdir()
        text2drs_verbnet_srl_output_path = srl_output_dir / f'{file_name}_verbNetsrl.txt'

        with open(text2drs_verbnet_srl_output_path, 'w') as text2drs_verbnet_srl_output_file:
            for index, LTH_sentence in enumerate(lth_text_data):
                for LTH_word in LTH_sentence.lth_sentence_data:
                    if LTH_word.ID == '1':
                        text2drs_verbnet_srl_output_file.write(f'\nSENTENCE {index + 1}:\n')
                    self.logger.debug(f'LTH Word Data is: {LTH_word}.')
                    text2drs_verbnet_srl_output_file.write(LTH_word.__str__())
                    text2drs_verbnet_srl_output_file.write('\n')


class VerbNetSelectionalRestriction:
    def __init__(self, value: str, name: str):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.VerbNetSelectionalRestriction')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of VerbNetSelectionalRestriction {value} {name}.')

        self.value = value
        self.name = name

    def __str__(self):
        return self.value + '' + self.name


class VerbNetThematicRole:
    def __init__(self, type_name: str):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.VerbNetThematicRole')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of VerbNetThematicRole {type_name}.')

        self.type = type_name
        self.modifiers = []

    def add_selectional_restriction(self, modifier: VerbNetSelectionalRestriction):
        self.modifiers.append(modifier)

    def __str__(self):
        return self.type + \
               ' ' + \
               ' '.join([m.__str__() for m in self.modifiers])


class VerbNetClass:
    def __init__(self, verbnet_id: str):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.LTHProcessor.VerbNetClass')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of VerbNetClass {verbnet_id}.')

        self.VerbNetID = verbnet_id
        self.ParentVerbNetIDs = list()
        self.VerbNetName = ''
        self.VerbNetThematicRoles = {}

        self._set_parent_verbnet_ids()
        self._set_verbnet_name()
        self._set_verbnet_thematic_roles()
        
        self.logger.debug(f'Parent VerbNet IDs are: {self.ParentVerbNetIDs}.')
        self.logger.debug(f'VerbNet Name is: {self.VerbNetName}.')
        self.logger.debug(f'VerbNet Thematic Roles are: {self.VerbNetThematicRoles}.')

    def _set_parent_verbnet_ids(self):
        if self.VerbNetID.__contains__('-'):
            split_name = self.VerbNetID.split('-')
            parent_name = split_name[0]
            for i, name in enumerate(split_name):
                if i != len(split_name) - 1:
                    if i != 0:
                        parent_name = parent_name + '-' + name
                    self.ParentVerbNetIDs.append(parent_name)

    def _set_verbnet_name(self):
        try:
            self.VerbNetName = v3.longid(self.VerbNetID)
        except ValueError as e:
            self.logger.warning(f'Set_Verbnet_Name: Unexpected error: {e.__str__()} in VerbNet.')
            exit(0)

    def _set_verbnet_thematic_roles(self):
        roles = list()
        try:
            roles = v3.themroles(self.VerbNetID)
        except ValueError as e:
            self.logger.warning(f'Unexpected error setting thematic roles: {e.__str__()} in VerbNet.')

        if self.ParentVerbNetIDs:
            parent_roles = self._get_parent_thematic_roles()
            roles = roles + parent_roles
            
        self.logger.debug(f'Roles: {roles.__str__()}.')
        self.VerbNetThematicRoles = self._create_thematic_role_dictionary(roles)

    def _get_parent_thematic_roles(self):
        parent_roles = list()
        for parent_ID in self.ParentVerbNetIDs:
            try:
                parent_roles += v3.themroles(parent_ID)
            except ValueError as e:
                self.logger.warning(f'Unexpected error getting parent thematic roles: {e.__str__()} in VerbNet.')
        self.logger.info(f'Parent Roles for {self.VerbNetID}: {parent_roles.__str__()}.')
        return parent_roles

    def _create_thematic_role_dictionary(self, roles):
        self.logger.info(f'Create thematic role dictionary {roles}.')
        role_dictionary = {}
        for role in roles:
            self.logger.debug(f'Role: {role}.')
            role_name = role['type']
            self.logger.debug(f'Role Name: {role_name}.')
            if role_name not in role_dictionary:
                thematic_role = VerbNetThematicRole(role_name)
                self.logger.debug(f'Thematic Role: {thematic_role}.')
                modifiers = role['modifiers']
                self.logger.debug(f'Modifiers: {modifiers}.')
                for modifier in modifiers:
                    value = modifier['value']
                    self.logger.debug(f'Value: {value}.')
                    name = modifier['type']
                    self.logger.debug(f'Name: {name}.')
                    thematic_role.add_selectional_restriction(VerbNetSelectionalRestriction(value, name))
                role_dictionary[role_name] = thematic_role
        return role_dictionary

    def __str__(self):
        return self.VerbNetName + ' ' + \
               self.VerbNetID + ' ' + \
               ' ' .join([role.__str__() for role in self.VerbNetThematicRoles])
