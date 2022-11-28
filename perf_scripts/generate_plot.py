import numpy as np
import pandas as pd
from math import ceil
import seaborn as sns
import matplotlib.pyplot as plt

NUM_ADDRESS_BINS = 150


def generate_plot(input_file, output_file):
    df = pd.read_csv(input_file, usecols=['Time', 'Data Physical Address'])

    df['Data Physical Address'] = df['Data Physical Address'].apply(lambda x: int(x[4:], 16))

    # Bin time by second
    pd.to_numeric(df['Time'])
    min_time = df['Time'].min()
    df['Time'] = df['Time'].apply(lambda x: round(x - min_time))

    # Bin Addresses
    df['Data Physical Address'] = pd.qcut(df['Data Physical Address'], NUM_ADDRESS_BINS)

    df.sort_values('Time')
    df = df.groupby(['Time', 'Data Physical Address']).size().reset_index(name='count')
    df = df.pivot_table(index=df['Data Physical Address'], values='count', columns='Time', aggfunc='first')

    sns.set(font_scale=2)
    fig, axs = plt.subplots(figsize=(100, 100))
    sns.heatmap(df, cmap='RdYlGn_r', linewidths=0.50, linecolor='Black', annot=True, ax=axs, cbar=True)

    plt.savefig(output_file, dpi=150)

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

    generate_plot(args.input, args.output)


if __name__ == '__main__':
    main()
