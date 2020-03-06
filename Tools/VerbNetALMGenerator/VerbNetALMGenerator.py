import FilePaths
import logging
import re
import typing
from lxml import html
import requests
import requests.exceptions

ALL_VERBNET_THEMATIC_ROLES = {'actor', 'agent', 'asset', 'attribute',
                              'beneficiary', 'cause', 'co-agent', 'co-patient',
                              'co-theme', 'destination', 'experiencer',
                              'extent', 'goal', 'initial_location',
                              'instrument', 'location', 'material', 'patient',
                              'pivot', 'predicate', 'product', 'recipient',
                              'reflexive', 'result', 'source', 'stimulus',
                              'theme', 'time', 'topic', 'trajectory', 'value'}
CORE_ALM_LIB = 'CoreALMLib'

module_logger = logging.getLogger('Text2ALM.Tools.VerbNetALMGenerator')
module_logger.setLevel(level=logging.WARNING)


class VerbNetALMGenerator:
    def __init__(self, verbnet_url: str, theory_module: str):
        self.logger = logging.getLogger('Text2ALM.Tools.VerbNetALMGenerator.VerbNetALMGenerator')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of VerbNetALMGenerator.')

        self.verbnet_url = verbnet_url
        self.theory, self.module = self._get_theory_module(theory_module)

    def _get_base_verb(self, tree):
        self.logger.info(f'Get base verb.')
        title = tree.xpath('//title/text()')[0].split(':')[1].strip()
        title = re.sub(r'[-.]', '_', title)
        members = set(map(lambda x: x.strip(), tree.xpath(
                '//body/table[@class="ClassSectionBox"]/tr/td/table/' +
                'tr/td/table/tr/td[@class="MemberCell"]/a/text()')))
        roles = set(map(lambda x: x.strip(), tree.xpath(
                '//body/table[@class="ClassSectionBox"]/tr/td/ul/li/a/text()')))
        return title, members, roles

    def _get_subclass_verb(self, tree):
        self.logger.info(f'Get subclass verb.')
        title = tree.xpath('./tr/td[not(@class)]/text()')[0].strip()
        title = re.sub(r'[-.]', '_', title)
        members = set(map(lambda x: x.strip(), tree.xpath(
                './../table[@class="ClassSectionBox"]/tr/td/table/tr/td/table/' +
                'tr/td[@class="MemberCell"]/a/text()')))
        roles = set(map(lambda x: x.strip(), tree.xpath(
                './../table[@class="ClassSectionBox"]/tr/td/ul/li/a/text()')))
        return title, members, roles

    def _get_theory_module(self, theory_module: str):
        self.logger.info(f'Get theory module.')
        theory_module = theory_module.split('.')
        theory = theory_module[0]
        module = theory_module[1]
        return theory, module

    def _get_role_dictionary(self, roles: set):
        self.logger.info(f'Get role dictionary.')
        role_dictionary = dict()
        for vn_role in sorted(roles):
            clean_vn_role = vn_role.replace('-', '')
            role_dictionary[clean_vn_role] = 'ATTRIBUTE'
        return role_dictionary

    def _write_header(self, file: typing.TextIO, title: str):
        self.logger.info(f'Write header.')
        file.write(f'theory {title}\n\n')
        file.write(f'\timport {self.theory}.{self.module} from {CORE_ALM_LIB}\n\n')

    def _write_base_verb_module(self, file: typing.TextIO, verb: dict):
        self.logger.info(f'Write base verb module.')
        title = list(verb.keys())[0]
        members, roles = verb[title]

        file.write(f'\tmodule {title}\n')
        file.write(f'\t\tdepends on {self.module}\n')
        file.write(f'\t\t% VerbNet class {title} has {len(members).__str__()} ' +
                   f'member verbs: (' + ', '.join(members) + ')\n\n')
        file.write(f'\t\tsort declarations\n')
        file.write(f'\t\t\t{title} :: {self.module}\n\n')
        file.write(f'\t\taxioms\n')
        file.write(f'\t\t\tstate constraints\n')
        for vn_thematic_role, kr_role in sorted(roles.items()):
            file.write(f'\t\t\t\t{kr_role}(A, B) if instance(A, {title}),\n'
                       f'\t\t\t\t\t\t\t\tvn_{vn_thematic_role.lower()}(A, B).\n')

    def _write_subclass_verb_modules(self, file: typing.TextIO,
                                     super_class: str,
                                     sub_classes: dict):
        self.logger.info(f'Write subclass verb modules.')
        for title in list(sub_classes.keys()):
            members, roles = sub_classes[title]
            file.write(f'\n\tmodule {title}\n')
            file.write(f'\t\tdepends on {super_class}\n')
            file.write(f'\t\t% VerbNet class {title} has ' +
                       f'{len(members).__str__()} member verbs: (' +
                       ', '.join(members) + ')\n\n')
            file.write(f'\t\tsort declarations\n')
            file.write(f'\t\t\t{title} :: {super_class}\n\n')
            file.write(f'\t\taxioms\n')
            file.write(f'\t\t\tstate constraints\n')
            for vn_thematic_role, kr_role in sorted(roles.items()):
                file.write(f'\t\t\t\t{kr_role}(A, B) if instance(A, {title}),\n'
                           f'\t\t\t\t\t\t\t\tvn_{vn_thematic_role.lower()}(A, B).\n')

    def execute_verbnet_alm_generator(self):
        page = None
        try:
            page = requests.get(self.verbnet_url)
        except requests.exceptions.InvalidURL:
            self.logger.exception(f'Could not find VerbNet page at URL: {self.verbnet_url}')
            exit()

        tree = html.fromstring(page.content)
        base_verb = dict()
        base_title, members, roles = self._get_base_verb(tree)
        base_roles = self._get_role_dictionary(roles)
        base_verb[base_title] = (members, base_roles)

        subclass_dictionary = dict()
        subclass_title_boxes = tree.xpath(
            '//body/table/tr/td/table[@class="SubclassTitleBox"]')
        for subclass_title_box in subclass_title_boxes:
            title, members, roles = self._get_subclass_verb(subclass_title_box)
            roles = roles.union(set(base_roles.keys()))
            roles = self._get_role_dictionary(roles)
            subclass_dictionary[title] = (members, roles)

        vn_alm_file_name = base_title + '.alm'
        vn_alm_output_path = FilePaths.VERBNETALMGENERATOR_OUTPUT_DIR / vn_alm_file_name
        self.logger.info(f'{vn_alm_output_path}')

        with open(vn_alm_output_path, 'w') as output_file:
            self._write_header(output_file, base_title)
            self._write_base_verb_module(output_file, base_verb)
            self._write_subclass_verb_modules(output_file,
                                              base_title,
                                              subclass_dictionary)
