import FilePaths


def main():
    x = FilePaths.TEXT2ALM_OUTPUT_DIR
    propbank_rolesets = dict()
    for d in x.glob('**/lth_*'):
        with open(d, 'r') as f:
            for i, line in enumerate(f):
                split_line = line.split('\t')
                if len(split_line) >= 13 and split_line[13] != '_':
                    if split_line[13] in propbank_rolesets:
                        propbank_rolesets[split_line[13]] = propbank_rolesets[split_line[13]] + 1
                    else:
                        propbank_rolesets[split_line[13]] = 0
    print(propbank_rolesets)

    verbnet_classes = dict()
    for d in x.glob('**/*.tp'):
        with open(d, 'r') as f:
            for i, line in enumerate(f):
                split_line = line.split()
                if len(split_line) > 0 and split_line[0].startswith('e'):
                    if split_line[2] in verbnet_classes:
                        verbnet_classes[split_line[2]] = verbnet_classes[split_line[2]] + 1
                    else:
                        verbnet_classes[split_line[2]] = 0
    print(verbnet_classes)


if __name__ == "__main__":
    main()
