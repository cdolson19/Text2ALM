import FilePaths


def main():

    file_path = FilePaths.TEST_FILE_DIR / 'BABI_Tests' / 'tasks_1-20_v1-2' / 'en' / 'qa8_lists-sets_test.txt'
    file_path2 = FilePaths.TEST_FILE_DIR / 'BABI_Tests' / 'tasks_1-20_v1-2' / 'en' / 'qa8_lists-sets-plus_test.txt'

    out = str()

    with open(file_path, 'r') as f:
        fl = f.readlines()
        travelled_count = 0
        went_back_count = 0
        went_to_count = 0
        discarded_count = 0
        dropped_count = 0
        got_count = 0
        grabbed_count = 0
        left_count = 0
        picked_up_count = 0
        put_down_count = 0
        took_count = 0
        moved_count = 0
        journeyed_count = 0

        for x in fl:
            if "travelled" in x:
                travelled_count += 1
                if travelled_count % 2 == 0:
                    out += x.replace('travelled', 'sprinted')
                else:
                    out += x
            elif "moved" in x:
                moved_count += 1
                if moved_count % 2 == 0:
                    out += x.replace('moved', 'wandered')
                else:
                    out += x
            elif "journeyed" in x:
                journeyed_count += 1
                if journeyed_count % 2 == 0:
                    out += x.replace('journeyed', 'marched')
                else:
                    out += x
            elif "discarded" in x:
                discarded_count += 1
                if discarded_count % 2 == 0:
                    out += x.replace('discarded', 'abandoned')
                else:
                    out += x
            elif "dropped" in x:
                dropped_count += 1
                if dropped_count % 2 == 0:
                    out += x.replace('dropped', 'released')
                else:
                    out += x
            elif "got" in x:
                got_count += 1
                if got_count % 2 == 0:
                    out += x.replace('got', 'acquired')
                else:
                    out += x
            elif "grabbed" in x:
                grabbed_count += 1
                if grabbed_count % 2 == 0:
                    out += x.replace('grabbed', 'seized')
                else:
                    out += x
            elif "left" in x:
                left_count += 1
                if left_count % 2 == 0:
                    out += x.replace('left', 'relinquished')
                else:
                    out += x
            elif "picked up" in x:
                picked_up_count += 1
                if picked_up_count % 2 == 0:
                    out += x.replace('picked up', 'gathered')
                else:
                    out += x
            elif "put down" in x:
                put_down_count += 1
                if put_down_count % 2 == 0:
                    out += x.replace('put down', 'set down')
                else:
                    out += x
            elif "took" in x:
                took_count += 1
                if took_count % 2 == 0:
                    out += x.replace('took', 'snatched')
                else:
                    out += x
            elif "went back" in x:
                went_back_count += 1
                if went_back_count % 2 == 0:
                    out += x.replace('went_back', 'returned')
                else:
                    out += x
            elif "went to" in x:
                went_to_count += 1
                if went_to_count % 2 == 0:
                    out += x.replace('went to', 'entered')
                else:
                    out += x
            else:
                out += x

    with open(file_path2, "w") as f2:
        f2.write(out)


if __name__ == "__main__":
    main()
