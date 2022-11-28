import argparse


def clean_csv(in_file, out_file):
    lines = []
    with open(in_file) as report:
        for idx, line in enumerate(report):
            if idx < 9:
                continue

            if line.startswith('#'):
                line = line[1:]

            lines.append(','.join([_.strip() for _ in line.strip().split(',')]))

    with open(out_file, 'w+') as clean:
        clean.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        dest="input"
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        dest="output"
    )

    args = parser.parse_args()

    clean_csv(args.input, args.output)


if __name__ == '__main__':
    main()
