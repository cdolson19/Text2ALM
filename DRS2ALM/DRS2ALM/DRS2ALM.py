import FilePaths
import logging
import os
from pathlib2 import Path
import shutil
import subprocess

module_logger = logging.getLogger('Text2ALM.DRS2ALM.DRS2ALM')
module_logger.setLevel(level=logging.WARNING)


class DRS2ALM:
    def __init__(self, file_name: str, drs_model):
        self.logger = logging.getLogger('Text2ALM.DRS2ALM.DRS2ALM.DRS2ALM')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of DRS2ALM.')

        self.file_name = file_name

        self.output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / file_name

        self.drs_model = drs_model

        self.alm_dict = dict()

        self.alm_dict['imports'] = self._set_import_list()

        self.alm_dict['selectional_restrictions'] = self._set_selectional_restrictions()
        self.alm_dict['referent_instances'] = self._set_referent_instances()
        self.alm_dict['event_instances'] = self._set_event_instances()
        self.alm_dict['event_instance_attributes'] = self._set_event_instance_attributes()
        self.alm_dict['ref_to_roles'] = self._set_ref_to_roles()
        self.alm_dict['history'] = self._set_history()
        self.alm_dict['sorts'] = self._set_sorts()

    def _set_import_list(self):
        import_dict = {}
        for event, vn_class in self.drs_model.DRS_Dict['eventType']:
            theory_name = f'{"_".join(vn_class.split("-")[0:2]).replace(".", "_")}'
            if theory_name not in import_dict:
                import_dict[theory_name] = f'{vn_class.replace(".", "_").replace("-", "_")}'

        import_list = [f'{key}.{value}' for key, value in import_dict.items()]
        import_list.sort()
        return import_list

    def _set_selectional_restrictions(self):
        selectional_restrictions = dict()
        for event, role, ref in self.drs_model.DRS_Dict['eventArgumentSelectionRestriction']:
            self.logger.debug(f'Event {event}  Role {role}  Ref {ref}')
            if ref not in selectional_restrictions:
                selectional_restrictions[ref] = set()
            selectional_restrictions[ref] = selectional_restrictions[ref].union([role.lower()])
        self.logger.info(f'Selectional_Restrictions: {selectional_restrictions.__str__()}')
        return selectional_restrictions

    def _set_sorts(self):
        sorts = dict()
        for ref, ent in self.drs_model.DRS_Dict['property']:
            if ent.lower() not in sorts:
                sorts[ent.lower()] = 'tangible_entity'

            roles = list()
            if ref in self.alm_dict['ref_to_roles']:
                roles = self.alm_dict['ref_to_roles'][ref]


            vn_thematic_role_spatial_entity = {
                'destination',
                'initial_location',
                'source'
                }

            vn_thematic_role_places = {
                'location',
                'place'
                }

            vn_thematic_role_living_entity = {
                'actor',
                'agent',
                'beneficiary',
                'cause',
                'co-agent',
                'co-patient',
                'co-theme',
                'experiencer',
                'participant',
                'patient',
                'recipient',
                'theme',
                'undergoer'
                }

            vn_thematic_role_entity = {
                 'instrument',
                 'material',
                 'pivot',
                 'product',
                 'stimulus',
                 'time',
                 'trajectory',
                 'topic',
                 'value',
                 'result',
                 'attribute',
                 'duration',
                 'extent',
                 'final_time',
                 'frequency',
                 'goal',
                 'initial_time'
                }

            spatial_entities = not set(roles).isdisjoint(vn_thematic_role_spatial_entity)
            places = not set(roles).isdisjoint(vn_thematic_role_places)
            living_entities = not set(roles).isdisjoint(vn_thematic_role_living_entity)
            entities = not set(roles).isdisjoint(vn_thematic_role_entity)

            if living_entities:
                sorts[ent.lower()] = 'living_entity'
            elif places:
                sorts[ent.lower()] = 'place'
            elif spatial_entities:
                sorts[ent.lower()] = 'spatial_entity'
            elif entities:
                sorts[ent.lower()] = 'entity'
        return sorts

    def _set_referent_instances(self):
        return [(ref, ent.lower()) for ref, ent in self.drs_model.DRS_Dict['property']]

    def _set_event_instances(self):
        return [(event, vn_class.replace(".", "_").replace("-", "_"))
                    for event, vn_class in self.drs_model.DRS_Dict['eventType']]

    def _set_event_instance_attributes(self):
        event_instance_attributes = dict()
        for event, attr, ref in self.drs_model.DRS_Dict['eventArgumentRole']:
            self.logger.debug(f'Event {event}  Attr {attr}  Ref {ref}')
            if event not in event_instance_attributes:
                event_instance_attributes[event] = list()
            event_instance_attributes[event].append((attr.lower(), ref))
        self.logger.debug(f'Event instance attributes: {event_instance_attributes.__str__()}')
        return event_instance_attributes

    def _set_ref_to_roles(self):
        ref_to_roles_dict = dict()
        for event, attr, ref in self.drs_model.DRS_Dict['eventArgumentRole']:
            self.logger.debug(f'Event {event}  Attr {attr}  Ref {ref}')
            if ref not in ref_to_roles_dict:
                ref_to_roles_dict[ref] = list()
            ref_to_roles_dict[ref].append(attr.lower())
        self.logger.debug(f'Ref to Roles: {ref_to_roles_dict.__str__()}')
        return ref_to_roles_dict

    def _set_history(self):
        return [(event, time) for event, time in sorted(self.drs_model.DRS_Dict['eventTime'], key=lambda et: et[1])]

    def execute_alm(self):
        self.logger.info(f'Executing ALM Processing.')
        file_generator_alm = FileGeneratorALM(self.file_name, self.alm_dict)
        file_generator_alm.write_alm_file()

        # store text2drs tool's path
        original_path = Path.cwd()
        alm_file_path = Path(Path.cwd(), FilePaths.TEXT2ALM_OUTPUT_DIR, self.file_name, self.file_name)

        os.chdir(FilePaths.CALM)
        cmd = f'java -jar calm.jar {alm_file_path}.tp'
        return_code = subprocess.call(cmd, shell=True)  # TODO
        os.chdir(original_path)

        if return_code == 0:
            self._move_calm_output()

        return return_code

    def _get_original_calm_output_file_path(self):
        self.logger.info(f'Get original CALM output file path')
        return FilePaths.CALM_OUTPUT_DIR_ORIGINAL / f'{self.file_name}.tp'

    def _get_new_calm_output_file_path(self):
        self.logger.info(f'Get new CALM output file path')
        return FilePaths.TEXT2ALM_OUTPUT_DIR / f'{self.file_name}' / f'CALM'

    def _move_calm_output(self):
        self.logger.info(f'Move CALM output.')
        original_output_dir = self._get_original_calm_output_file_path()
        new_output_dir = self._get_new_calm_output_file_path()
        if new_output_dir.exists():
            shutil.rmtree(new_output_dir.__str__())
        if original_output_dir.exists():
            shutil.move(original_output_dir.__str__(), new_output_dir.__str__())


class FileGeneratorALM:
    def __init__(self, file_name, alm_dict):
        self.logger = logging.getLogger('Text2ALM.DRS2ALM.DRS2ALM.FileGeneratorALM')
        self.logger.setLevel(logging.WARNING)
        self.logger.info(f'Creating an instance of FileGeneratorALM.')
        self.file_name = file_name
        self.alm_file_name = self.file_name + '.tp'
        self.alm_dict = alm_dict

    def write_alm_file(self):
        self.logger.info(f'Writing ALM for {self.alm_file_name}.')
        output_dir = FilePaths.TEXT2ALM_OUTPUT_DIR / self.file_name
        output_path = output_dir / self.alm_file_name

        with open(output_path, 'w') as alm_file:
            self._write_alm_file(alm_file)
            alm_file.close()

    def _write_alm_file(self, alm_file):
        self.logger.info(f'Write DRS to ALM.')
        self._write_alm_header(alm_file)
        self._write_alm_theory(alm_file)
        self._write_alm_structure(alm_file)
        self._write_alm_footer(alm_file)

    def _write_alm_header(self, alm_file):
        self.logger.info(f'Writing ALM Header.')
        alm_string = f'system description {self.file_name}'
        alm_file.write(alm_string)

    def _write_alm_theory(self, alm_file):
        self.logger.info(f'Writing ALM Theory.')
        alm_string = f'\n\ttheory {self.file_name}'
        alm_file.write(alm_string)
        self._write_alm_imports(alm_file)
        self._write_alm_module(alm_file)

    def _write_alm_imports(self, alm_file):
        self.logger.info(f'Writing ALM Imports.')
        alm_string = f'\n'
        for vn_module in self.alm_dict["imports"]:
            alm_string += f'\n\t\timport {vn_module} from VN_class_library'
        alm_file.write(alm_string)

    def _write_alm_module(self, alm_file):
        self.logger.info(f'Writing ALM Module.')
        alm_string = f'\n\n\t\tmodule {self.file_name}'

        if len(self.alm_dict["imports"]) > 0:
            alm_string += f'\n\t\t\tdepends on {self.alm_dict["imports"][0]}'

        alm_string += f'\n\n\t\t\tsort declarations'
        for sort, val in self.alm_dict['sorts'].items():
            alm_string += f'\n\t\t\t\t{sort} :: {val}'

        alm_file.write(alm_string)

    def _write_alm_structure(self, alm_file):
        self.logger.info(f'Writing ALM Structure.')
        alm_string = f'\n\n\tstructure {self.file_name}_structure'
        alm_string += f'\n\t\tinstances'

        for ref, ent in self.alm_dict['referent_instances']:
            alm_string += f'\n\t\t\t{ref} in {ent}'

        for event, vn_class in self.alm_dict['event_instances']:
            alm_string += f'\n\n\t\t\t{event} in {vn_class}'
            for attr, ref in self.alm_dict['event_instance_attributes'][event]:
                if attr != 'none-themerole':
                    alm_string += f'\n\t\t\t\tvn_{attr}({ref}) = true'

        alm_file.write(alm_string)

    def _write_alm_footer(self, alm_file):
        self.logger.info(f'Writing ALM Footer.')
        alm_string = f'\n\ntemporal projection'
        alm_string += f'\nmax steps {len(self.alm_dict["history"]) + 1}'
        alm_string += f'\nhistory'
        for event, time in self.alm_dict['history']:
            alm_string += f'\n\thappened({event}, {time}).'
        alm_file.write(alm_string)
