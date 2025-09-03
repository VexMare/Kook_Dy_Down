# 抖音音乐机器人 (Kook_Dy_Down)

一个基于 Kook 平台的智能抖音视频下载机器人，能够自动检测抖音链接并下载视频、图片到 Kook 平台。

## ✨ 功能特性

### 🎯 核心功能
- **自动检测抖音链接**：智能识别消息中的抖音视频链接
- **视频下载上传**：自动下载抖音视频并上传到 Kook
- **图片下载上传**：下载视频封面图片并上传到 Kook
- **多链接支持**：支持多个备用图片链接，提高下载成功率
- **智能去重**：避免重复处理相同的链接

### 🛡️ 安全特性
- **随机请求头**：使用随机 User-Agent 和请求头，避免被检测
- **随机文件名**：下载后使用随机文件名，避免冲突
- **链接验证**：严格的链接格式验证和视频ID提取
- **错误处理**：完善的异常处理和错误日志

### 🎨 用户体验
- **实时反馈**：处理过程中提供状态更新
- **详细信息**：显示视频标题、作者、时长、播放量等
- **卡片展示**：使用 Kook 卡片消息展示视频信息
- **多格式支持**：支持各种抖音链接格式

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Kook 机器人 Token
- 抖音解析 API

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Kook_Dy_Down
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp test.env .env
# 编辑 .env 文件，填入你的配置
```

4. **启动机器人**
```bash
python3 run.py
```

## ☁️ 推荐部署平台

### DigitalOcean 云服务器部署

[![DigitalOcean Referral Badge](https://camo.githubusercontent.com/3ec52d20f03b93ab09dc4bad6d9cba51d3932934667dbc5ca37f778797171e8e/68747470733a2f2f7765622d706c6174666f726d732e73666f322e63646e2e6469676974616c6f6365616e7370616365732e636f6d2f5757572f4261646765253230322e737667)](https://m.do.co/c/8dcaa780cb2f)

**推荐使用 DigitalOcean 部署您的抖音音乐机器人，享受简单、可靠的云服务器体验！**

#### 部署步骤：

1. **注册 DigitalOcean 账户**
   - 访问: [https://m.do.co/c/8dcaa780cb2f](https://m.do.co/c/8dcaa780cb2f)
   - 注册新账户，获得 **$200 免费额度**
   - 支持信用卡或 PayPal 支付

2. **创建 Droplet**
   - 选择 **Ubuntu 20.04 LTS** 操作系统
   - 推荐配置: **1GB RAM, 1 CPU, 25GB SSD**
   - 选择合适的数据中心位置（推荐新加坡或香港）

3. **配置服务器**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装 Python 3.8+
   sudo apt install python3 python3-pip git -y
   
   # 克隆项目
   git clone https://github.com/VexMare/Kook_Dy_Down
   cd Kook_Dy_Down
   
   # 安装依赖
   pip3 install -r requirements.txt
   
   # 配置环境变量
   cp test.env .env
   nano .env  # 编辑配置文件
   
   # 启动机器人
   python3 run.py
   ```

4. **设置开机自启**
   ```bash
   # 安装 PM2 进程管理器
   sudo npm install -g pm2
   
   # 启动机器人
   pm2 start run.py --name douyin-bot --interpreter python3
   
   # 设置开机自启
   pm2 startup
   pm2 save
   ```

#### DigitalOcean 优势：
- 🆓 **$200 免费额度** - 足够运行数月
- 💰 **价格透明** - 无隐藏费用，按小时计费
- 🚀 **快速部署** - 60秒内创建服务器
- 🌍 **全球节点** - 多个数据中心选择
- 🛡️ **安全可靠** - 99.99% 正常运行时间
- 📞 **24/7 支持** - 专业技术支持

> 💡 **提示**：使用上面的推荐链接注册，您将获得 $200 免费额度，足够免费运行您的机器人项目！

## ⚙️ 配置说明

### 环境变量配置 (.env)
```env
# Kook 机器人配置
BOT_TOKEN=your_kook_bot_token

# 抖音解析 API 配置
DOUYIN_API_URL=https://your-api-domain.com/api/douyin

# 其他配置
LOG_LEVEL=INFO
```

### 项目结构
```
Kook_Dy_Down/
├── src/                    # 源代码目录
│   ├── bot/               # 机器人核心逻辑
│   │   └── main.py        # 主程序
│   ├── api/               # API 接口
│   │   ├── douyin_api.py  # 抖音 API
│   │   └── kook_api.py    # Kook API
│   ├── models/            # 数据模型
│   │   ├── video.py       # 视频信息模型
│   │   └── player.py      # 播放器状态模型
│   └── utils/             # 工具类
│       ├── link_parser.py # 链接解析器
│       └── logger.py      # 日志工具
├── config/                # 配置文件
│   └── settings.py        # 设置管理
├── logs/                  # 日志文件
├── requirements.txt       # 依赖列表
├── run.py                # 启动文件
└── README.md             # 项目说明
```

## 📖 使用说明

### 基本使用
1. 将机器人添加到 Kook 服务器
2. 在任意频道发送包含抖音链接的消息
3. 机器人会自动检测并处理链接
4. 等待下载完成后查看结果

### 支持的链接格式
- `https://v.douyin.com/xxxxx/`
- `https://www.douyin.com/video/xxxxx`
- `https://m.douyin.com/video/xxxxx`
- Markdown 格式：`[链接文本](https://v.douyin.com/xxxxx/)`

### 示例消息
```
这是一个很棒的抖音视频！
https://v.douyin.com/_tNRIScpmpY/
```

## 🎬 功能演示

### 实际处理效果
机器人成功处理的示例文件：

#### 视频文件
- [示例视频1](https://img.kookapp.cn/attachments/2025-09/03/68b7837dc8509.mp4) - 成功下载并上传的抖音视频
- [示例视频2](https://img.kookapp.cn/attachments/2025-09/03/68b7836c1103a.mp4) - 另一个处理成功的视频

#### 封面图片
- [示例封面](https://img.kookapp.cn/attachments/2025-09/03/LVlqYUDIBK0c8096.jpg) - 自动下载的视频封面图片

> 💡 **说明**：这些链接展示了机器人实际工作的效果，包括视频下载、图片提取和Kook平台上传功能。

## 🔧 技术特性

### 智能链接检测
- 支持多种抖音链接格式
- 自动处理 Markdown 格式链接
- 智能去重，避免重复处理
- 支持连字符和下划线字符

### 下载优化
- 使用随机请求头避免反爬检测
- 支持多个备用图片链接
- 自动重试机制
- 文件大小限制检查

### 错误处理
- 完善的异常捕获
- 详细的错误日志
- 用户友好的错误提示
- 自动清理临时文件

## 📊 日志系统

项目使用 loguru 进行日志管理，日志文件位于 `logs/` 目录：

- `bot.log` - 机器人运行日志
- `error.log` - 错误日志
- `command.log` - 命令执行日志

## 🛠️ 开发说明

### 添加新功能
1. 在相应的模块中添加功能代码
2. 更新数据模型（如需要）
3. 添加相应的测试
4. 更新文档

### 调试模式
```bash
# 设置日志级别为 DEBUG
export LOG_LEVEL=DEBUG
python3 run.py
```

### 测试
```bash
# 运行测试（如果有测试文件）
python3 -m pytest tests/
```

## 📝 更新日志

### v1.0.0 (2025-09-03)
- ✨ 初始版本发布
- 🎯 支持抖音视频链接检测和下载
- 🖼️ 支持封面图片下载
- 🛡️ 实现随机请求头和文件名
- 🔧 支持多个备用图片链接
- 📊 完善的日志系统

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## ⚠️ 免责声明

本项目仅供学习和研究使用，请遵守相关法律法规和平台服务条款。使用本项目产生的任何问题，作者不承担任何责任。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 其他联系方式

---

**注意**：使用前请确保已获得必要的 API 访问权限，并遵守相关平台的使用条款。
