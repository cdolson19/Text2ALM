# MIT License
#
# Copyright (c) [2018] [Gang Ling (gling@unomaha.edu),
#                      Yuliya Lierler (ylierler@unomaha.edu)]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import FilePaths
import logging
import pprint
from time import time
from threading import Thread
import Text2DRS.Text2DRS.CoreNLPProcessor as corenlpProcessor
import Text2DRS.Text2DRS.LTHProcessor as lthProcessor

module_logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS')
module_logger.setLevel(level=logging.WARNING)

VERB_POS_LIST = ['VBD', 'VB', 'VBN', 'VBG', 'VBP']
NOUN_POS_LIST = ['NNP', 'NN', 'PRP', 'NNS']

WIDTH = 80


class Text2DRS:
    def __init__(self,input_text: str, input_name: str):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.Text2DRS')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of Text2DRS.')
        self.input_name = input_name
        self.input_text = input_text
        self.file_generator_drs = FileGeneratorDRS()

    def execute_text2drs(self):
        self.logger.info(f'Execute Text2DRS.')
        ts = time()

        # Process input narrative file using LTH system
        lth_processor = lthProcessor.LTHProcessor(self.input_text, self.input_name)
        corenlp_processor = corenlpProcessor.CoreNLPProcessor(self.input_text, self.input_name)

        p1 = Thread(target=lth_processor.process_lth)
        p1.start()

        p2 = Thread(target=corenlp_processor.process_corenlp)
        p2.start()

        p1.join()
        p2.join()

        drs_model = DRSModel(lth_processor.LTH_Text.lth_text_data, corenlp_processor.coref_dict)
        self.file_generator_drs.write_text2drs_output(self.input_name, drs_model.DRS_Dict)

        te = time()
        self.logger.warning(f'{self.input_name} Total Time: {te - ts}')
        return drs_model


class DRSModel:
    def __init__(self, lth_text_data: list, coref_dictionary):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.DRSModel')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of DRSModel.')
        self.logger.debug(f'Coref Dict: {coref_dictionary}')

        self.DRS_Dict = dict()

        self.Entity_Dict = self._form_entity_dict(lth_text_data, coref_dictionary)
        self.Entity_Property = [(ref, ent) for ref, ent in self.Entity_Dict.items()]
        (self.Events_Dict, self.Event_Property) = self._retrieve_events(lth_text_data)
        self.Event_Type = self._retrieve_event_types(lth_text_data)
        self.Event_Time = self._retrieve_event_times()
        self.Event_Argument_Role = self._retrieve_event_argument_roles(lth_text_data)
        self.Event_Argument_Selection_Restriction = self._retrieve_event_argument_selection_restrictions(lth_text_data)
        self.Event_PDepRel = self._retrieve_event_pdeprel(lth_text_data)

        self.DRS_Dict['entity'] = [ref for ref in self.Entity_Dict.keys()]  # [r1, r2, r3 ... ]
        self.DRS_Dict['property'] = [(ref, ent) for ref, ent in self.Entity_Dict.items()]  # [ (r1, John), (r2, Mary) ... ]
        self.DRS_Dict['event'] = [k for k in self.Events_Dict.keys()]  # [ e1, e2, e3 ... ]
        self.DRS_Dict['eventType'] = self.Event_Type  # [ (e1, "run-51.3.2"), (e2, "run-51.3.2") ... ]
        self.DRS_Dict['eventTime'] = self.Event_Time  # [ (e1, "2"), (e2, "1") ... ]
        self.DRS_Dict['eventArgumentRole'] = self.Event_Argument_Role  # [ (e1, "Theme", r1), (e1, "Location", r2) ... ]
        self.DRS_Dict['eventArgumentSelectionRestriction'] = self.Event_Argument_Selection_Restriction  # [ (e1, "+animate", r1), (e1, "+machine", r1) ... ]
        self.DRS_Dict['eventPDependencyRelation'] = self.Event_PDepRel  # [ (e1, "PMOD", r1), (e1, "SBJ", r2) ... ]

    def _get_omit_entities(self, coref_dictionary):
        self.logger.info(f'Getting omit entities.')
        special = "\'s"
        omit_list = list()
        for key, value in coref_dictionary.items():
            if ' ' in key and special not in key:
                entity = key.split(' ')[-1]
                for v in value[1:]:
                    omit_list.append((entity, v))
            else:
                for v in value[1:]:
                    omit_list.append((key, v))
        self.logger.debug(f'Omit List: {omit_list}')
        return omit_list

    def _get_entity_list(self, lth_text_data):
        self.logger.info(f'Getting all entities.')

        entities = list()
        for index, LTH_sentence in enumerate(lth_text_data):
            for LTH_word in LTH_sentence.lth_sentence_data:
                if LTH_word.PPOS in NOUN_POS_LIST and LTH_word.Form not in entities:
                    entities.append(LTH_word.Form)
        self.logger.debug(f'Entities: {entities}.')
        return entities

    def _get_pdeprel_list(self, lth_text_data):
        self.logger.info(f'Getting all P Dependency Relations.')

        entities = list()
        for index, LTH_sentence in enumerate(lth_text_data):
            for LTH_word in LTH_sentence.lth_sentence_data:
                if LTH_word.PPOS in NOUN_POS_LIST and LTH_word.Form not in entities:
                    entities.append(LTH_word.Form)
        self.logger.debug(f'Entities: {entities}.')
        return entities

    def _form_entity_dict(self, lth_text_data, coref_dictionary):
        self.logger.info(f'Forming Entity Dict.')
        entities = dict()
        entity_list = self._get_entity_list(lth_text_data)

        for index, entity in enumerate(entity_list):
            entities['r' + str(index + 1)] = entity
        self.logger.debug(f'Entity Dict: {entities}.')
        return entities

    def _retrieve_events(self, lth_text_data):
        self.logger.info(f'Retrieve event.')
        events_dict = dict()
        events_property = dict()
        count = 1
        for index, LTH_sentence in enumerate(lth_text_data):
            verb = list()
            for LTH_word in LTH_sentence.lth_sentence_data:
                if LTH_word.Pred != '_' and LTH_word.PPOS in VERB_POS_LIST:
                    events_dict['e' + str(count)] = LTH_word.PLemma
                    verb.append((LTH_word.PLemma, 'e' + str(count)))
                    count += 1
            events_property[index + 1] = verb
        return events_dict, events_property

    # include picking first vn-class if multiple returns
    def _retrieve_event_types(self, lth_text_data):
        self.logger.info(f'Retrieve event type.')
        event_type_list = []
        count = 1
        for LTH_sentence in lth_text_data:
            for LTH_word in LTH_sentence.lth_sentence_data:
                if LTH_word.PPOS in VERB_POS_LIST:
                    pred = LTH_word.Pred
                    if pred in LTH_word.VN_Class:
                        event_type_list.append(('e' + str(count), LTH_word.VN_Class[pred][0]))
                        count += 1
        return event_type_list

    def _retrieve_event_times(self):
        self.logger.info(f'Retrieve event time.')
        event_time_list = []
        for index, (event, value) in enumerate(self.Events_Dict.items()):
            event_time_list.append((event, index))
        return event_time_list

    def _retrieve_event_argument_roles(self, lth_text_data):
        self.logger.info(f'Retrieve event argument role with lth_text_data: {lth_text_data}\n')
        event_argument_role_list = list()
        event_types = self.Event_Type
        for index, LTH_sentence in enumerate(lth_text_data):
            self.logger.debug(f'LTH Sentence Data: {LTH_sentence}.')
            predicates = LTH_sentence.get_predicates()
            self.logger.debug(f'Predicates: {predicates}.')
            self.logger.debug(f'Self Event Type: {self.Event_Type}.')
            events = event_types[0:len(predicates)]
            event_types = event_types[len(predicates):]
            self.logger.debug(f'Events: {events}')
            for (pred, event) in zip(predicates, events):
                self.logger.debug(f'Pred: {pred} & Event: {event}.')
                event_ref = event[0]
                self.logger.debug(f'Event Ref: {event_ref}.')
                for LTH_word in LTH_sentence.lth_sentence_data:
                    self.logger.debug(f'LTH Word: {LTH_word}.')
                    if LTH_word.Args[pred] != '_':
                        self.logger.debug(f'Sentence pred: {[data.__str__() for data in LTH_word.VN_Class[pred]]}.')
                        # use first verb class as vn class
                        vn_role = LTH_word.VN_Class[pred][0][1]
                        self.logger.debug(f'VN Role: {vn_role}')
                        self.logger.debug(f'VN Role Type: {type(vn_role)}')
                        if LTH_word.PPOS in NOUN_POS_LIST:
                            ref = self._get_referent_from_entity(LTH_word.Form)
                            if ref:
                                if vn_role == 'NONE-THEMEROLE':
                                    event_argument_role_list.append(
                                        (event_ref, vn_role, ref))
                                else:
                                    event_argument_role_list.append(
                                        (event_ref, vn_role.type, ref))
                        elif LTH_word.PPOS in VERB_POS_LIST:
                            verb_property = self.Event_Property.get(index + 1)
                            for (plemma, eref) in verb_property:
                                if LTH_word.PLemma == plemma:
                                    event_argument_role_list.append(
                                        (event_ref, vn_role.type, eref))
        return event_argument_role_list

    def _retrieve_event_pdeprel(self, lth_text_data):
        self.logger.info(f'Retrieve event PDEPREL with lth_text_data: {lth_text_data}\n')
        event_pdeprel_list = list()
        event_types = self.Event_Type
        for index, LTH_sentence in enumerate(lth_text_data):
            self.logger.debug(f'LTH Sentence Data: {LTH_sentence}.')
            predicates = LTH_sentence.get_predicates()
            self.logger.debug(f'Predicates: {predicates}.')
            self.logger.debug(f'Self Event Type: {self.Event_Type}.')
            events = event_types[0:len(predicates)]
            event_types = event_types[len(predicates):]
            self.logger.debug(f'Events: {events}')
            for (pred, event) in zip(predicates, events):
                self.logger.debug(f'Pred: {pred} & Event: {event}.')
                event_ref = event[0]
                self.logger.debug(f'Event Ref: {event_ref}.')
                for LTH_word in LTH_sentence.lth_sentence_data:
                    self.logger.debug(f'LTH Word: {LTH_word}.')
                    if LTH_word.Args[pred] != '_':
                        # use first verb class as vn class
                        self.logger.debug(f'Sentence pred: {[data.__str__() for data in LTH_word.VN_Class[pred]]}.')
                        pdeprel = LTH_word.PDeprel
                        self.logger.debug(f'PDEPREL: {pdeprel}')
                        if LTH_word.PPOS in NOUN_POS_LIST:
                            ref = self._get_referent_from_entity(LTH_word.Form)
                            event_pdeprel_list.append((event_ref, pdeprel, ref))
                        elif LTH_word.PPOS in VERB_POS_LIST:
                            verb_property = self.Event_Property.get(index + 1)
                            for (plemma, eref) in verb_property:
                                if LTH_word.PLemma == plemma:
                                    event_pdeprel_list.append((event_ref, pdeprel, eref))
        return event_pdeprel_list

    def _retrieve_event_argument_selection_restrictions(self, lth_text_data):
        self.logger.info(f'Retrieve event argument selection restriction with lth_text_data: {lth_text_data}\n')
        event_argument_selection_restriction_list = list()
        event_types = self.Event_Type
        for index, LTH_sentence in enumerate(lth_text_data):
            self.logger.debug(f'LTH Sentence Data: {LTH_sentence}.')
            predicates = LTH_sentence.get_predicates()
            self.logger.debug(f'Predicates: {predicates}.')
            self.logger.debug(f'Self Event Type: {self.Event_Type}.')
            events = event_types[0:len(predicates)]
            event_types = event_types[len(predicates):]
            self.logger.debug(f'Events: {events}')
            for (pred, event) in zip(predicates, events):
                self.logger.debug(f'Pred: {pred} & Event: {event}.')
                event_ref = event[0]
                self.logger.debug(f'Event Ref: {event_ref}.')
                for LTH_word in LTH_sentence.lth_sentence_data:
                    self.logger.debug(f'LTH Word: {LTH_word}.')
                    if LTH_word.Args[pred] != '_':
                        # use first verb class as vn class
                        self.logger.debug(f'Sentence pred: {[data.__str__() for data in LTH_word.VN_Class[pred]]}.')
                        vn_role = LTH_word.VN_Class[pred][0][1]
                        self.logger.debug(f'VN Role: {vn_role}')
                        self.logger.debug(f'VN Role Type: {type(vn_role)}')
                        if LTH_word.PPOS in NOUN_POS_LIST:
                            ref = self._get_referent_from_entity(LTH_word.Form)
                            if ref and vn_role != 'NONE-THEMEROLE':
                                for modifier in vn_role.modifiers:
                                    event_argument_selection_restriction_list.append(
                                        (event_ref, modifier.__str__(), ref))
                        elif LTH_word.PPOS in VERB_POS_LIST:
                            verb_property = self.Event_Property.get(index + 1)
                            for (plemma, eref) in verb_property:
                                if LTH_word.PLemma == plemma:
                                    for modifier in vn_role.modifiers:
                                        event_argument_selection_restriction_list.append(
                                            (event_ref, modifier.__str__(), eref))
        return event_argument_selection_restriction_list

    def _get_referent_from_entity(self, form):
        for ref, ent in self.Entity_Dict.items():
            if ent == form:
                return ref
        return None

    def __str__(self):
        return pprint.pformat(self.DRS_Dict)


class FileGeneratorDRS:
    def __init__(self):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.FileGeneratorDRS')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of FileGeneratorDRS.')

    def write_text2drs_output(self, input_file_name: str, drs_dict: dict):
        drs_output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / input_file_name
        if not drs_output_dir.is_dir():
            drs_output_dir.mkdir()
        text2drs_drs_output_path = drs_output_dir / f'{input_file_name}_drs.txt'
        self.logger.info(f'Writing DRS Output to {text2drs_drs_output_path}.')

        with open(text2drs_drs_output_path, 'w') as text2drs_drs_output_file:
            self._write_drs_to_asp(drs_dict, text2drs_drs_output_file)

    def _write_drs_to_asp(self, drs_dict: dict, text2drs_drs_output_file):
        """
        Print DRS in ASP format.
        :param drs_dict:
        :param text2drs_drs_output_file:
        :return:
        """
        self.logger.info(f'Write DRS to ASP.')
        self._write_drs_to_asp_header(drs_dict, text2drs_drs_output_file)

        key_list = [k for k in drs_dict.keys()]
        for key in key_list:
            items = drs_dict[key]
            if key == 'entity' or key == 'event':
                self._write_drs_to_asp_entity_or_event(items, key, text2drs_drs_output_file)
            elif key == 'eventArgumentRole' or key == 'eventPDependencyRelation':
                self._write_drs_to_asp_event_arg_role_or_sel_restr(items, key, text2drs_drs_output_file)
            elif key == 'eventArgumentSelectionRestriction':
                continue
            else:
                self._write_drs_to_asp_generic_data(items, key, text2drs_drs_output_file)

    def _write_drs_to_asp_header(self, drs_dict: dict, text2drs_drs_output_file):
        self.logger.info(f'Write DRS to ASP Header.')
        header_string = f'\n% {", ".join(drs_dict["entity"])}, {", ".join(drs_dict["event"])}'
        header_string += f'\n% {"==" * 30}\n'
        self.logger.debug(f'Header string: {header_string}.')
        text2drs_drs_output_file.write(header_string)

    def _write_drs_to_asp_entity_or_event(self, items, key, text2drs_drs_output_file):
        self.logger.info(f'Write DRS to ASP Entity or Event.')
        drs_string = str()
        for index, i in enumerate(items):
            if index % 3 == 0:
                drs_string += '\n'
            drs_string += f'{key.__str__()}({i.__str__()}). '
        self.logger.debug(f'Entity or Event string: {drs_string}.')
        text2drs_drs_output_file.write(drs_string + '\n')

    def _write_drs_to_asp_event_arg_role_or_sel_restr(self, items, key, text2drs_drs_output_file):
        self.logger.info(f'Write DRS to ASP Event Argument Roles or Selection Restriction.')
        drs_string = str()
        for index, (e, t, r) in enumerate(items):
            if index % 3 == 0:
                drs_string += '\n'
            drs_string += f'{key.__str__()}({e.__str__()}, "{t.__str__()}", {r.__str__()}). '
        self.logger.debug(f'Event Argument Role or Selection Restriction string: {drs_string}.')
        text2drs_drs_output_file.write(drs_string + '\n')

    def _write_drs_to_asp_generic_data(self, items, key, text2drs_drs_output_file):
        self.logger.info(f'Write DRS to ASP Generic Data.')
        drs_string = str()
        for index, (e, v) in enumerate(items):
            if index % 3 == 0:
                drs_string += '\n'
            drs_string += f'{key.__str__()}({e.__str__()}, "{v.__str__()}"). '
        self.logger.debug(f'Generic DRS string: {drs_string}.')
        text2drs_drs_output_file.write(drs_string + '\n')
