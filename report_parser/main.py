import report_parser
import os
def main():
    src_path  = 'gem5_simout/stats.txt'
    dest_path = 'files/Report/report.json'

    success = report_parser.parseReport(src_path, dest_path)

    if success:
        pass
        # print('parse file successfully')
    else:
        print('failed to parse gem5 output file')

if __name__ == '__main__':
    main()
