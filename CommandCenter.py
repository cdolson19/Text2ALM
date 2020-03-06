from argparse import ArgumentParser
import logging
import FilePaths
from multiprocessing import Pool
from os import listdir
from pathlib2 import Path
from time import time
from DRS2ALM.DRS2ALM.DRS2ALM import DRS2ALM
from Text2DRS.Text2DRS.Text2DRS import Text2DRS
from Tools.AnswerSetFilter import AnswerSetFilter
from Tools.BABIParser import BABIParser
from Tools.Sphinx import Sphinx
from Tools.VerbNetALMGenerator import VerbNetALMGenerator

module_logger = logging.getLogger('Text2ALM.CommandCenter')
module_logger.setLevel(level=logging.WARNING)

POOL_SIZE = 2


class CommandCenter:
    def __init__(self):
        self.logger = logging.getLogger('Text2ALM.CommandCenter.CommandCenter')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of CommandCenter.')
        self.input_file = None
        self.args = self._get_args()
        self.action = self._get_action()

    def _get_args(self):
        self.logger.info(f'Get Args.')
        parser = ArgumentParser()
        parser.add_argument("action", help='give action to perform', type=str)
        parser.add_argument("--input", help='give full path of input file', type=str)
        parser.add_argument("--size", help='number of tests to run', type=int)
        parser.add_argument("--names", type=str, default=None)
        return parser.parse_args()

    def _get_action(self):
        self.logger.info(f'Get Action.')
        action = self.args.action
        if action.lower() == 'text2alm':
            return 1
        if action.lower() == 'babiparser':
            return 2
        if action.lower() == 'verbnetalmgenerator':
            return 3
        if action.lower() == 'babitests':
            return 4
        else:
            self.logger.exception(f'Did not give valid action to execute.')
            exit(1)

    def execute(self):
        self.logger.info(f'Execute {self.action}.')
        if self.action == 1:
            self.input_file = self._set_input_file(self.args.input)
            self._execute_text2alm()
        elif self.action == 2:
            self.input_file = self._set_input_file(self.args.input)
            self._execute_babi_parser()
        elif self.action == 3:
            self._execute_verbnet_alm_generator()
        elif self.action == 4:
            self._execute_babi_tests()

    def _set_input_file(self, input_path):
        self.logger.info(f'Get Input File.')
        self._validate_input_file(input_path)
        return Path(input_path)

    def _validate_input_file(self, input_path):
        self.logger.info(f'Validate Input File {input_path}.')
        input_narrative_file = Path(input_path)
        if not input_narrative_file.exists():
            self.logger.exception(f'Could not find the txt file.')
            exit(1)

    def _get_input_file_name(self):
        self.logger.info(f'Get Input File Name.')
        return self.input_file.stem

    def _execute_text2alm(self):
        self.logger.info(f'Execute Text2ALM.')
        ts = time()
        self._execute_text2alm_processes(self.input_file, 'QA5')
        te = time()
        self.logger.warning(f'EL FIN (Took {te - ts} s)')

    def _execute_babi_parser(self):
        self.logger.info(f'Execute BABI Parser.')
        ts = time()
        babi_parser = BABIParser.BABIParser(self.input_file)
        babi_parser.execute_babi_parser()
        te = time()
        self.logger.warning(f'EL FIN (Took {te - ts} s)')

    def _execute_verbnet_alm_generator(self):
        self.logger.info(f'Execute VerbNet ALM Generator.')
        ts = time()
        verbnet_alm_generator = VerbNetALMGenerator.VerbNetALMGenerator(self.args.input, self.args.names)
        verbnet_alm_generator.execute_verbnet_alm_generator()
        te = time()
        self.logger.warning(f'EL FIN (Took {te - ts} s)')

    def _execute_babi_tests(self):
        self.logger.info(f'Execute BABI Tests.')
        tests_to_run = self.args.size
        RUN_TESTS = False

        if str(self.args.input).lower() == 'all':
            #categories = ['QA1', 'QA2', 'QA3', 'QA5', 'QA6', 'QA7', 'QA8']
            categories = ['QA5', 'QA6', 'QA7', 'QA8']
        else:
            categories = [self.args.input]

        BASELINE_COUNT = 0
        for category in categories:

            start_time = time()
            if RUN_TESTS:
                test_dir = FilePaths.BABI_TEST_TEST_FILE_DIR / category
            else:
                test_dir = FilePaths.BABI_TEST_FILE_DIR / category


            sphinx = Sphinx.Sphinx(test_dir)
            results_dict = {}

            count = 0
            p = Pool(POOL_SIZE)
            work = []

            for file in sorted(listdir(test_dir.__str__())):
                self.logger.warning(f'File: {file}.')
                if count < BASELINE_COUNT:
                    count += 1
                    continue

                if count >= tests_to_run + BASELINE_COUNT:
                    break

                work.append((Path(file), test_dir, category, sphinx, results_dict))
                count += 1

            results = p.map(self._execute_text2alm_babi_processes, work)
            p.close()
            p.join()
            for result in results:
                results_dict[result[0]] = result[1]
            self._document_results(category, results_dict)
            end_time = time()
            self.logger.warning(f'Total Time: {end_time - start_time}.')

    @staticmethod
    def _execute_text2alm_babi_processes(work):
        (file, test_dir, category, sphinx, results_dict) = work
        ts = time()
        question_num = int(file.stem.split('_')[-1])
        input_file = test_dir / file

        CommandCenter._execute_text2alm_processes(input_file, category)

        qa = Sphinx.QuestionAnswer(sphinx.QuestionDict.get(question_num),
                                   sphinx.AnswerDict.get(question_num),
                                   sphinx.QuestionTimePointDict.get(question_num),
                                   AnswerSetFilter.AnswerSetFilter.get_output_file_path(file.stem))
        ans = qa.Correct
        te = time()
        module_logger.warning(f'EL FIN ({category}-{question_num} took {te - ts} s)\n\n')
        return question_num, f'{category}-{question_num}\t:\t{ans}\t:\t{te - ts}\n'

    @staticmethod
    def _execute_text2alm_processes(input_file: Path, filter_category):
        output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / input_file.stem
        if not output_dir.is_dir():
            output_dir.mkdir()

        with open(input_file, 'r') as t:
            text = ' '.join(t)

        text2drs = Text2DRS(text, input_file.stem)
        drs_model = text2drs.execute_text2drs()
        drs2alm = DRS2ALM(input_file.stem, drs_model)
        return_code = drs2alm.execute_alm()
        answer_set_filter = AnswerSetFilter.AnswerSetFilter(input_file.stem, drs_model)

        if return_code == 0:
            answer_set_filter.filter_calm_answer_set(filter_category)

    def _document_results(self, category: str, results_dict: dict):
        self.logger.info(f'Document Results.')
        results = FilePaths.TEXT2ALM_OUTPUT_DIR / f'{category}_results.txt'
        if results.exists():
            results.unlink()
        results_str = str()
        for key, value in sorted(results_dict.items()):
            results_str += value
        self.logger.info(f'Results String {results_str}.')
        with open(results, 'w') as result_file:
            result_file.write(f'{results_str}')

if __name__ == "__main__":
    module_logger.info(f'Main.')
    commandCenter = CommandCenter()
    commandCenter.execute()
