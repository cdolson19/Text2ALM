from pathlib2 import Path


# region Outputs
OUTPUT_DIR = Path(Path.cwd(), 'Output')
BABI_PARSER_OUTPUT_DIR = OUTPUT_DIR / 'BABIParser_Outputs'
CALM_OUTPUT_DIR_ORIGINAL = Path(Path.cwd(), 'CALM', 'output')
VERBNETALMGENERATOR_OUTPUT_DIR = OUTPUT_DIR / 'VerbNetALMGenerator_Outputs'
TEXT2ALM_OUTPUT_DIR = OUTPUT_DIR / 'Text2ALM_Outputs'
# endregion

# region Resource Paths
VNPB_MAPPINGS = Path(Path.cwd(), "Text2DRS", "SemLink", "vn-pb", "vnpbMappings")
CALM = Path(Path.cwd(), 'CALM')
# endregion

TEST_FILE_DIR = Path(Path.cwd(), 'TestFiles')
BABI_TEST_FILE_DIR = TEST_FILE_DIR / 'BABI_Tests' / 'Train'
BABI_TEST_TEST_FILE_DIR = TEST_FILE_DIR / 'BABI_Tests' / 'Test'

CONFIG = Path(Path.cwd(), "CONFIG.cfg")

LTH_PATH = Path(Path.cwd(), 'lth_srl')
