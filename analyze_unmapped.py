import json
import difflib

# 加载数据
with open('name_to_id_mapping.json', 'r', encoding='utf-8-sig') as f:
    name_map = json.load(f)

with open('extra_tags.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

with open('arknights_operators.json', 'r', encoding='utf-8-sig') as f:
    operators = json.load(f)

# 查找未映射的角色ID
not_mapped = [id for id, info in data.items() if '未知职业' in info['职业']]

# 创建ID到名称的反向映射
name_to_id_reverse = {v: k for k, v in name_map.items()}

# 提取所有干员名称
operator_names = list(operators.keys())

# 创建文本文件
output_file = 'unmapped_analysis.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    # 写入标题和统计信息
    header = f'未成功映射的角色分析报告\n{"="*40}\n\n总计未映射角色数: {len(not_mapped)}\n\n详细分析:\n{"="*40}\n'
    print(header)
    f.write(header)
    
    # 分析未映射的角色
    for id in not_mapped:
        name = name_to_id_reverse.get(id, "未知名称")
        entry = f'\nID: {id}, 名称: {name}\n'
        print(entry, end='')
        f.write(entry)
        
        # 使用字符串相似度查找可能的匹配
        if name != "未知名称":
            matches = difflib.get_close_matches(name, operator_names, n=3, cutoff=0.4)
            if matches:
                match_header = f'  可能的匹配:\n'
                print(match_header, end='')
                f.write(match_header)
                for match in matches:
                    match_entry = f'    - {match} | 职业: {operators[match]["职业"]} | 星级: {operators[match]["星级"]}\n'
                    print(match_entry, end='')
                    f.write(match_entry)
            else:
                no_match = '  没有找到可能的匹配\n'
                print(no_match, end='')
                f.write(no_match)

print(f"\n分析报告已保存到 {output_file}") 