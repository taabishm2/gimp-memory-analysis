import csv
import argparse


def data_object_filter(row):
    return row['Data Object'] not in {'[heap]', 'anon'}


ALL_FILTERS = [data_object_filter]


def filter_csv(in_file, out_file):
    lines = []
    with open(in_file) as report:
        reader = csv.DictReader(report)
        for row in reader:
            if any(f(row) for f in ALL_FILTERS):
                continue
            else:
                lines.append(row)

    with open(out_file, 'w+') as clean:
        writer = csv.DictWriter(clean, fieldnames=lines[0].keys())
        writer.writeheader()
        writer.writerows(lines)


def main():
    parser = argparse.ArgumentParser(prog="clean_spaces")

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

    filter_csv(args.input, args.output)


if __name__ == '__main__':
    main()
