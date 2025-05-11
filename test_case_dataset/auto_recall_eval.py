import requests
import pandas as pd
import re

# 读取标准.md文件，提取问题和黄金答案
def parse_markdown_table(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    tables = []
    current_table = []
    in_table = False
    for line in lines:
        if line.strip().startswith('|'):
            in_table = True
            current_table.append(line.strip())
        elif in_table and not line.strip():
            if current_table:
                tables.append(current_table)
                current_table = []
            in_table = False
    if current_table:
        tables.append(current_table)
    # 只处理前两个表（电动汽车安全要求、动力蓄电池安全要求）
    all_rows = []
    for table in tables:
        header = [h.strip() for h in table[0].split('|')[1:-1]]
        for row in table[2:]:
            cols = [c.strip() for c in row.split('|')[1:-1]]
            if len(cols) == len(header):
                all_rows.append(dict(zip(header, cols)))
    return all_rows

def recall_test(questions, api_url='http://localhost:8001/search', top_ks=[1,3,5]):
    results = []
    for q in questions:
        query = q['问题']
        gold = q['黄金答案']
        row = {'问题': query, '黄金答案': gold}
        try:
            resp = requests.get(api_url, params={'query': query, 'k': max(top_ks)})
            resp.raise_for_status()
            data = resp.json()['results']
            for k in top_ks:
                hit = any(gold[:10] in item['content'] for item in data[:k])
                row[f'Top{k}_hit'] = hit
        except Exception as e:
            for k in top_ks:
                row[f'Top{k}_hit'] = False
            row['error'] = str(e)
        results.append(row)
    return pd.DataFrame(results)

if __name__ == '__main__':
    md_path = 'test_case_dataset/标准.md'
    questions = parse_markdown_table(md_path)
    # 只保留有黄金答案的
    questions = [q for q in questions if q.get('黄金答案')]
    df = recall_test(questions)
    print(df[['问题','Top1_hit','Top3_hit','Top5_hit']])
    print('\nTop1召回率:', df['Top1_hit'].mean())
    print('Top3召回率:', df['Top3_hit'].mean())
    print('Top5召回率:', df['Top5_hit'].mean())
    df.to_csv('test_case_dataset/auto_recall_eval_result.csv', index=False)
    print('\n详细结果已保存到 test_case_dataset/auto_recall_eval_result.csv') 