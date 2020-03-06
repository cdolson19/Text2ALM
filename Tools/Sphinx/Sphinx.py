import logging
from pathlib2 import Path
import re

module_logger = logging.getLogger('Text2ALM.Tools.Sphinx')
module_logger.setLevel(level=logging.WARNING)


class Sphinx:
    def __init__(self, directory):
        self.logger = logging.getLogger('Text2ALM.Tools.Sphinx.Sphinx')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of Sphinx.')
        self.QuestionDict = {}
        self.AnswerDict = {}
        self.QuestionTimePointDict = {}
        self._set_question_answer_dicts(directory)

    def _set_question_answer_dicts(self, test_directory):
        self.logger.info(f'Set Question Answer Dictionary.')
        question_files = test_directory.glob("*_questions.txt")
        question_file = next(question_files)
        with open(question_file, 'r') as q_file:
            for line in q_file:
                split_line = line.split(':')
                question_num_in_file = int(split_line[0].strip())
                self.QuestionDict[question_num_in_file] = split_line[1].strip()
                self.AnswerDict[question_num_in_file] = split_line[2].strip()
                self.QuestionTimePointDict[question_num_in_file] = int(split_line[3].strip())


class QuestionAnswer:
    def __init__(self, question: str, answer: str, question_time: int, answer_set_file: Path):
        self.logger = logging.getLogger('Text2ALM.Tools.Sphinx.QuestionAnswer')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of QuestionAnswer.')

        self.Answer = answer
        self.Question = question
        self.QuestionTimePoint = question_time
        self.AnswerSetFile = answer_set_file
        self.Correct = False

        self._check_if_correct()

    def _check_if_correct(self):
        self.logger.info(f'Checking for correct answer.')

        if not self.AnswerSetFile.exists():
            self.logger.warning(f'Answer Set File Path {self.AnswerSetFile} does not exist.')
            return

        as_answer = None
        with open(self.AnswerSetFile, 'r') as answer_set_file:
            answer_set_lines = ' '.join(answer_set_file)

        question1 = r'Where is (\w+)\?'  # Where is Fred?
        match = re.match(question1, self.Question)
        if match:
            atom_in_question = 'location'
            entity_in_question = match.group(1)
            answer_atom = f'{atom_in_question}\\({entity_in_question}, (\\w+), ' \
                f'{self.QuestionTimePoint}\\)'

            atom_match = re.search(answer_atom, answer_set_lines)
            if atom_match:
                as_answer = atom_match.group(1)
            self.Correct = as_answer == self.Answer
            return

        question2 = r'Where is the (\w+)\?'  # Where is the football?
        match = re.match(question2, self.Question)
        if match:
            atom_in_question = 'location'
            entity_in_question = match.group(1)
            answer_atom = f'{atom_in_question}\\({entity_in_question}, (\\w+), ' \
                f'{self.QuestionTimePoint}\\)'

            atom_match = re.search(answer_atom, answer_set_lines)
            if atom_match:
                as_answer = atom_match.group(1)
            self.Correct = as_answer == self.Answer
            return

        question3 = r'Where was the (\w+) before the (\w+)\?'  # Where was the football before the kitchen?
        match = re.match(question3, self.Question)
        if match:
            atom_in_question = 'location'
            entity_in_question = match.group(1)
            new_location = match.group(2)
            answer_atom = f'{atom_in_question}\\({entity_in_question}, (\\w+), ' \
                f'(\\d+)\\)'

            matches = re.findall(answer_atom, answer_set_lines)
            matches.sort(key=lambda m: int(m[1]), reverse=True)
            has_been_in_new_location = False
            for (loc, t) in matches:
                if loc == new_location:
                    has_been_in_new_location = True
                elif loc != new_location and has_been_in_new_location:
                    as_answer = loc
                    break
            self.Correct = as_answer == self.Answer
            return

        question4 = r'What did (\w+) give to (\w+)\?'  # What did Fred give to Bob?
        match = re.match(question4, self.Question)
        if match:
            atom_in_question = 'event_object'
            agent_in_question = match.group(1)
            recipient_in_question = match.group(2)

            agent_answer_atom = f'event_agent\\((\\w+), {agent_in_question}\\)'
            agent_matches = re.findall(agent_answer_atom, answer_set_lines)
            agent_matches.sort(key=lambda m: m, reverse=True)

            recipient_answer_atom = f'event_recipient\\((\\w+), {recipient_in_question}\\)'
            recipient_matches = re.findall(recipient_answer_atom, answer_set_lines)
            recipient_matches.sort(key=lambda m: m, reverse=True)

            event = None

            for agent_event_num in agent_matches:
                for recipient_event_num in recipient_matches:
                    if agent_event_num == recipient_event_num:
                        event = agent_event_num
                        break
                if event:
                    break

            if event:
                object_answer_atom = f'{atom_in_question}\\({event}, ([a-zA-Z]+)\\b\\)'
                atom_matches = re.findall(object_answer_atom, answer_set_lines)
                if len(atom_matches) > 0:
                    as_answer = atom_matches[0]
                    self.Correct = as_answer == self.Answer
            return

        question5 = r'Who (\w+) the (\w+)\?'  # Who received the football? OR Who gave the football?
        match = re.match(question5, self.Question)
        if match:
            action_in_question = match.group(1)
            object_in_question = match.group(2)

            if action_in_question == 'received':
                atom_in_question = 'event_recipient'
            else:  # action_in_question == 'gave':
                atom_in_question = 'event_agent'

            object_answer_atom = f'event_object\\((\\w+), {object_in_question}\\)'
            object_matches = re.findall(object_answer_atom, answer_set_lines)
            object_matches.sort(key=lambda m: m, reverse=True)

            if len(object_matches) > 0:
                event = object_matches[0]
                entity_answer_atom = f'{atom_in_question}\\({event}, ([a-zA-Z]+)\\b\\)'
                atom_matches = re.findall(entity_answer_atom, answer_set_lines)
                if len(atom_matches) > 0:
                    as_answer = atom_matches[0]
                    self.Correct = as_answer == self.Answer
            return

        question6 = r'Who did (\w+) give the (\w+) to\?'  # Who did Mary give the football to?
        match = re.match(question6, self.Question)
        if match:
            atom_in_question = 'event_recipient'
            agent_in_question = match.group(1)
            object_in_question = match.group(2)

            agent_answer_atom = f'event_agent\\((\\w+), {agent_in_question}\\)'
            agent_matches = re.findall(agent_answer_atom, answer_set_lines)
            agent_matches.sort(key=lambda m: m, reverse=True)

            object_answer_atom = f'event_object\\((\\w+), {object_in_question}\\)'
            object_matches = re.findall(object_answer_atom, answer_set_lines)
            object_matches.sort(key=lambda m: m, reverse=True)

            event = None

            for agent_event_num in agent_matches:
                for object_event_num in object_matches:
                    if agent_event_num == object_event_num:
                        event = agent_event_num
                        break
                if event:
                    break

            if event:
                recipient_answer_atom = f'{atom_in_question}\\({event}, ([a-zA-Z]+)\\b\\)'
                recipient_matches = re.findall(recipient_answer_atom, answer_set_lines)
                if len(recipient_matches) > 0:
                    as_answer = recipient_matches[0]
                    self.Correct = as_answer == self.Answer
            return

        question7 = r'Is (\w+) in the (\w+)\?'  # Is Sandra in the hallway?
        match = re.match(question7, self.Question)
        if match:
            atom_in_question = 'location'
            entity_in_question = match.group(1)
            location_in_question = match.group(2)
            answer_atom = f'{atom_in_question}\\({entity_in_question}, {location_in_question}, ' \
                f'{self.QuestionTimePoint}\\)'

            true_false_answer = self.Answer == 'yes'
            matches = re.findall(answer_atom, answer_set_lines)
            as_answer = len(matches) > 0
            self.Correct = as_answer == true_false_answer
            return

        question8 = r'How many objects is (\w+) (?:carrying\?|holding\?)'  # How many objects is
        # Mary carrying?
        match = re.match(question8, self.Question)
        if match:
            atom_in_question = 'held_by'
            entity_in_question = match.group(1)
            answer_atom = f'{atom_in_question}\\((\\w+), {entity_in_question}, ' \
                f'{self.QuestionTimePoint}\\)'

            matches = re.findall(answer_atom, answer_set_lines)
            as_answer = len(matches)
            self.Correct = as_answer == self._convert_written_number_to_int(self.Answer)
            return

        question9 = r'What is (\w+) (?:carrying\?|holding\?)'  # What is John carrying?
        match = re.match(question9, self.Question)
        if match:
            atom_in_question = 'held_by'
            entity_in_question = match.group(1)
            answer_atom = f'{atom_in_question}\\((\\w+), {entity_in_question}, ' \
                f'{self.QuestionTimePoint}\\)'

            if ',' in self.Answer:
                answer = self.Answer.split(', ')
                answer.sort()
            else:
                answer = [self.Answer]
            matches = re.findall(answer_atom, answer_set_lines)
            if len(matches) == 0:
                as_answer = ['nothing']
            else:
                matches.sort()
                as_answer = matches
            self.Correct = as_answer == answer
            return

        question10 = r'Who gave the (\w+) to (\w+)\?'  # Who did Mary give the football to?
        match = re.match(question10, self.Question)
        if match:
            atom_in_question = 'event_agent'
            object_in_question = match.group(1)
            recipient_in_question = match.group(2)

            object_answer_atom = f'event_object\\((\\w+), {object_in_question}\\)'
            object_matches = re.findall(object_answer_atom, answer_set_lines)
            object_matches.sort(key=lambda m: m, reverse=True)

            recipient_answer_atom = f'event_recipient\\((\\w+), {recipient_in_question}\\)'
            recipient_matches = re.findall(recipient_answer_atom, answer_set_lines)
            recipient_matches.sort(key=lambda m: m, reverse=True)

            event = None

            for recipient_event_num in recipient_matches:
                for object_event_num in object_matches:
                    if recipient_event_num == object_event_num:
                        event = recipient_event_num
                        break
                if event:
                    break

            if event:
                agent_answer_atom = f'{atom_in_question}\\({event}, ([a-zA-Z]+)\\b\\)'
                agent_matches = re.findall(agent_answer_atom, answer_set_lines)
                if len(agent_matches) > 0:
                    as_answer = agent_matches[0]
                    self.Correct = as_answer == self.Answer
            return

        self.logger.warning(f'No question match was found for {self.Question}.')

    @staticmethod
    def _convert_written_number_to_int(number: str):
        if number == 'zero':
            return 0
        if number == 'one':
            return 1
        if number == 'two':
            return 2
        if number == 'three':
            return 3
        if number == 'four':
            return 4
        if number == 'five':
            return 5
        if number == 'six':
            return 6
        if number == 'seven':
            return 7
        if number == 'eight':
            return 8
        if number == 'nine':
            return 9
        if number == 'ten':
            return 10
        return 0
