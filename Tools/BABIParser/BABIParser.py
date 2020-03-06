import FilePaths
import logging
from pathlib2 import Path

module_logger = logging.getLogger('Text2ALM.Tools.BABIParser')
module_logger.setLevel(level=logging.WARNING)


class BABIInput:
    def __init__(self, question='', answers=None):
        self.logger = logging.getLogger('Text2ALM.Tools.BABIParser.BABIInput')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of BABIInput.')
        self.narrative = dict()
        self.question = question
        self.question_time_point = 0

        if answers is None:
            self.answers = list()
        else:
            self.answers = answers.copy()

    def set_question_time_point(self, timepoint):
        self.logger.info(f'Set Question Time Point: {timepoint}.')
        self.question_time_point = timepoint

    def set_narrative(self, narrative: dict):
        self.logger.info(f'Set Narrative: {narrative}.')
        self.narrative = narrative.copy()

    def set_question(self, question: str):
        self.logger.info(f'Set Question: {question}.')
        self.question = question

    def _get_narrative_string(self, with_keys: bool):
        narrative = ''
        keys = list(self.narrative)
        keys.sort()
        for key in keys:
            if with_keys:
                narrative += f'\n\t{key}: {self.narrative[key]}'
            else:
                narrative += f'{self.narrative[key]}\n'
        return narrative

    def _get_answers_string(self):
        return ', '.join(self.answers)

    def get_narrative_str(self):
        return f'{self._get_narrative_string(False)}'

    def __str__(self):
        return f'Narrative: {self._get_narrative_string(True)}\n' + \
               f'Question: {self.question}\n' + \
               f'Question Time Point: {self.question_time_point}\n' + \
               f'Answers: {self._get_answers_string()}\n'


class BABIParser:
    def __init__(self, babi_file_path: Path):
        self.logger = logging.getLogger('Text2ALM.Tools.BABIParser.BABIParser')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of BABIParser with {babi_file_path}.')
        self.babi_file_path = babi_file_path

    @staticmethod
    def _get_number(line: str):
        split_line = line.split(' ')
        number = split_line[0]
        return int(number), line[len(number):].strip()

    @staticmethod
    def _is_question(line: str):
        return line.__contains__('?')

    def _create_babi_input(self, line: str):
        self.logger.info(f'Create BABI Input: {line}')
        question_answer = line.split('\t')
        question = question_answer[0].strip()
        answers = question_answer[1].strip().split(',')
        return BABIInput(question, answers)

    def execute_babi_parser(self):
        self.logger.info(f'Execute BABI Parser.')
        babi_input_info = list()
        with open(self.babi_file_path, 'r') as babi_file:
            narrative = dict()
            question_count = 0
            for line in babi_file:
                number, sentence = self._get_number(line)
                if number == 1:
                    narrative = dict()
                    question_count = 0

                number = (number - question_count) - 1

                if self._is_question(sentence):
                    babi_input = self._create_babi_input(sentence)
                    babi_input.set_narrative(narrative.copy())
                    babi_input.set_question_time_point(number)
                    babi_input_info.append(babi_input)
                    question_count += 1
                else:
                    narrative[number] = sentence

        filename = self.babi_file_path.name
        output_path = Path(FilePaths.BABI_PARSER_OUTPUT_DIR, filename)

        with open(output_path, 'w') as output_file:
            output = str()
            for count, info in enumerate(babi_input_info):
                output += f'#{count}\n{info.__str__()}\n'
            output_file.write(output)

        # Write 200 training narrative text files to TestFiles/BABI_Tests/Train/

        if self.babi_file_path.name[3].isdigit():
            dir_name = self.babi_file_path.name[0:4]
        else:
            dir_name = self.babi_file_path.name[0:3]
        output_path = Path(FilePaths.TEST_FILE_DIR, 'BABI_Tests', 'Train', dir_name.upper())

        if not output_path.is_dir():
            output_path.mkdir()

        for count, babi_info in enumerate(babi_input_info):
            output_file_path = output_path / f'{self.babi_file_path.stem}_{count}.txt'
            with open(output_file_path, 'w') as output_file:
                output_file.write(babi_info.get_narrative_str())
            if count >= 1999:
                break

        output_file_path = output_path / f'{self.babi_file_path.stem}_questions.txt'
        with open(output_file_path, 'w') as output_file:
            for count, babi_info in enumerate(babi_input_info):
                output_file.write(f'{count} : {babi_info.question} '
                                  f': {", ".join(babi_info.answers)} '
                                  f': {babi_info.question_time_point}\n')
                if count >= 1999:
                    break
