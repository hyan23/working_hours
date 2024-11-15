#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sqlite3


def parse_time_str(time_str):
    if time_str.endswith('min'):
        return int(time_str[:-3])
    parts = time_str.split('.')
    if len(parts) == 1:
        return int(parts[0]) * 60
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    raise ValueError('Invalid time string: ' + time_str)

def read_data(data_file):
    data = {}
    last_line = None
    current_day = None
    with open(data_file, 'r', encoding='utf-8') as f:
        match_day = re.compile(r'^(\d{4}\.\d{1,2}\.\d{1,2}) (Mon\.|Tues\.|Weds\.|Thur\.|Fri\.|Sat\.|Sun\.)$')
        for line in f:
            
            line = line.strip()
            if not line:
                continue
            
            m = match_day.match(line)
            if m:
                print(m.group(1), m.group(2))
                current_day = line
                last_line = None
                continue
            
            if not current_day:
                print('Error: no day', line)
                continue
            
            comment = None
            parts = line.split('#')
            if len(parts) > 1:
                comment = '#'.join(parts[1:]).strip()
            
            parts = parts[0].strip().split()
            if len(parts) != 2:
                print('Error: invalid syntax', current_day, line)
                continue
            
            cat, time_str = parts
            
            if not comment:
                if last_line and cat == last_line[0]:
                    comment = last_line[1]
                else:
                    print('Error: no comment', current_day, line)
                    continue
            
            try:
                time = parse_time_str(time_str)
            except Exception:
                print('Error: invalid time string', current_day, line)
                continue
            last_line = (cat, comment)
            data.setdefault(current_day, []).append((cat, time, comment))
    return data
    
def read_synonyms(synonyms_file):
    synonyms = {}
    with open(synonyms_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            words = line.split()
            for word in words:
                synonyms[word] = words[0]
    return synonyms
    
def insert_into_sqlite(data, synonyms) -> sqlite3.Connection:
    # insert into sqlite
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS data (day DATE, cat TEXT, time INTEGER, comment TEXT)')
    c.execute('DELETE FROM data')
    for day, items in data.items():
        day = day.split()[0]
        day = day.replace('.', '-')
        for cat, time, comment in items:
            if cat in synonyms:
                cat = synonyms[cat]
            if comment in synonyms:
                comment = synonyms[comment]
            c.execute('INSERT INTO data VALUES (?, ?, ?, ?)', (day, cat, time, comment))
    conn.commit()
    return conn
    
def select_all_from_sqlite(conn: sqlite3.Connection):
    # select from sqlite
    c = conn.cursor()
    c.execute('SELECT * FROM data')
    for row in c.fetchall():
        print(row)

def group_by_day_cat(conn: sqlite3.Connection):
    # group by day, cat
    c = conn.cursor()
    c.execute('SELECT day, cat, SUM(time) FROM data GROUP BY day, cat')
    for row in c.fetchall():
        print(row)
        
def group_by_week_cat(conn: sqlite3.Connection):
    # group by week, cat
    c = conn.cursor()
    c.execute('SELECT strftime(\'%W\', day) as week, cat, SUM(time) FROM data GROUP BY week, cat')
    for row in c.fetchall():
        print(row)
        
def group_by_day_work(conn: sqlite3.Connection):
    # group by day, comment where cat = '工作'
    c = conn.cursor()
    c.execute('SELECT day, comment,CAST((SUM(time)/60.0*100) AS INTEGER)/100.0 FROM data WHERE cat = \'工作\' GROUP BY day, comment')
    for row in c.fetchall():
        print(row)

def main():
    data_file = 'data.txt'
    synonyms_file = 'syn.txt'

    data = read_data(data_file)
    synonyms = {}
    if os.path.exists(synonyms_file):
        synonyms = read_synonyms(synonyms_file)
        
    conn = insert_into_sqlite(data, synonyms)
    select_all_from_sqlite(conn)


if __name__ == '__main__':
    main()
