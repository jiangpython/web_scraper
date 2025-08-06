# 数英网数据统计与智能对话系统

## 🎯 系统概述

这是一个集成了数据统计和AI智能对话的Web界面系统，基于您提供的设计图开发。系统包含：

- **左侧统计区域**: 显示品牌总数和项目总数
- **右侧对话区域**: 集成Gemini AI的智能问答功能
- **实时数据更新**: 自动从Excel文件读取最新数据

## 📊 数据来源

系统从 `data/` 文件夹中的所有Excel文件中读取数据：

- 每个Excel文件必须包含名为"所有项目合并"的sheet
- 品牌总数通过"brand"字段去重统计
- 项目总数通过"link"字段去重统计
- 数据文件：`web_data.json`

## 🚀 快速启动

### 方式一：一键启动（推荐）

#### Windows用户
1. **双击运行** `启动系统.bat` 或 `启动系统.ps1`
2. 系统会自动检查环境、依赖和配置
3. 自动启动Web服务器并打开浏览器

#### 配置管理
1. **双击运行** `配置管理器.bat` 或 `配置管理器.ps1`
2. 在图形界面中设置您的Gemini API密钥
3. 点击"启动系统"按钮

### 方式二：命令行启动

#### 1. 环境准备

确保已安装必要的Python包：

```bash
pip install flask flask-cors pandas openpyxl google-generativeai jieba
```

#### 2. 配置文件设置

编辑 `config.env` 文件，设置您的Gemini API密钥：

```env
GEMINI_API_KEY=your_actual_api_key_here
```

#### 3. 启动系统

```bash
python start_dashboard.py
```

系统会自动：
- 检查依赖和环境
- 分析data文件夹中的Excel文件
- 生成统计数据
- 启动Web服务器
- 自动打开浏览器

## 🌐 访问界面

启动后访问：`http://localhost:5000`

## 📋 功能特性

### 数据统计
- ✅ 实时显示品牌总数和项目总数
- ✅ 自动从Excel文件读取数据
- ✅ 支持手动刷新数据
- ✅ 显示最后更新时间和文件数量

### 智能对话
- ✅ 基于Gemini AI的自然语言问答
- ✅ 支持项目查询和统计分析
- ✅ 品牌营销策略分析
- ✅ 项目对比和趋势洞察
- ✅ 实时对话界面

### 界面设计
- ✅ 响应式设计，支持移动端
- ✅ 现代化UI，符合设计图要求
- ✅ 流畅的动画效果
- ✅ 直观的用户交互

## 💬 对话示例

您可以向AI助手询问以下类型的问题：

### 数据查询
- "有多少个品牌？"
- "统计一下项目数量"
- "最近有哪些新项目？"

### 品牌分析
- "分析可口可乐的营销策略"
- "宝马和奔驰的广告有什么不同？"
- "哪些品牌最活跃？"

### 趋势洞察
- "今年的营销趋势是什么？"
- "汽车行业有什么新创意？"
- "对比不同行业的营销特点"

## 🔧 技术架构

### 前端
- HTML5 + CSS3 + JavaScript
- 响应式设计
- 实时数据更新
- 现代化UI组件

### 后端
- Flask Web服务器
- RESTful API设计
- 数据分析和处理
- Gemini AI集成

### 数据处理
- Pandas数据分析
- Excel文件读取
- 数据去重和统计
- JSON格式输出

## 📁 文件结构

```
网页爬虫/
├── simple_dashboard.html    # 主界面文件
├── web_server.py           # Web服务器
├── start_dashboard.py      # 启动脚本
├── data_analyzer.py        # 数据分析器
├── project_assistant.py    # AI助手
├── web_data.json          # 统计数据
└── data/                  # Excel数据文件夹
    └── *.xlsx             # Excel文件
```

## ⚙️ 配置说明

### 配置文件
系统使用 `config.env` 文件进行配置，包含以下设置：

#### Gemini API配置
- `GEMINI_API_KEY`: Gemini API密钥（必需）

#### 服务器配置
- `SERVER_HOST`: 服务器地址（默认: 0.0.0.0）
- `SERVER_PORT`: 端口号（默认: 5000）
- `DEBUG_MODE`: 调试模式（默认: false）

#### 数据配置
- `DATA_FOLDER`: 数据文件夹（默认: data）
- `OUTPUT_FOLDER`: 输出文件夹（默认: output）
- `WEB_DATA_FILE`: Web数据文件（默认: web_data.json）

#### 浏览器配置
- `AUTO_OPEN_BROWSER`: 自动打开浏览器（默认: true）
- `BROWSER_URL`: 浏览器地址（默认: http://localhost:5000）

### 配置管理
- **图形界面**: 运行 `配置管理器.bat` 进行可视化配置
- **手动编辑**: 直接编辑 `config.env` 文件
- **重置配置**: 删除 `config.env` 文件，系统会重新创建默认配置

## 🛠️ 故障排除

### 常见问题

#### 1. 依赖包缺失
```bash
pip install flask flask-cors pandas openpyxl google-generativeai jieba
```

#### 2. Gemini API密钥未设置
```bash
set GEMINI_API_KEY=your_api_key_here
```

#### 3. 数据文件不存在
确保 `data/` 文件夹中有Excel文件，且包含"所有项目合并"sheet

#### 4. 端口被占用
修改 `web_server.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5001)  # 改为5001或其他端口
```

### 调试模式

如需调试，可以修改 `web_server.py`：
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

## 📈 性能优化

### 数据更新
- 自动每3分钟刷新数据
- 支持手动刷新
- 增量更新，避免重复处理

### 内存管理
- 连接池复用
- 自动清理临时文件
- 优化大数据集处理

### 用户体验
- 加载动画
- 错误提示
- 响应式设计

## 🔄 更新日志

### v1.0.0 (2025-08-06)
- ✅ 初始版本发布
- ✅ 基础统计功能
- ✅ AI对话集成
- ✅ 响应式界面设计

## 📞 技术支持

如遇到问题，请检查：

1. **环境检查**: `python start_dashboard.py`
2. **日志文件**: 查看控制台输出
3. **API状态**: 访问 `http://localhost:5000/api/status`
4. **数据文件**: 确认Excel文件格式正确

## 🎨 设计说明

界面设计参考了您提供的设计图：

- **三层嵌套结构**: 对应Web、项目数/口语数、GEMINI/ME/对话
- **品牌总数**: 显示在左侧统计区域
- **项目总数**: 显示在左侧统计区域  
- **对话功能**: 集成在右侧聊天区域
- **现代化UI**: 渐变背景、毛玻璃效果、动画交互

---

**版本**: 1.0.0  
**更新时间**: 2025-08-06  
**兼容性**: Python 3.7+, Chrome 90+ 