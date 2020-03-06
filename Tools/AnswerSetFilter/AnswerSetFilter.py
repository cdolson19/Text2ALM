import FilePaths
import logging
import re
from pathlib2 import Path

module_logger = logging.getLogger('Text2ALM.Tools.AnswerSetFilter')
module_logger.setLevel(level=logging.WARNING)

CATEGORIES_FILTERS = {'QA1': ['location'],
                      'QA2': ['location', 'held_by'],
                      'QA3': ['location', 'held_by'],
                      'QA4': ['location', 'held_by'],
                      'QA5': ['location', 'held_by', 'event_recipient', 'event_agent', 'event_object'],
                      'QA6': ['location'],
                      'QA7': ['location', 'held_by'],
                      'QA8': ['location', 'held_by'],
                      'QA9': ['location', 'held_by'],
                      'QA10': ['location', 'held_by']
                      }


class AnswerSetFilter:
    def __init__(self, file_name: str, drs_model):
        self.logger = logging.getLogger('Text2ALM.Tools.AnswerSetFilter.AnswerSetFilter')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of AnswerSetFilter.')
        self.input_file_path = self._set_input_file_path(file_name)
        self.output_file_path = self._set_output_file_path(file_name)
        self.drs_model = drs_model

    def _set_input_file_path(self, name: str):
        """
        Sets the input file path to 'CALM/output/<name>/<name>.ans'.
        :param name: The name of the folder containing the input file.
        """
        self.logger.info(f'Setting answer set input file path for name: {name}.')
        input_file_name = f'{name}.tp.ans'
        input_file_path = Path(FilePaths.TEXT2ALM_OUTPUT_DIR / f'{name}' / f'CALM' / f'{input_file_name}')
        return input_file_path

    def _set_output_file_path(self, name: str):
        """
        Sets the output file path to 'CALM/output/<name>/filter_<name>.ans'.
        :param name: The name of the folder to place the output file.
        """
        self.logger.info(f'Setting filtered output file path for name: {name}.')
        output_file_name = f'filtered_{name}.tp.ans'
        output_file_path = Path(FilePaths.TEXT2ALM_OUTPUT_DIR / f'{name}' / f'CALM' / f'{output_file_name}')
        return output_file_path

    @staticmethod
    def get_output_file_path(name: str):
        """
        Gets the output file path 'CALM/output/<name>/filter_<name>.ans'.
        :param name: The name of the folder to place the output file.
        """
        output_file_name = f'filtered_{name}.tp.ans'
        output_file_path = Path(FilePaths.TEXT2ALM_OUTPUT_DIR / f'{name}' / f'CALM' / f'{output_file_name}')
        return output_file_path

    def _read_answer_sets_from_input_file(self):
        """
        Reads the answer sets from the input file path.
        :return: A list containing strings representing each answer set.
        """
        self.logger.info(f'Reading answer set input file at {self.input_file_path.__str__()}')
        with open(self.input_file_path, 'r') as input_file:
            file_content = input_file.read()
            answer_sets = re.findall('{.*?}', file_content, re.M | re.DOTALL)
        return answer_sets

    def _filter_answer_set(self, filter_literal: str, answer_set: str):
        """
        Finds all occurrences of the given literal in the given answer set.
        :param filter_literal: A string, the literal to find in the answer set.
        :param answer_set: A string, the answer set to filter.
        :return:
        """
        self.logger.info(f'Filtering answer set with literal: {filter_literal}.')
        match = f'({filter_literal}\(.*?\))'
        output = re.findall('[\s|,]' + match, answer_set, re.DOTALL)
        output.sort()
        return output

    def _filter_answer_sets(self, answer_sets: list, category: str):
        """
        Writes the filtered answer sets to the output file.
        """
        self.logger.info(f'Filtering answer sets.')
        output_string = str()
        for count, answer_set in enumerate(answer_sets):
            output_string += f'% Filtered Answer Set {count+1} of {len(answer_sets)}\n' + '{\n'
            for cat_filter in CATEGORIES_FILTERS[category]:
                output = self._filter_answer_set(cat_filter, answer_set)
                output_string += f'{", ".join(output)}\n'
            output_string += '}\n\n'
        return output_string

    def _rewrite_answer_sets(self, filtered_answer_sets: str):
        """
        Writes the filtered answer sets to the output file.
        """
        self.logger.info(f'Re-writing answer sets.')
        re_written_answer_sets = str(filtered_answer_sets)
        for ref, ent in self.drs_model.DRS_Dict['property']:
            pattern = f'({ref})' + '\\b'
            re_written_answer_sets = re.sub(pattern, ent, re_written_answer_sets)
        filtered_answer_sets += f'\n% Rewritten:\n{re_written_answer_sets}'
        return filtered_answer_sets

    def _write_filtered_calm_answer_set(self, filtered_answer_sets):
        with open(self.output_file_path, 'w') as output_file:
            output_file.write(filtered_answer_sets)

    def filter_calm_answer_set(self, category: str):
        """
        Performs the answer set filtering my calling other functions.
        :return:
        """
        if Path.exists(self.input_file_path):
            answer_sets = self._read_answer_sets_from_input_file()
            filtered_answer_sets = self._filter_answer_sets(answer_sets, category)
            self._write_filtered_calm_answer_set(filtered_answer_sets)
            filtered_answer_sets = self._rewrite_answer_sets(filtered_answer_sets)
            self._write_filtered_calm_answer_set(filtered_answer_sets)
