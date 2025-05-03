# 明日方舟角色数据爬虫

这是一个Python爬虫项目，用于从Bangumi网站和明日方舟Wiki获取角色数据，并将这些数据合并处理为适用于ccb标签系统的JSON格式。

是的就是AI生成

## 功能特点

- 从Bangumi网站爬取明日方舟角色信息
- 从明日方舟Wiki爬取干员详细数据（星级、职业、阵营、标签等）
- 自动匹配Bangumi角色与明日方舟干员数据
- 支持离线模式，减少重复请求
- 生成符合ccb标签系统要求的JSON格式数据
- 对数据进行结构化处理，便于筛选和搜索

## 生成的数据格式

程序生成的`extra_tags.json`文件包含以下结构：

```json
{
  "角色ID": {
    "稀有度": {
      "6星": "<img src='/assets/tag/arknights/Star_Rating/6star.png' alt='6星' />"
    },
    "特种": {
      "特种": "<img src='/assets/tag/arknights/Occupation/特种.png' alt='特种' />"
    },
    "标签": {
      "远程位": "远程位",
      "输出": "输出"
    },
    "阵营": {
      "喀兰贸易": "喀兰贸易",
      "谢拉格": "谢拉格"
    },
    "是否感染": {
      "是": "是"
    }
  }
}
```

## 使用方法

### 环境要求

- Python 3.6+
- 依赖包：requests, beautifulsoup4

### 安装依赖

```bash
pip install requests beautifulsoup4
```

### 运行

#### 在线模式（获取最新数据）

```bash
python main.py --offline=False
```

#### 离线模式（使用缓存数据）

```bash
python main.py --offline
```

### 输出文件

- `bangumi_characters.json` - Bangumi角色数据缓存
- `arknights_operators.json` - 明日方舟Wiki干员数据缓存
- `name_to_id_mapping.json` - 角色名称到ID的映射
- `extra_tags.json` - 最终生成的标签数据（主要输出）

## 数据处理说明

1. **角色匹配逻辑**：
   - 尝试精确匹配角色名称
   - 如未找到，尝试模糊匹配（名称包含关系）
   - 如仍未找到，添加默认"未知"数据

2. **数据格式处理**：
   - 标签以分隔形式拆分为多个独立键值对
   - 阵营信息按逗号分隔为多个独立键值对
   - 职业和星级生成带图片的HTML标签

## 注意事项

- 频繁请求可能被网站限制，建议使用离线模式
- 数据结构可能随着网站变化而需要调整
- 初次运行需要联网获取数据

## 数据来源

- [Bangumi明日方舟条目](https://bangumi.tv/subject/225878/characters)
- [明日方舟Wiki干员数据表](https://wiki.biligame.com/arknights/干员数据表) 
