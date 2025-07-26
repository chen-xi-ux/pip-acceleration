# Pypi 源管理工具

一个用于测试、管理和切换 Python Pypi 镜像源的图形化工具，帮助用户快速找到最快的 Pypi 源并一键应用配置。

## 功能特性



*   🚀 自动测试多个主流 Pypi 镜像站的连接延迟

*   🔍 按延迟自动排序，直观展示各镜像站速度

*   ⚡ 支持单源模式和多源轮询模式

*   🖱️ 一键应用最优配置，无需手动编辑配置文件

*   🔄 随时查看当前配置和恢复默认设置

*   📱 自适应界面设计，支持窗口大小调整

*   🎨 清晰的视觉反馈，延迟状态用颜色标识（绿色 / 橙色 / 红色）

## 支持的镜像站

包含国内主流 Pypi 镜像源和官方源：



*   阿里云

*   腾讯云

*   网易

*   清华大学（TUNA）

*   中国科学技术大学（USTC）

*   北京大学

*   火山引擎

*   浙江大学

*   Python 官方

## 安装与使用

### 前提条件



*   Python 3.6 及以上版本

*   需要安装的依赖库：


    *   PyQt5：用于图形界面

    *   requests：用于测试镜像站连接

### 安装步骤



1.  克隆或下载本项目代码

2.  安装依赖：



```
Pypi install PyQt5 requests
```



3.  运行程序：



```
python main.py
```

### 使用方法



1.  启动程序后，点击 "测试所有镜像站延迟（自动排序）" 按钮

2.  等待测试完成，程序会自动按延迟从小到大排序

3.  选择单源模式或多源模式：

*   单源模式：直接选择一个最快的镜像站

*   多源模式：可选择多个镜像站（推荐 3-5 个）

4.  点击 "应用设置" 按钮完成配置

## 界面展示

### 主界面

<img width="1920" height="1040" alt="image" src="https://github.com/user-attachments/assets/a39fe994-961b-4818-86f8-cc0a8ac7598f" />

### 测速结果

<img width="1134" height="976" alt="image" src="https://github.com/user-attachments/assets/194130f1-64e0-4634-ba45-622cb20f287a" />


### 配置应用

<img width="475" height="187" alt="image" src="https://github.com/user-attachments/assets/86cd54e1-bbda-48e0-8329-75eaf3d9af18" />

<img width="585" height="297" alt="image" src="https://github.com/user-attachments/assets/f98d6026-5ca3-4978-971d-1f90a0cd59f3" />


## 许可证

本项目采用 GPL-3.0 许可证 - 详见 LICENSE 文件

## 致谢

感谢所有提供公共 Pypi 镜像服务的机构和组织

## 反馈与贡献

如有任何问题或建议，欢迎提交 Issue 或 Pull Request
