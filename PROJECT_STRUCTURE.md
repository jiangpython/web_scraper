# 项目文件结构说明 (清理后)

## 核心系统文件

### 🚀 主要脚本
- `run_enhanced_scraper_v3.py` - **主程序** - 一键式数据整合和爬取
- `batch_manager.py` - **批次管理器** - 支持断点续传和状态跟踪
- `smart_ai_assistant.py` - **智能AI助手** - 新的AI查询翻译器系统
- `excel_integrator.py` - **Excel整合器** - 自动整合data文件夹中的Excel数据
- `data_converter.py` - **数据转换器** - 生成AI兼容的JSON格式
- `prompt_manager.py` - **提示词管理器** - 管理AI提示词模板

### 🔧 核心工具组件
- `gemini_client.py` - **AI客户端** - Gemini API封装
- `driver_pool.py` - **WebDriver连接池** - 浏览器驱动管理
- `digitaling_parser_enhanced.py` - **增强解析器** - 网页内容提取
- `utils/data_cleaner.py` - **数据清理工具** - 字段标准化和清理

### 📊 数据文件
- `master_projects.csv` - **主数据源** - 7527个项目的基础信息
- `scraped_projects.csv` - **进度跟踪表** - 爬取状态和断点续传支持
- `data/` - **Excel数据源** - 原始Excel文件存储

### ⚙️ 配置文件
- `config_optimized.py` - **系统配置** - 爬虫和AI系统配置
- `config.env` - **环境配置** - API密钥等敏感配置
- `requirements.txt` - **依赖管理** - Python包依赖列表
- `prompts/simple_prompts.json` - **AI提示词模板** - 可独立调整

### 🌐 Web界面 (可选)
- `web_server.py` - **Web服务器** - 提供Web界面访问 (需要更新)
- `web_dashboard.html` - **Web前端** - 用户界面 (需要更新)

### 📁 输出目录
- `output/` - **系统输出**
  - `batch_status.json` - 批次状态跟踪
  - `details/` - 批次详细数据存储
  - `projects_index.json` - AI系统兼容的项目索引
  - `global_search_index.json` - 全局搜索索引

### 🛠️ 系统工具
- `chromedriver.exe` - **浏览器驱动** - Selenium需要
- `venv/` - **Python虚拟环境**
- `CLAUDE.md` - **项目文档** - 完整的任务记录和使用说明

## 使用流程

### 1. 数据准备
```bash
# 将新的Excel文件放入data/文件夹
# 系统会自动检测并整合
```

### 2. 启动爬虫
```bash
cd D:\项目\网页爬虫
source venv/Scripts/activate
python run_enhanced_scraper_v3.py
```

### 3. AI查询
```bash
# 使用智能AI助手
python smart_ai_assistant.py

# 或启动Web界面 (需要先更新)
python web_server.py
```

## 系统优势

- ✅ **一键式操作**: 自动数据整合、爬取、转换
- ✅ **断点续传**: 支持大规模长时间爬取任务
- ✅ **智能AI查询**: 自然语言转查询指令
- ✅ **独立配置**: 提示词和配置可独立调整
- ✅ **成本优化**: 最小化API调用成本
- ✅ **易于维护**: 清晰的模块化结构

## 已清理的文件

已删除以下类型的冗余文件：
- 旧版爬虫脚本 (v1, v2版本)
- 旧版AI系统文件
- 测试文件和报告
- 重复的配置文件
- 旧版文档和启动脚本
- 临时数据文件

总计清理了约40个冗余文件，系统结构更加简洁清晰。