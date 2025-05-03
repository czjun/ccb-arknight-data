import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
from urllib.parse import urljoin
import traceback
import sys
import argparse

# 设置请求头，模拟浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 全局变量：是否使用离线模式
OFFLINE_MODE = True  # 修改为False以爬取最新数据


def get_bangumi_characters():
    """爬取Bangumi上的明日方舟角色数据"""
    # 检查是否有缓存，如果有且使用离线模式则直接读取
    cache_file = 'bangumi_characters.json'
    if OFFLINE_MODE and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取缓存文件失败: {e}")
    
    try:
        url = "https://bangumi.tv/subject/225878/characters"
        response = requests.get(url, headers=headers)
        # 确保使用正确的编码
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        characters = []

        # 查找所有角色信息
        character_divs = soup.select("div.light_odd, div.light_even")

        for div in character_divs:
            name_tag = div.select_one("h2 a")
            if name_tag:
                name = name_tag.text.strip()
                # 获取角色URL并提取ID
                char_url = name_tag.get('href', '')
                char_id = None
                if char_url:
                    # 从URL中提取角色ID
                    id_match = re.search(r'/character/(\d+)', char_url)
                    if id_match:
                        char_id = id_match.group(1)
                
                # 有些角色有两个名字，用/分隔
                if "/" in name:
                    name_parts = name.split("/", 1)
                    name = name_parts[0].strip()
                    name_cn = name_parts[1].strip()
                else:
                    name_cn = name

                # 从角色的详细信息中提取角色类型(主角/配角/客串)
                role_type = "配角"  # 默认为配角
                role_info = div.select_one("span.tip")
                if role_info:
                    role_text = role_info.text.strip()
                    if "主角" in role_text:
                        role_type = "主角"
                    elif "客串" in role_text:
                        role_type = "客串"

                characters.append({
                    "id": char_id,
                    "name": name,
                    "name_cn": name_cn,
                    "role_type": role_type
                })
        
        # 保存到缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(characters, f, ensure_ascii=False, indent=2)
        
        return characters
    except Exception as e:
        print(f"爬取Bangumi角色数据失败: {e}")
        # 如果爬取失败且缓存存在，尝试使用缓存
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e2:
                print(f"读取缓存文件失败: {e2}")
                return []
        return []


def get_arknights_operators():
    """爬取明日方舟Wiki的干员数据"""
    # 使用全局定义的headers变量
    global headers
    
    # 检查是否有缓存，如果有且使用离线模式则直接读取
    cache_file = 'arknights_operators.json'
    if OFFLINE_MODE and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                operators = json.load(f)
                if operators:
                    # 清理干员名称格式
                    cleaned_operators = {}
                    for key, value in operators.items():
                        # 移除"文件:"前缀和".jpg"后缀
                        if key.startswith("文件:") and key.endswith(".jpg"):
                            clean_name = key.replace("文件:", "").replace("hd.jpg", "").replace(".jpg", "")
                            cleaned_operators[clean_name] = value
                        else:
                            cleaned_operators[key] = value
                    
                    print(f"从缓存中加载了 {len(cleaned_operators)} 个干员数据")
                    return cleaned_operators
        except Exception as e:
            print(f"读取缓存文件失败: {e}")
    
    try:
        # 这里改用离线文件测试，如果有的话
        if os.path.exists('wiki_page.html'):
            print("使用本地wiki_page.html文件")
            with open('wiki_page.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
        else:
            url = "https://wiki.biligame.com/arknights/%E5%B9%B2%E5%91%98%E6%95%B0%E6%8D%AE%E8%A1%A8"
            print(f"正在请求页面: {url}")
            response = requests.get(url, headers=headers)
            html_content = response.text
            # 保存一份页面内容，便于调试
            with open('wiki_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        operators = {}

        # 查找干员数据表格
        tables = soup.select("table.wikitable")
        if not tables:
            print("未找到干员数据表格")
            tables = soup.select("table")
            if not tables:
                print("未找到任何表格")
                return {}
            print(f"找到 {len(tables)} 个普通表格")
        else:
            print(f"找到 {len(tables)} 个wikitable表格")

        # 找到最大的表格，通常是干员数据表
        main_table = max(tables, key=lambda t: len(t.select("tr")))
        print(f"主表格包含 {len(main_table.select('tr'))} 行数据")
            
        # 解析表格数据
        rows = main_table.select("tr")
        if len(rows) <= 1:
            print("表格行数太少，可能不是正确的干员数据表")
            return {}
            
        # 获取表头
        header_row = rows[0]
        headers_cells = header_row.select("th")
        headers_text = [cell.get_text(strip=True) for cell in headers_cells]
        print(f"表头: {headers_text}")
            
        # 定位关键列索引
        name_idx = -1
        star_idx = -1
        class_idx = -1
        faction_idx = -1
        tags_idx = -1
        infected_idx = -1
            
        for i, header in enumerate(headers_text):
            if "干员" in header or "名称" in header:
                name_idx = i
            elif "星级" in header or "稀有度" in header:
                star_idx = i
            elif "职业" in header or "职业分支" in header:
                class_idx = i
            elif "阵营" in header or "势力" in header or "国家" in header:
                faction_idx = i
            elif "标签" in header or "公招" in header:
                tags_idx = i
            elif "感染" in header:
                infected_idx = i
        
        print(f"列索引 - 名称:{name_idx}, 星级:{star_idx}, 职业:{class_idx}, 阵营:{faction_idx}, 标签:{tags_idx}, 感染:{infected_idx}")
        
        if name_idx == -1:
            print("未找到干员名称列，尝试使用第一列")
            name_idx = 0
        
        # 解析每行数据
        for row in rows[1:]:  # 跳过表头
            cells = row.select("td")
            if len(cells) <= name_idx:
                print(f"行格式不正确，跳过: {len(cells)} 个单元格")
                continue
                
            try:
                # 提取干员名称
                name_cell = cells[name_idx]
                name = ""
                
                # 尝试从a标签获取名称
                name_link = name_cell.select_one("a")
                if name_link:
                    name = name_link.get_text(strip=True)
                    if not name:
                        # 如果a标签内没有文本，尝试获取title或alt属性
                        name = name_link.get('title', '') or name_link.get('alt', '')
                        
                # 如果仍未获取到名称，尝试直接获取单元格文本
                if not name:
                    name = name_cell.get_text(strip=True)
                    
                # 如果名称包含文件前缀，尝试获取干员名称
                if name.startswith("文件:") and ".jpg" in name:
                    # 从链接文本尝试提取干员名称
                    links = name_cell.select("a")
                    for link in links:
                        if link.get_text(strip=True) and not link.get_text(strip=True).startswith("文件:"):
                            name = link.get_text(strip=True)
                            break
                            
                # 如果仍未获取到合适的名称，跳过
                if not name or name.startswith("文件:"):
                    # 最后尝试检查单元格中的所有文本
                    all_text = name_cell.get_text(strip=True)
                    if "]" in all_text:
                        name = all_text.split("]")[-1].strip()
                    
                if not name or name.startswith("文件:"):
                    print(f"无法提取干员名称，跳过")
                    continue
                    
                # 提取星级
                star_text = "未知星级"
                if star_idx != -1 and star_idx < len(cells):
                    star_cell = cells[star_idx]
                    star_value = star_cell.get_text(strip=True)
                    if star_value.isdigit():
                        star_text = f"{star_value}星"
                        
                # 提取职业
                profession_text = "未知职业"
                if class_idx != -1 and class_idx < len(cells):
                    class_cell = cells[class_idx]
                    class_text = class_cell.get_text(strip=True)
                    if "-" in class_text:
                        profession_text = class_text.split("-")[0].strip()
                    else:
                        profession_text = class_text
                        
                # 提取阵营
                faction_text = "未知阵营"
                if faction_idx != -1 and faction_idx < len(cells):
                    faction_cell = cells[faction_idx]
                    faction_text = faction_cell.get_text(strip=True)
                    
                # 提取标签
                tags_text = "未知标签"
                if tags_idx != -1 and tags_idx < len(cells):
                    tags_cell = cells[tags_idx]
                    raw_tags = tags_cell.get_text(strip=True).replace(" ", "")
                    
                    # 添加分隔符的处理逻辑
                    # 识别常见的标签组合并添加分隔符
                    tag_patterns = [
                        "远程位", "近战位", "治疗", "支援", "输出", "群攻", 
                        "减速", "生存", "防护", "削弱", "位移", "控场",
                        "爆发", "召唤", "快速复活", "费用回复", "新手",
                        "支援机械","元素","高空"
                    ]
                    
                    # 对原始标签文本进行分割处理
                    processed_tags = raw_tags
                    for pattern in tag_patterns:
                        if pattern in processed_tags:
                            # 替换标签为带分隔符的形式，但避免替换已经有分隔符的部分
                            processed_tags = processed_tags.replace(pattern, f"{pattern}/", 1)
                    
                    # 移除末尾可能多余的分隔符
                    tags_text = processed_tags.rstrip("/")
                
                # 提取感染状态
                infected_text = "未知"
                if infected_idx != -1 and infected_idx < len(cells):
                    infected_cell = cells[infected_idx]
                    infected_value = infected_cell.get_text(strip=True)
                    if "是" in infected_value:
                        infected_text = "是"
                    elif "否" in infected_value:
                        infected_text = "否"
                
                # 获取干员基础名称，用于合并不同职业形态的同一角色
                base_name = name
                if "（" in name and "）" in name:
                    base_name = name.split("（")[0].strip()
                
                # 干员数据以名称为键
                operators[name] = {
                    "星级": star_text,
                    "职业": profession_text,
                    "标签": tags_text,
                    "阵营": faction_text,
                    "是否感染": infected_text,
                    "基础名称": base_name  # 添加基础名称字段，用于后续合并
                }
                
                print(f"成功提取干员: {name}")
                
            except Exception as e:
                print(f"解析行时出错: {e}")
                continue
                
        print(f"总共提取了 {len(operators)} 个干员")
        
        # 如果提取的干员数很少，可能表明解析逻辑不正确
        if len(operators) < 10:
            print("警告: 提取的干员数量很少，可能解析逻辑不正确")
            
        # 保存到缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(operators, f, ensure_ascii=False, indent=2)
            
        return operators
    except Exception as e:
        print(f"爬取明日方舟Wiki干员数据失败: {traceback.format_exc()}")
        # 如果爬取失败且缓存存在，尝试使用缓存
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    operators = json.load(f)
                    print(f"使用缓存的干员数据，共 {len(operators)} 个")
                    
                    # 清理干员名称格式
                    cleaned_operators = {}
                    for key, value in operators.items():
                        # 移除"文件:"前缀和".jpg"后缀
                        if key.startswith("文件:") and key.endswith(".jpg"):
                            clean_name = key.replace("文件:", "").replace("hd.jpg", "").replace(".jpg", "")
                            cleaned_operators[clean_name] = value
                        else:
                            cleaned_operators[key] = value
                    
                    return cleaned_operators
            except Exception as e2:
                print(f"读取缓存文件失败: {e2}")
                return {}
        return {}


def match_characters_with_operators(bangumi_chars, arknights_ops):
    """匹配Bangumi角色与明日方舟Wiki干员"""
    result = {}
    # 创建一个名称到ID的映射，用于调试
    name_to_id = {}

    # 星级的英文名称映射
    star_mapping = {
        "1星": "1star", "2星": "2star", "3星": "3star", 
        "4星": "4star", "5星": "5star", "6星": "6star",
        "未知星级": "unknown"
    }
    
    # 预处理：创建基础名称到所有变体的映射
    base_to_variants = {}
    for op_name, op_data in arknights_ops.items():
        base_name = op_data.get("基础名称", op_name)
        if base_name not in base_to_variants:
            base_to_variants[base_name] = []
        base_to_variants[base_name].append(op_name)

    # 处理每个Bangumi角色
    for char in bangumi_chars:
        name = char["name_cn"]
        char_id = char["id"]
        if not char_id:
            continue  # 跳过没有ID的角色
            
        name_to_id[name] = char_id
        
        # 初始化角色数据结构
        character_data = {
            "稀有度": {},
            "职业": {},
            "标签": {},
            "阵营": {},
            "是否感染": {}
        }
        
        matched = False
        matched_ops = []
        
        # 检查是否有完全匹配的名称
        exact_match = None
        if name in arknights_ops:
            exact_match = name
        else:
            # 检查是否是某个基础名称
            for base_name, variants in base_to_variants.items():
                if name == base_name:
                    matched_ops.extend(variants)
                    matched = True
                    break
                    
        # 如果有精确匹配，使用它的所有变体
        if exact_match:
            base_name = arknights_ops[exact_match].get("基础名称", exact_match)
            if base_name in base_to_variants:
                matched_ops.extend(base_to_variants[base_name])
                matched = True
        
        # 如果没有匹配到，尝试模糊匹配
        if not matched:
            for op_name, op_data in arknights_ops.items():
                # 检查名称是否包含或被包含
                if name in op_name or op_name in name:
                    base_name = op_data.get("基础名称", op_name)
                    if base_name in base_to_variants:
                        # 添加所有变体
                        for variant in base_to_variants[base_name]:
                            if variant not in matched_ops:
                                matched_ops.append(variant)
                    else:
                        matched_ops.append(op_name)
                    matched = True
            
        # 处理匹配到的干员数据
        if matched_ops:
            # 合并所有匹配到的干员数据
            for op_name in matched_ops:
                op_data = arknights_ops[op_name]
                
                # 处理星级
                star_value = op_data["星级"]
                star_image = f"<img src='/assets/tag/arknights/Star_Rating/{star_mapping.get(star_value, 'unknown')}.png' alt='{star_value}' />"
                character_data["稀有度"][star_value] = star_image
                
                # 处理职业 - 添加图片和文本
                profession = op_data["职业"]
                profession_image = f"<img src='/assets/tag/arknights/Occupation/{profession}.png' alt='{profession}' /> {profession}"
                character_data["职业"][profession] = profession_image
                
                # 处理标签
                if "/" in op_data["标签"]:
                    tag_list = op_data["标签"].split("/")
                    for tag in tag_list:
                        if tag.strip() and tag.strip() not in character_data["标签"]:
                            character_data["标签"][tag.strip()] = tag.strip()
                else:
                    # 如果没有分隔符，就使用整个标签
                    tag = op_data["标签"]
                    if tag not in character_data["标签"]:
                        character_data["标签"][tag] = tag
                
                # 处理阵营
                if "," in op_data["阵营"] or "，" in op_data["阵营"]:
                    # 替换中文逗号为英文逗号，然后分割
                    faction_text = op_data["阵营"].replace("，", ",")
                    faction_list = faction_text.split(",")
                    for faction in faction_list:
                        if faction.strip() and faction.strip() not in character_data["阵营"]:
                            character_data["阵营"][faction.strip()] = faction.strip()
                else:
                    # 如果没有分隔符，就使用整个阵营
                    faction = op_data["阵营"]
                    if faction not in character_data["阵营"]:
                        character_data["阵营"][faction] = faction
                
                # 处理感染状态
                infected_status = op_data["是否感染"]
                character_data["是否感染"][infected_status] = infected_status
            
            result[char_id] = character_data
        else:
            # 如果没有匹配到，添加一个空记录
            result[char_id] = {
                "稀有度": {
                    "未知星级": "<img src='/assets/tag/arknights/Star_Rating/unknown.png' alt='未知星级' />"
                },
                "职业": {
                    "未知职业": "<img src='/assets/tag/arknights/Occupation/未知职业.png' alt='未知职业' /> 未知职业"
                },
                "标签": {
                    "未知标签": "未知标签"
                },
                "阵营": {
                    "未知阵营": "未知阵营"
                },
                "是否感染": {
                    "未知": "未知"
                }
            }
    
    # 保存名称到ID的映射，方便调试
    with open('name_to_id_mapping.json', 'w', encoding='utf-8-sig') as f:
        json.dump(name_to_id, f, ensure_ascii=False, indent=2)
    print("名称到ID的映射已保存到 name_to_id_mapping.json")

    return result


def save_to_json(data, filename="extra_tags.json"):
    """将数据保存为JSON文件，保留手动修改的数据"""
    # 检查是否存在旧的数据文件
    if os.path.exists(filename):
        try:
            # 加载旧的数据文件
            with open(filename, 'r', encoding='utf-8-sig') as f:
                old_data = json.load(f)
                
            # 合并数据：只替换包含"未知职业"的条目，保留其他手动修改
            for char_id, char_info in old_data.items():
                if char_id in data:
                    # 检查是否为未映射的条目（含"未知职业"）
                    if "未知职业" not in char_info["职业"]:
                        # 如果不是未映射条目，保留手动修改
                        data[char_id] = char_info
                        print(f"保留手动修改的数据: ID {char_id}")
                else:
                    # 如果新数据中不存在此ID，也要保留
                    data[char_id] = char_info
                    
            print(f"已合并手动修改的数据")
        except Exception as e:
            print(f"读取旧数据文件失败，无法保留手动修改: {e}")
    
    # 保存合并后的数据
    with open(filename, 'w', encoding='utf-8-sig') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {filename}")


def main():
    # 使用命令行参数控制离线模式
    global OFFLINE_MODE
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='明日方舟角色数据爬虫')
    parser.add_argument('--offline', action='store_true', help='启用离线模式，使用本地缓存数据')
    parser.add_argument('--refresh-all', action='store_true', help='刷新所有数据，不保留手动修改')
    args = parser.parse_args()
    
    OFFLINE_MODE = args.offline
    
    if OFFLINE_MODE:
        print("启用离线模式，将使用本地缓存数据")
    else:
        print("禁用离线模式，将从网络获取最新数据")
        
    if args.refresh_all:
        print("警告: 将刷新所有数据，不保留手动修改!")

    print("开始获取Bangumi角色数据...")
    bangumi_characters = get_bangumi_characters()
    print(f"成功获取 {len(bangumi_characters)} 个角色")

    print("开始获取明日方舟Wiki干员数据...")
    arknights_operators = get_arknights_operators()
    print(f"成功获取 {len(arknights_operators)} 个干员")

    # 打印部分干员名称，用于检查编码是否正确
    print("干员名称示例:")
    count = 0
    for name in list(arknights_operators.keys())[:5]:
        print(f"  - {name}")
        count += 1
        if count >= 5:
            break

    print("开始匹配角色和干员数据...")
    matched_data = match_characters_with_operators(bangumi_characters, arknights_operators)
    
    # 打印部分匹配结果，用于检查编码是否正确
    print("匹配结果示例:")
    count = 0
    for char_id in list(matched_data.keys())[:5]:
        print(f"  - ID: {char_id}")
        count += 1
        if count >= 5:
            break
    
    print(f"成功匹配 {len(matched_data)} 个角色")

    # 根据参数决定是否保留手动修改
    if args.refresh_all:
        # 不保留手动修改，直接保存
        with open("extra_tags.json", 'w', encoding='utf-8-sig') as f:
            json.dump(matched_data, f, ensure_ascii=False, indent=2)
        print("所有数据已刷新，未保留手动修改")
    else:
        # 保留手动修改
        save_to_json(matched_data)


if __name__ == "__main__":
    main()