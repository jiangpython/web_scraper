# 数英网项目爬虫系统使用指南

## 🚀 脚本总览

现有3个主要爬虫脚本，各有不同用途：

### 1. `scraper_urls_batch.py` - URLs批量基础爬虫
**用途**: 从urls.txt文件批量获取基础项目信息
```bash
python scraper_urls_batch.py
```

**功能特点**：
- ✅ 基于urls.txt文件的批量爬取
- ✅ 提取基础信息(标题、品牌、代理商、发布日期)
- ✅ 输出Excel表格到data/文件夹
- ✅ 支持断点续传和增量爬取
- ✅ 内存优化，适合大量URL处理

**适用场景**：初步数据收集、从URLs生成Excel数据源

---

### 2. `scraper_interactive.py` - 交互式详细爬虫
**用途**: 基于Excel数据进行详细内容爬取(交互式界面)
```bash
python scraper_interactive.py
```

**功能特点**：
- ✅ 交互式用户界面(6个操作选项)
- ✅ 断点续传，支持任意位置中断恢复
- ✅ 智能数据整合(Excel + 网页详细内容)
- ✅ 实时进度跟踪和统计
- ✅ 单线程稳定爬取，适合长期运行
- ✅ 自动生成AI兼容的索引文件

**适用场景**：长期稳定爬取、需要交互控制、初次使用

---

### 3. `scraper_parallel.py` - 高并发详细爬虫
**用途**: 基于Excel数据进行高性能详细内容爬取(命令行)
```bash
# 自动配置
python scraper_parallel.py

# 指定配置
python scraper_parallel.py --preset balanced
python scraper_parallel.py --max-workers 8
python scraper_parallel.py --dry-run  # 测试配置
```

**功能特点**：
- ✅ 命令行参数控制，适合自动化
- ✅ 高并发多线程，性能提升5-10倍
- ✅ 智能配置预设(conservative/balanced/aggressive/extreme/auto)
- ✅ 断点续传支持
- ✅ 专注性能，简洁高效

**适用场景**：高速爬取、脚本自动化、服务器批量处理

## 📊 数据流程图

```
URLs收集阶段:
urls.txt → scraper_urls_batch.py → data/*.xlsx

详细爬取阶段:
data/*.xlsx → (合并) → master_projects.csv → 详细爬虫 → output/批次文件

AI系统集成:
output/批次文件 → 数据转换器 → projects_index.json + global_search_index.json
```

## 🔄 推荐工作流程

### 场景1: 首次使用，有urls.txt文件
1. **基础爬取**: `python scraper_urls_batch.py` (获取基础信息)
2. **详细爬取**: `python scraper_interactive.py` (交互式详细爬取)

### 场景2: 已有Excel数据，需要详细内容
1. **稳定爬取**: `python scraper_interactive.py` (推荐初次使用)
2. **高速爬取**: `python scraper_parallel.py` (适合大规模数据)

### 场景3: 服务器自动化
```bash
# 高性能自动化脚本
python scraper_parallel.py --preset aggressive
```

## ⚙️ 配置说明

### 并发配置预设 (scraper_parallel.py)
- `conservative`: 2线程，适合网络较慢环境
- `balanced`: 4线程，推荐日常使用
- `aggressive`: 8线程，适合高性能环境
- `extreme`: 12线程，适合服务器环境
- `auto`: 自动检测最优配置

## 📁 输出文件说明

### data/文件夹 (基础数据)
- `*.xlsx`: 基础项目信息表格
- `master_projects.csv`: 合并后的统一数据源

### output/文件夹 (详细数据)
- `batch_*.json`: 详细项目内容分批次存储
- `combined_projects.json`: 合并的详细项目数据
- `projects_index.json`: AI系统项目索引
- `global_search_index.json`: 全局搜索索引

## 🛠️ 常见问题

**Q: 如何选择爬虫脚本？**
A: 
- 有urls.txt → 用`scraper_urls_batch.py`
- 需要交互控制 → 用`scraper_interactive.py` 
- 追求高性能 → 用`scraper_parallel.py`

**Q: 爬取中断了怎么办？**
A: 所有脚本都支持断点续传，重新运行即可从断点继续

**Q: 如何提升爬取速度？**
A: 使用`scraper_parallel.py`并选择aggressive或extreme配置

**Q: 数据存储在哪里？**
A: 基础数据在data/文件夹，详细数据在output/文件夹

## 📞 技术支持

如遇问题，请检查：
1. 网络连接是否稳定
2. ChromeDriver版本是否匹配
3. 虚拟环境是否正确激活
4. 依赖包是否完整安装

---
*最后更新: 2025-08-11*