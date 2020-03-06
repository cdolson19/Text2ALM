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
import json
import os
from config import CORE_NLP_HOST, CORE_NLP_PORT
from stanfordcorenlp import StanfordCoreNLP
from time import time

coref_props = {'annotators': 'coref', 'pipelineLanguage': 'en'}
nlp = StanfordCoreNLP(CORE_NLP_HOST, port=CORE_NLP_PORT)

module_logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS')
module_logger.setLevel(level=logging.WARNING)


class CoreNLPProcessor:
    def __init__(self, input_text: str, input_name: str):
        self.logger = logging.getLogger('Text2ALM.Text2DRS.Text2DRS.CoreNLPProcessor')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of CoreNLPProcessor.')
        self.input_name = input_name
        self.input_text = input_text
        self.coref_dict = dict()
        self.ner_dict = dict()

    def process_corenlp(self):
        self.logger.info(f'Execute CoreNLP Processing.')
        ts = time()

        if not self._get_existing_corenlp_output():
            nlp_coref_dict = self._get_coref()
            self._generate_coref_dict(nlp_coref_dict)

        te = time()
        self.logger.warning(f'Processing CoreNLP took {te-ts}')

        self._write_corenlp_output()

    def _get_corenlp_output_file_path(self):
        return FilePaths.TEXT2ALM_OUTPUT_DIR / self.input_name / f'{self.input_name}_corenlp.txt'

    def _get_existing_corenlp_output(self):
        file_existed = False
        corenlp_output_file = self._get_corenlp_output_file_path()
        if corenlp_output_file.exists() and os.path.getsize(corenlp_output_file.__str__()) > 0:
            output = open(corenlp_output_file, 'r').read().split('\n')
            if len(output) > 1:
                self.coref_dict = eval(output[1])
                file_existed = True
        return file_existed

    def _get_coref(self):
        """
        Process input file by running corenlp through command line
        Output file format can be choose from text, xml, json
        :return:
        """
        self.logger.info(f'Get Coreferences.')
        result_dict = json.loads(nlp.annotate(self.input_text, properties=coref_props))
        self.logger.info(f'Get Coreferences Result: {result_dict.get("corefs")}.')
        return result_dict.get('corefs')

    def _generate_coref_dict(self, nlp_coref_dict: dict):
        self.logger.info(f'Generate Coref Dict {nlp_coref_dict}.')
        for idx, entity in nlp_coref_dict.items():
            for elem in entity:
                word = elem.get('text')
                sentence_id = int(elem.get('sentNum'))
                if word not in self.coref_dict:
                    self.coref_dict[word] = [sentence_id]
                else:
                    id_list = self.coref_dict.get(word)
                    if elem.get('isRepresentativeMention'):
                        id_list.insert(0, sentence_id)
                    else:
                        id_list.append(sentence_id)

    def _write_corenlp_output(self):
        self.logger.info(f'Writing CoreNLP Output.')
        output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / self.input_name
        if not output_dir.is_dir():
            output_dir.mkdir()
        output_path = output_dir / f'{self.input_name}_corenlp.txt'
        with open(output_path, 'w') as output_file:
            output_file.write(f'COREF DICTIONARY:\n{self.coref_dict.__str__()}\n\n')
